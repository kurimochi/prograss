import sys
from logging import getLogger, StreamHandler, Formatter, INFO, WARNING


def get_logger(name: str = None):
    name = name or "default"
    logger = getLogger(name)

    if not logger.hasHandlers():
        # INFO以下はstdout
        stdout_handler = StreamHandler(sys.stdout)
        stdout_handler.setLevel(INFO)
        stdout_handler.addFilter(lambda record: record.levelno <= INFO)
        formatter = Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        stdout_handler.setFormatter(formatter)
        logger.addHandler(stdout_handler)

        # WARNING以上はstderr
        stderr_handler = StreamHandler(sys.stderr)
        stderr_handler.setLevel(WARNING)
        stderr_handler.addFilter(lambda record: record.levelno >= WARNING)
        stderr_handler.setFormatter(formatter)
        logger.addHandler(stderr_handler)

        logger.setLevel(INFO)
        logger.propagate = False

    return logger
