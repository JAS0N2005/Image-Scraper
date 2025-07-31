"""
Handles file and row operations including safe slno generation and output file moves.
slno starts from 1 for each ActivityId per run.
"""

import os
import csv
import uuid
import portalocker
from urllib.parse import urlparse

class FileHandler:
    def __init__(self, config):
        self.config = config
        self.output_dir = config["OUTPUT_FOLDER"]
        os.makedirs(self.output_dir, exist_ok=True)
        self.slno_file = os.path.join(self.output_dir, "slno_tracker.csv")
        # Internal state for per-run activity slno
        self.activity_slno = {}

    def iter_input_rows(self, config, start_row):
        with portalocker.Lock(config["DATA_LOG_CSV"], 'r', encoding='utf-8', timeout=10) as f:
            reader = csv.DictReader(f)
            for idx, row in enumerate(reader):
                if idx + 1 >= start_row and row.get("Status", "").strip().lower() == "pending":
                    yield row

    def is_valid_url(self, url):
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False

    def get_per_row_slno(self, activity_id):
        # Starts from 1 for each ActivityId per run
        if activity_id not in self.activity_slno:
            self.activity_slno[activity_id] = 1
        slno = self.activity_slno[activity_id]
        self.activity_slno[activity_id] += 1
        return slno

    def get_output_name(self, row, slno, flag_type=None, ext="png"):
        base = f"{row['ActivityId']}_{row['Type']}_{slno}"
        if flag_type:
            base += f"_[{flag_type}]"
        return base + f".{ext}"

    def move_to_output(self, img_file, out_name):
        out_path = os.path.join(self.output_dir, out_name)
        temp_path = out_path + f".{uuid.uuid4().hex}.tmp"
        if hasattr(img_file, 'save'):
            img_file.save(temp_path)
        elif isinstance(img_file, str) and os.path.exists(img_file):
            os.rename(img_file, temp_path)
        os.replace(temp_path, out_path)
        return out_path

# Alias for backward compatibility
FileHandler.get_unique_slno = FileHandler.get_per_row_slno
