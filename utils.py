import json
import csv
import os
import logging
import portalocker
import asyncio
from functools import wraps

def load_config():
    with open('config.json', 'r') as f:
        return json.load(f)

def save_config(config):
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=4)

def setup_logging(log_file):
    logging.basicConfig(
        filename=log_file,
        filemode='a',
        format='%(asctime)s,%(levelname)s,%(message)s',
        level=logging.INFO
    )

def ensure_log_csv(config):
    if not os.path.exists(config["DATA_LOG_CSV"]):
        with portalocker.Lock(config["DATA_LOG_CSV"], 'w', timeout=10) as f:
            writer = csv.writer(f)
            writer.writerow(['Row', 'ActivityId', 'Type', 'Name', 'Website', 'Status', 'Reason'])

def log_skip(config, row_num, activity_id, reason):
    with portalocker.Lock(config["DATA_LOG_CSV"], 'a', timeout=10) as f:
        writer = csv.writer(f)
        writer.writerow([row_num, activity_id, '', '', '', 'Skipped', reason])
    logging.info(f"{row_num},{activity_id},Skipped,{reason}")

def log_downloaded(config, row_num, activity_id, file_name):
    with portalocker.Lock(config["DATA_LOG_CSV"], 'a', timeout=10) as f:
        writer = csv.writer(f)
        writer.writerow([row_num, activity_id, '', '', '', 'Downloaded', file_name])
    logging.info(f"{row_num},{activity_id},Downloaded,{file_name}")

def log_failure(config, row_num, activity_id, reason):
    with portalocker.Lock(config["DATA_LOG_CSV"], 'a', timeout=10) as f:
        writer = csv.writer(f)
        writer.writerow([row_num, activity_id, '', '', '', 'Failure', reason])
    logging.info(f"{row_num},{activity_id},Failure,{reason}")

def get_next_row(config):
    with portalocker.Lock(config["DATA_LOG_CSV"], 'r', encoding='utf-8', timeout=10) as f:
        reader = csv.reader(f)
        rows = list(reader)
    total_rows = len(rows) - 1
    next_row = config.get("NEXT_ROW", 1)
    return total_rows, next_row

def update_next_row(config, next_row):
    config["NEXT_ROW"] = next_row
    save_config(config)

def retry_with_backoff(max_retries, backoff):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exc = e
                    if attempt < max_retries - 1:
                        await asyncio.sleep(backoff ** attempt)
            raise last_exc
        return wrapper
    return decorator
