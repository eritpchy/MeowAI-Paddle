import json
import os
import time
import io
import numpy as np
import tempfile
import mimetypes
import subprocess
import magic
from PIL import Image, ImageOps
from typing import Optional

from src import log
from src.api import api
from src.detect import detect, detect_dict
from src.executor import executor
from src.locale import locale
from src.log.logger import logger

from sqlitedict import SqliteDict


score_threshold = 0.7
offset = 0
limit = 100
max_limit = 500
total_done_list = []
_ = locale.lc
_executor: Optional[executor.DetectExecutor] = None

ocr = None
done_list_db = SqliteDict("docker/data/done_list.sqlite", encode=json.dumps, decode=json.loads, autocommit=True)

class DetectFile:

    def __init__(self, id, filename, type, clasTagDicts, model, cost):
        self.id = id
        self.filename = filename
        self.type = type
        self.clasTagDicts = clasTagDicts
        self.model = model
        self.cost = cost

def start_indexing():
    global offset
    global ocr
    _limit = limit
    while True:
        photo_ids = list()
        has_more = True
        offset = 0
        while has_more:
            photo_list = api.get_photos(offset, _limit)
            photo_ids.extend(list(str(item['id']) for item in photo_list))
            has_more = photo_list is not None and len(photo_list) > 0
            if not has_more:
                break
            detect_list, done_list = detect_photo_list(photo_list)
            offset += len(photo_list)
            if len(done_list) == 0:
                # If all files are skipped, increase limit
                _limit = max_limit
            else:
                _limit = limit
            text_info = _("Detect %d images, handle %d photos, total handle %d photos")
            logger.info(f'{text_info}', len(detect_list), len(done_list), len(done_list_db))
        # if picture deleted from server
        photo_ids_deleted = list()
        for key in done_list_db:
            if key not in photo_ids:
                photo_ids_deleted.append(key)
        for key in photo_ids_deleted:
            logger.info(f'Delete id: {key} from database')
            del done_list_db[key]
        photo_ids = None
        photo_ids_deleted = None
        # check has more
        total = api.count_total_photos()
        done_list_db_len = len(done_list_db)
        if total > done_list_db_len:
            has_more = True
            text_wake = _("Wake...")
            logger.info(f"{text_wake} total: {total} done_list_db_len: {done_list_db_len}")
            # reset offset
            offset = 0
        else:
            if ocr is not None:
                logger.info("Exit, free memory")
                exit(0)
            while True:
                text_sleep = _("Sleep...")
                logger.info(text_sleep)
                # sleep for a while
                time.sleep(10)
                if api.count_total_photos() != total:
                    break


def ocr_photo(id, p, image_data):
    global ocr
    if ocr is None:
        from paddleocr import PaddleOCR
        ocr = PaddleOCR(use_angle_cls=True, lang="ch", debug=False, show_log=False)
    # return
    try:
        result = ocr.ocr(image_data, cls=True)
        lines = ""
        for idx in range(len(result)):
            res = result[idx]
            for line in res:
                text, score = line[1]
                if score > score_threshold:
                    lines += text
                    lines += " "
                # print(f'id: {id} ocr_line: {line}')
        ocr.text_recognizer.predictor.try_shrink_memory()
        logger.info(f"ocr: {lines}")
        exist_tags = p['additional']['tag']
        if lines != "":
            resolution = p['additional']['resolution']
            # fixed 图片信息不生成, 导致无法插入描述
            if (resolution['width'] == 0 or resolution['height'] == 0):
                tag_id = bind_tag(id, "临时", exist_tags)
                api.remove_tags(id, [tag_id])
            api.set_description(id, lines)
    except Exception as e:
        logger.exception("Error: %s", e)


