"""Setting logging once for each pipeline cycles"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(log_dir: Path) -> None:
    root = logging.getLogger()
    if root.handlers:  # already configured: don't add duplicate handlers
        return

    log_dir.mkdir(parents=True, exist_ok=True)
    root.setLevel(logging.DEBUG)
    formatter = logging.Formatter(FORMAT, DATE_FORMAT)

    console = logging.StreamHandler()
    console.setLevel(logging.INFO)  # terminal: INFO and up
    console.setFormatter(formatter)

    file_handler = RotatingFileHandler(
        log_dir / "pipeline.log", maxBytes=1_000_000, backupCount=3, encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)  # file: everything
    file_handler.setFormatter(formatter)

    root.addHandler(console)
    root.addHandler(file_handler)
