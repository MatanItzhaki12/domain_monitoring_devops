import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logger(name: str):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    logger.handlers.clear()

    # Ensure "logs" folder exists in the repo root
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
    os.makedirs(log_dir, exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    log_levels = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL,
    }

    for level_name, level in log_levels.items():
        fh = RotatingFileHandler(
            os.path.join(log_dir, f"{level_name}.log"),
            maxBytes=8_000_000,
            backupCount=0
        )
        fh.setLevel(level)
        fh.setFormatter(formatter)
        fh.addFilter(lambda record, lvl=level: record.levelno == lvl)
        logger.addHandler(fh)

    return logger
