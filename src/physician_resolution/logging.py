import logging
import os
import sys


def setup_logging(level: str | None = None) -> logging.Logger:
    """Configure and return the root logger for the pipeline."""
    level = level or os.getenv("LOG_LEVEL", "INFO")

    logger = logging.getLogger("physician_resolution")
    logger.setLevel(getattr(logging, level.upper()))

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(getattr(logging, level.upper()))

        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a child logger for a specific module."""
    return logging.getLogger(f"physician_resolution.{name}")
