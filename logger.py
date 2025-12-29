import logging
import os
import sys
from logging.handlers import RotatingFileHandler


class ColorFormatter(logging.Formatter):
    COLORS = {
        logging.DEBUG: "\033[36m",     # Cyan
        logging.INFO: "\033[32m",      # Green
        logging.WARNING: "\033[33m",   # Yellow
        logging.ERROR: "\033[31m",     # Red
        logging.CRITICAL: "\033[41m",  # Red background
    }
    RESET = "\033[0m"

    def format(self, record):
        log_msg = super().format(record)
        if sys.stdout.isatty():
            color = self.COLORS.get(record.levelno, "")
            return f"{color}{log_msg}{self.RESET}"
        return log_msg


def setup_logger(name: str, log_dir: str, level=logging.DEBUG):
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, f"{name}.log")

    logger = logging.getLogger(name)
    logger.setLevel(level)

    if logger.handlers:
        return logger

    base_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    # ---- File handler (NO color)
    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setFormatter(logging.Formatter(base_format, date_format))
    file_handler.setLevel(level)

    # ---- Console handler (WITH color)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(ColorFormatter(base_format, date_format))
    console_handler.setLevel(logging.INFO)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.propagate = False

    return logger
