import gettext
import json
import os
import time
import sys
import io
import tempfile

import numpy as np
sys.path.append("/home/jason/miniconda3/envs/MeowAI/lib/")
from io import BytesIO

from PIL import Image, ImageOps

from src.detect import detect_dict
from src.detect.clas_tag import ClasTag
from src.locale import locale
from src.log.logger import logger


clas = None 
model = None
model_name = 'PPHGNet_small_ssld'
_ = locale.lc


def init_model():
    global model_name
    detect_dict.init_model_var()
    start_time = time.time()
    model_name = os.environ.get('model', model_name)
    text = _("Load model:")
    logger.info(f'{text} {model_name}')
    end_time = time.time()
    elapsed_time = round(end_time - start_time, 2)
    logger.info(f'{text} {elapsed_time} s')


def detect(image_data):
    global clas
    if clas is None:
        from paddleclas import PaddleClas
        clas = PaddleClas(model_name=model_name, debug=False, show_log=False)
    tempFilePath = None
    try:
        clasTags = []
        # logger.info(f"正在识别 %s", image_path)
        results = clas.predict(image_data)
        for r in results:
            r = r[0]
            class_id = r['class_ids'][0]
            class_label = r['label_names'][0]
            class_score = r['scores'][0]
            class_label = detect_dict.get_tag_by_label(class_id, class_label, locale.language)
            exclude = detect_dict.is_label_exclude(class_label)
            clasTags.append(ClasTag(class_id, class_label, class_score, exclude))
        return clasTags
    except Exception as e:
        logger.exception("Error: %s", e)
        return []
    finally:
        clas.predictor.predictor.try_shrink_memory()


def detect_dir():
    global files, f
    base = './data'
    detect_file_list = []
    for home, dirs, files in os.walk(base):
        for filename in files:
            # 判断是否是图片格式
            if filename.endswith(".png") or filename.endswith(".jpg") or filename.endswith(".jpeg"):
                # 文件名列表，包含完整路径
                file = os.path.join(home, filename)
                # is_cat = detect(file)
                # if is_cat:
                #     file_name = os.path.basename(file)
                #     new_file_path = './results/' + file_name
                #     shutil.copy2(file, new_file_path)
                # detect_file = DetectFile(file_name, file_path=file)
                # detect_file_list.append(detect_file)
    json_str = json.dumps([f.__dict__ for f in detect_file_list])
    with open("./results/result.json", "w") as f:
        json.dump(json_str, f)
