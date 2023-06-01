import logging
import sys

from src.config import config

logger = logging.getLogger('meow')


def init_log():
    level = logging.INFO
    if config.is_debug:
        level = logging.DEBUG

    # 设置Logger对象的日志级别
    logger.setLevel(level)
