import logging
from logging import Formatter
from logging.handlers import RotatingFileHandler


def configure_logger(module_name):
    """
    Настройка логирования
    """
    logger = logging.getLogger(module_name)
    logger.setLevel(logging.DEBUG)
    formatter = Formatter("%(asctime)s - [%(levelname)s] - %(name)s "
                          "(%(filename)s).%(funcName)s(%(lineno)d): "
                          "%(message)s")
    # configure file log
    filename = 'logs/wipo.log'
    fh = RotatingFileHandler(filename, maxBytes=30000000, backupCount=50)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    # configure console log
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger
