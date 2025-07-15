# image_scraper/logger.py

import logging

def setup_logging(level):
    lvl = getattr(logging, level.upper(), logging.ERROR)
    logging.basicConfig(level=lvl, format='%(asctime)s %(levelname)s:%(message)s')