def detect_photo(id, p):
    image = None
    image_is_temp = False
    try:
        start_time = time.time()
        thumbnail = p['additional']['thumbnail']
        cache_key = thumbnail['cache_key']
        filename = p['filename']
        image_content = api.get_photo_by_id(id, cache_key, api.headers)
        image, image_is_temp = process_image_content(filename, image_content)
        clasTags = detect.detect(image)
        clasTagDicts = []
        if len(clasTags) > 0:
            clasTagDicts = [clasTag.__dict__ for clasTag in clasTags]
        ocr_photo(id, p, image)
        end_time = time.time()
        elapsed_time = round(end_time - start_time, 2)
        detect_file = DetectFile(id, filename=filename, type=p['type'], 
            clasTagDicts=clasTagDicts, model=detect.model_name, cost=elapsed_time)
        exist_tags = p['additional']['tag']
        for clasTag in clasTags:
            if clasTag is not None and clasTag.score >= score_threshold and not clasTag.exclude:
                bind_tag(id, tag_name=clasTag.label, exist_tags=exist_tags)
        return detect_file
    finally:
        if image_is_temp:
            delete_file_path(image)

def delete_file_path(path):
    if path is None:
        return False
    if not os.path.exists(path):
        return False
    os.remove(path)
    return True

def detect_photo_list(list):
    detect_list = []
    start_time = time.time()
    for i, p in enumerate(list):
        id = p['id']
        if has_done(id):
            continue
        _executor.add_task(executor.DetectTask(i, id, len(list), p, detect_photo))
    _executor.run()
    results: Optional[map] = _executor.wait_completion()
    done_list = []
    for key, value in results.items():
        if value.clasTagDicts is not None:
            detect_list.append(value)
        done_list.append(value)
    end_time = time.time()
    logger.debug(f'detect_photo_list cost = {round(end_time - start_time, 2)}s')
    add_to_done_list(done_list)
    return detect_list, done_list


# return image_content/temp_image_path, is_temp
def process_image_content(filename, image_content):
    # logger.info(f"正在识别 %s", image_path)
    tempfile_path = None
    if type(image_content) == str:
        return image_content, False
    mime = magic.from_buffer(image_content, mime=True)
    if mime.startswith('video/'):
        videofile = os.path.join(tempfile.gettempdir(), filename)
        try:
            with io.open(videofile, "wb") as f:
                f.write(image_content)
            tempfile_path = os.path.join(tempfile.gettempdir(), f"{filename}.png")
            subprocess.run(['ffmpeg', '-i', videofile, '-y', '-vf', 'select=eq(n\\,0)', tempfile_path])
            if os.path.exists(tempfile_path):
                return tempfile_path, True
        finally:
            delete_file_path(videofile)
    image_data = None
    try:
        image = Image.open(io.BytesIO(image_content))
        if (filename.lower().endswith(".gif")):
            image = image.convert("RGB")
        image_data = np.array(image)
    except Exception as e:
        logger.exception(e)

    if (image_data is None or image_data.ndim < 3):
        tempfile_path = os.path.join(tempfile.gettempdir(), filename)
        with io.open(tempfile_path, "wb") as f:
            f.write(image_content)
        return tempfile_path, True
    else:
        return image_data, False
    


def has_done(id):
    id_str = str(id)
    if id_str not in done_list_db:
        return False
    d = done_list_db[id_str]
    if d is not None:
        clasTagDicts = d['clasTagDicts']
        model = d['model']
        if model == detect.model_name and (
                clasTagDicts is not None or (clasTagDicts is None and model == detect.model_name)):
            return True
    return False


def add_to_done_list(list):
    if len(list) == 0:
        return
    for detect_file in list:
        done_list_db[str(detect_file.id)] = {
            "filename": detect_file.filename,
            "type": detect_file.type,
            "clasTagDicts": detect_file.clasTagDicts,
            "model": detect_file.model,
            "cost": detect_file.cost,
        }


def bind_tag(id, tag_name, exist_tags):
    tag_id = api.get_tag_id_by_name(tag_name)

    if tag_id is None:
        api.create_tag(tag_name)
        tag_id = api.get_tag_id_by_name(tag_name)

    if exist_tags and len(exist_tags) > 0:
        for e_tag in exist_tags:
            e_tag_name = e_tag['name']
            if e_tag_name == tag_name:
                return

    api.bind_tag(id, tag_id, tag_name)
    return tag_id


def start(executor):
    global _executor
    _executor = executor
    api.init_var()
    start_indexing()


if __name__ == '__main__':
    log.init_log()
    api.init_var()
    start_indexing()
