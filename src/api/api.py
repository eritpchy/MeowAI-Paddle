import gettext
import json
import os
from typing import Dict

import requests
import functools
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.api import error_codes
from src.locale import locale
from src.log.logger import logger

base_url = 'http://127.0.0.1:5000'
cookie = None
token = None
headers = None
tags = []

# 识别文件夹
mode = 'person'
# api 前缀
api_pre = None

username = None
pwd = None
# token错误码
token_error_code = ['119', '120', '150']
_ = locale.lc

s = requests.Session()
# 配置重试策略，包括超时情况
retry_strategy = Retry(
    total=3,  # 总共重试3次
    backoff_factor=1,  # 重试间隔时间因子
    status_forcelist=[429, 500, 502, 503, 504],  # 遇到这些状态码时重试
    allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "PUT", "DELETE", "PATCH"],  # 允许重试的请求方法
    raise_on_status=False,  # 不因状态码错误而中断重试
    raise_on_redirect=False,  # 不因重定向而中断重试
)

# 将重试策略应用到会话的适配器
adapter = HTTPAdapter(max_retries=retry_strategy)
s.mount("http://", adapter)
s.mount("https://", adapter)

# 设置超时时间为300秒
s.request = functools.partial(s.request, timeout=(3, 300))

def get_token():
    global cookie
    global token
    global headers
    url = f'{base_url}/webapi/auth.cgi?api=SYNO.API.Auth&version=3&method=login&account={username}&passwd={pwd}&format=cookie&enable_syno_token=yes'
    #url = f'{base_url}/webapi/auth.cgi?api=SYNO.API.Auth&session=Foto&version=7&method=login&account={username}&passwd={pwd}&format=cookie&enable_syno_token=yes'
    response = s.get(url)
    try:
        data = json.loads(response.content)
        if data['success']:
            cookie = response.headers.get('Set-Cookie')
            token = data['data']['synotoken']
            headers = {
                'Cookie': cookie,
                'X-SYNO-TOKEN': token,
            }
        else:
            error_msg = get_error_message(data)
            logger.error(error_msg)
    except Exception as e:
        logger.error(e)


def get_tags():
    try:
        url = f'{base_url}/webapi/entry.cgi/{api_pre}.Browse.GeneralTag'
        data = {
            'api': f'{api_pre}.Browse.GeneralTag',
            'method': 'list',
            'version': '1',
            'limit': '500',
            'offset': '0'
        }
        response = s.post(url, data, headers=headers)
        data = json.loads(response.content)
        if data['success']:
            list = data['data']['list']
            return list
        else:
            if data['error']['code'] in token_error_code:
                get_token()
            logger.error(get_error_message(data))
        return []
    except Exception as e:
        logger.exception(e)
        return []


def get_photos(offset, limit):
    try:
        logger.info(f'current offset = {offset} limit = {limit}')
        url = f'{base_url}/webapi/entry.cgi/{api_pre}.Browse.Item'
        data = {
            "api": f"{api_pre}.Browse.Item",
            "method": "list",
            "version": "1",
            "offset": offset,
            "limit": limit,
            "additional": '["thumbnail","tag", "resolution"]',
            "timeline_group_unit": '"day"',
            #     'start_time':,
            # 'end_time':
        }
        # logger.info(headers)
        response = s.post(url, data=data, headers=headers)
        data = json.loads(response.content)
        if data['success']:
            list = data['data']['list']
            logger.info(f'get_photos: {len(list)}')
            return list
        else:
            if data['error']['code'] in token_error_code:
                get_token()
            logger.error(get_error_message(data))
            return None
    except Exception as e:
        logger.exception(e)
        return None


def download_photo_by_id(id):
    try:
        url = f'{base_url}/webapi/entry.cgi/{api_pre}.Download'
        data = {
            'api': f'{api_pre}.Download',
            'method': 'download',
            'version': '1',
            'item_id': f'[{id}]',
            'force_download': 'true',
        }
        headers['Accept-Encoding'] = 'gzip, deflate'
        response = s.post(url, data, headers=headers)
        if response.status_code == 200:
            return response.content
        else:
            logger.info(response.content)
        return None
    except Exception as e:
        logger.exception(e)
        return None


