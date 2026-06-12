import logging
import sys
import os

class ColoredFormatter(logging.Formatter):
    """Logging Formatter to add colors only to the levelname"""
    green = "\x1b[32;21m"
    yellow = "\x1b[33;21m"
    red = "\x1b[31;21m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    
    # Format: Levelname (colored) : Message (not colored)
    FORMATS = {
        logging.DEBUG: "%(levelname)s: %(message)s",
        logging.INFO: f"{green}%(levelname)s{reset}: %(message)s",
        logging.WARNING: f"{yellow}%(levelname)s{reset}: %(message)s",
        logging.ERROR: f"{red}%(levelname)s{reset}: %(message)s",
        logging.CRITICAL: f"{bold_red}%(levelname)s{reset}: %(message)s"
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno, "%(levelname)s: %(message)s")
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

def setup_logging(level=logging.INFO, log_file=None):
    """Sets up colored logging for the console and optional file logging."""
    logger = logging.getLogger()
    logger.setLevel(level)
    
    # Remove existing handlers to avoid double logging
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        
    # Console handler (with colors)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(ColoredFormatter())
    logger.addHandler(console_handler)
    
    # File handler (optional, no colors)
    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(file_handler)
    
    return logger
