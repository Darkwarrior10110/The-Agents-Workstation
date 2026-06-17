import logging
import os
from datetime import datetime

def setup_logger(name: str):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Create logs directory if not exists
    if not os.path.exists("storage/logs"):
        os.makedirs("storage/logs")
        
    # File handler
    file_handler = logging.FileHandler(f"storage/logs/system.log")
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter('\033[94m%(name)s\033[0m: %(message)s')
    console_handler.setFormatter(console_formatter)
    
    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
    return logger

system_logger = setup_logger("WORKSTATION")