def get_photo_by_id(id, cache_key, headers):
    try:
        # logger.info(f'{id}  {cache_key}')
        url = f'{base_url}/webapi/entry.cgi?id={id}&cache_key={cache_key}&type=unit&size=xl&api={api_pre}.Thumbnail&method=get&version=2&SynoToken=NXibb.RkEVsCY'
        # logger.info(url)
        headers[
            'Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7'
        headers['Accept-Encoding'] = 'gzip, deflate'
        response = s.get(url, headers=headers)
        if response.status_code == 200:
            return response.content
        else:
            logger.info(response.status_code)
            return download_photo_by_id(id)
        return None
    except Exception as e:
        logger.exception(e)
        return None


def create_tag(tag_name):
    try:
        url = f'{base_url}/webapi/entry.cgi/{api_pre}.Browse.GeneralTag'
        data = {
            'api': f'{api_pre}.Browse.GeneralTag',
            'method': 'create',
            'version': '1',
            'name': tag_name,
        }
        response = s.post(url, data, headers=headers)
        data = json.loads(response.content)
        if data['success']:
            text = _("tag generate success:")
            logger.info(f'{text} {tag_name}')
            tags.append(data['data']['tag'])
        else:
            if data['error']['code'] in token_error_code:
                get_token()
            text = _("tag generate failed")
            logger.info(f'{text}: {tag_name}')
    except Exception as e:
        logger.exception(e)


def bind_tag(id, tag_id, tag_name):
    url = f'{base_url}/webapi/entry.cgi/{api_pre}.Browse.Item'
    data = {
        'api': f'{api_pre}.Browse.Item',
        'method': 'add_tag',
        'version': '1',
        'id': f'[{id}]',
        'tag': f'[{tag_id}]'
    }
    # logger.info(data)
    response = s.post(url, data, headers=headers)
    try:
        data = json.loads(response.content)
        if data['success']:
            text = _("tag bind success:")
            logger.debug(f'{text} id={id} {tag_name}')
            return True
        else:
            if data['error']['code'] in token_error_code:
                get_token()
            text = _("tag bind failed:")
            logger.error(f'{text} id={id} {tag_name}')
            return False
    except Exception as e:
        logger.error(e)
        text = _("tag bind failed:")
        logger.error(f'{text} id={id} {tag_name}')


def get_tag_id_by_name(tag_name):
    for tag in tags:
        if tag['name'] == tag_name:
            return tag['id']
    return None


def get_photo_info_by_id(id):
    try:
        url = f'{base_url}/webapi/entry.cgi/{api_pre}.Browse.Item'
        params = {
            'api': f'{api_pre}.Browse.Item',
            'method': 'get',
            'version': 2,
            'id': f'[{id}]',
            'additional': ["tag"]
        }
        # 发送请求
        response = s.get(url, params=params, headers=headers)
        # 解析响应结果
        result = response.json()
        if result['success']:
            return result['data']['list'][0]
        return None
    except Exception as e:
        logger.exception(e)
        return None




def remove_tags(id, tag_ids):
    url = f'{base_url}/webapi/entry.cgi/{api_pre}.Browse.GeneralTag'
    data = {
        'api': f'{api_pre}.Browse.Item',
        'method': 'remove_tag',
        'version': '1',
        'id': f'[{id}]',
        'tag': f'{tag_ids}'
    }
    response = s.post(url, data, headers=headers)
    try:
        data = response.json()
        if data['success']:
            text = _("tag remove success:")
            logger.debug(f'{text} id={id} {tag_ids}')
            return True
        else:
            if data['error']['code'] in token_error_code:
                get_token()
            text = _("tag remove failed:")
            logger.error(f'{text} id={id} {tag_ids}')
            return False
    except Exception as e:
        text = _("tag remove failed:")
        logger.error(f'{text} id={id} {tag_ids}')
        logger.error(e)
        return False


def count_total_photos():
    url = f'{base_url}/webapi/entry.cgi/{api_pre}.Browse.Timeline'
    data = {
        'api': f'{api_pre}.Browse.Timeline',
        'method': 'get',
        'version': '2',
        'timeline_group_unit': 'day',
    }
    response = s.post(url, data, headers=headers)
    try:
        data = response.json()
        if data['success']:
            section_list = data['data']['section']
            total = 0
            for section in section_list:
                if section['limit']:
                    total += section['limit']
            return total
        else:
            if data['error']['code'] in token_error_code:
                get_token()
            text = _("count_total_photos failed:")
            error_msg = get_error_message(data)
            logger.error(f'{text} %s', error_msg)
            return 0
    except Exception as e:
        text = _("count_total_photos failed:")
        logger.error(f'{text} %s', e)
        return 0


def set_description(id, description):
    try:
        url = f'{base_url}/webapi/entry.cgi/{api_pre}.Browse.Item'
        params = {
            'api': f'{api_pre}.Browse.Item',
            'method': 'set',
            'version': 2,
            'id': f'[{id}]',
            'description': description,
        }
        # 发送请求
        response = s.get(url, params=params, headers=headers)
        # 解析响应结果
        result = response.json()
        # logger.info(f'set_description:{result} params: {params}')
        if result['success']:
            return True
        return False
    except Exception as e:
        logger.exception(e)
        return False


def get_error_code(response: Dict[str, object]) -> int:
    if response.get('success'):
        code = error_codes.CODE_SUCCESS
    else:
        code = response.get('error').get('code')
    return code


def get_error_message(response: Dict[str, object]) -> str:
    code = get_error_code(response)
    if code in error_codes.error_codes.keys():
        message = error_codes.error_codes[code]
    else:
        message = error_codes.auth_error_codes.get(code, response)
    return 'Error {} - {}'.format(code, message)


def init_var():
    global mode
    global api_pre
    global username
    global pwd
    global base_url
    global tags
    username = os.environ['user']
    pwd = os.environ['pwd']
    mode = os.environ.get('mode', 'person')
    ip = os.environ.get('ip', '127.0.0.1:5000')
    if mode == 'person':
        api_pre = 'SYNO.Foto'
    else:
        api_pre = 'SYNO.FotoTeam'
    base_url = f'http://{ip}'
    get_token()
    tags = get_tags()
    logger.info(tags)
