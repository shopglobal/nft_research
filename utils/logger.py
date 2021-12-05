"""Generic function to hold the basic logging."""

import os
import logging
from datetime import datetime


def get_standard_logger(name, log_dir=None):
    """Function to return an instance of type logger."""
    if log_dir is None:
        log_dir = '/Users/teaton/dev/fantasyAM/logs'

    time_stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Create a file handler
    os.makedirs(log_dir, exist_ok=True)
    handler = logging.FileHandler(os.path.join(log_dir, f'{name}_{time_stamp}.log'))
    handler.setLevel(logging.INFO)

    # Create a logging format
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    # add the handlers to the logger
    logger.addHandler(handler)

    return logger
