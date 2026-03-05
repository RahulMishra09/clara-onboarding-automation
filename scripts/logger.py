"""
Logging utilities for Clara AI Automation Pipeline.
Provides colored console output and file logging.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
import colorlog

from config import LOG_DIR, LOG_LEVEL


def setup_logger(
    name: str,
    log_file: Optional[str] = None,
    level: Optional[str] = None
) -> logging.Logger:
    """
    Set up a logger with colored console output and optional file logging.

    Args:
        name: Logger name
        log_file: Optional log file name (will be created in LOG_DIR)
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level or LOG_LEVEL))

    # Clear existing handlers
    logger.handlers.clear()

    # Console handler with colors
    console_handler = colorlog.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_formatter = colorlog.ColoredFormatter(
        "%(log_color)s%(levelname)-8s%(reset)s %(blue)s[%(name)s]%(reset)s %(message)s",
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        log_path = LOG_DIR / log_file
        file_handler = logging.FileHandler(log_path, mode='a', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger


def get_processing_logger() -> logging.Logger:
    """Get the main processing logger."""
    return setup_logger(
        "clara.processing",
        log_file="processing.log"
    )


def get_extraction_logger() -> logging.Logger:
    """Get the extraction logger."""
    return setup_logger(
        "clara.extraction",
        log_file="extraction.log"
    )


def get_validation_logger() -> logging.Logger:
    """Get the validation logger."""
    return setup_logger(
        "clara.validation",
        log_file="validation.log"
    )


def log_separator(logger: logging.Logger, char: str = "=", length: int = 80):
    """Log a visual separator line."""
    logger.info(char * length)


def log_section(logger: logging.Logger, title: str):
    """Log a section header."""
    log_separator(logger)
    logger.info(f" {title} ")
    log_separator(logger)


if __name__ == "__main__":
    # Test logging
    logger = get_processing_logger()
    log_section(logger, "Testing Logger")
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
    print(f"\nLog file created at: {LOG_DIR / 'processing.log'}")
