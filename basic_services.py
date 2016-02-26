# basic_services

logger = None

def set_logger(logger1):
    global logger
    logger = logger1

def logger():
    return logger

def log_info(*args):
    if logger is not None:
        logger.log_info(*args)

def log_error(*args):
    if logger is not None:
        logger.log_error(*args)

def log_debug(tag, *args):
    if logger is not None:
        logger.log_debug(tag, *args)
