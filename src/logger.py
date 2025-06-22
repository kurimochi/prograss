from logging import getLogger, StreamHandler, Formatter, INFO

def get_logger(name: str = None):
    name = name or "default"
    logger = getLogger(name)

    if not logger.hasHandlers():
        handler = StreamHandler()
        handler.setLevel(INFO)
        formatter = Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(INFO)
        logger.propagate = False

    return logger