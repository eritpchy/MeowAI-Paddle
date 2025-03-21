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
    # So, if you want a custom handler on "test", and you don't want its messages also going to the root handler, the answer is simple: turn off its propagate flag:
    logger.propagate = False

    # 创建一个StreamHandler对象，指定输出到sys.stdout
    stream_handler = logging.StreamHandler(sys.stdout)
    # 设置立即刷新
    stream_handler.setLevel(level)
    # 确保每次写入后立即刷新
    stream_handler.flush = lambda: sys.stdout.flush()

    # 创建一个FileHandler对象，指定输出到log.txt文件
    file_handler = logging.FileHandler('logs.txt')

    # 设置FileHandler对象的日志级别
    file_handler.setLevel(level)

    # 创建一个Formatter对象，指定日志格式
    format = '%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    formatter = logging.Formatter(format, datefmt='%Y-%m-%d %H:%M:%S')

    # 为两个Handler对象设置Formatter对象
    stream_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    if (logger.hasHandlers()):
        logger.handlers.clear()
    logger.addHandler(stream_handler)
    # logger.addHandler(file_handler)
