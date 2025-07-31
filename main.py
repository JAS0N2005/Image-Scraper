import asyncio
import logging
import os

from utils import (
    load_config, setup_logging,
    ensure_log_csv, log_skip, log_downloaded, log_failure,
    get_next_row, update_next_row
)
from input_processor import process_input_excel
from file_handler import FileHandler
from image_scraper import ImageScraper
from image_filter import ImageFilter
from image_deduplicator import ImageDeduplicator
from image_converter import ImageConverter
from ocr_logo_detector import load_ml_model

def csv_has_data_rows(csv_path):
    import csv
    if not os.path.exists(csv_path):
        return False
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)
    if len(rows) <= 1:
        return False
    for row in rows[1:]:
        if row and row[5].strip().lower() == "pending":
            return True
    return False

async def process_row(row, config, scraper, image_filter, deduper, converter, file_handler, ml_model):
    row_num = int(row['Row'])
    activity_id = row['ActivityId']
    row_type = row.get('Type', '')
    website = row['Website']

    downloads = 0
    perfect = 0
    failures = 0
    attempts = 0

    skip_reason = None
    if not website or not website.startswith("http"):
        skip_reason = "Invalid or missing URL"
    elif "facebook.com" in website or "instagram.com" in website:
        skip_reason = "Social link"
    elif not file_handler.is_valid_url(website):
        skip_reason = "Invalid URL format"

    if skip_reason:
        log_skip(config, row_num, activity_id, skip_reason)
    else:
        async for info in scraper.scrape_images(website, row, config):
            attempts += 1
            ok, img, flag = await image_filter.process_image(info, config, ml_model)
            if not ok:
                failures += 1
                log_failure(config, row_num, activity_id, f"DownloadFailed:{info.get('src')}")
                continue
            if img is None:
                failures += 1
                log_failure(config, row_num, activity_id, f"OpenError:{info.get('src')}")
                continue
            if not deduper.is_unique(img):
                failures += 1
                log_failure(config, row_num, activity_id, f"Duplicate:{info.get('src')}")
                continue

            img = converter.ensure_png(img)
            slno = file_handler.get_per_row_slno(activity_id)
            out_name = file_handler.get_output_name(row, slno, flag)
            saved_path = file_handler.move_to_output(img, out_name)
            log_downloaded(config, row_num, activity_id, out_name)
            downloads += 1
            if not flag:
                perfect += 1
            if downloads >= config["IMAGES_PER_SITE"]:
                break

    print(f"Row:{row_num} | ActivityId:{activity_id} | Type:{row_type} | Website:{website}")
    print(f"Downloads:{downloads} | Perfect:{perfect} | Failures:{failures} | Attempts:{attempts}")

async def main():
    config = load_config()
    setup_logging(config["LOG_FILE"])
    ensure_log_csv(config)

    if not os.path.exists(config["DATA_LOG_CSV"]) or not csv_has_data_rows(config["DATA_LOG_CSV"]):
        print("Generating CSV from Excel...")
        process_input_excel(config)
        print(f"Generated {config['DATA_LOG_CSV']}")

    total_rows, next_row = get_next_row(config)
    print(f"Resuming from row {next_row} of {total_rows}")

    fh = FileHandler(config)
    scraper = ImageScraper(config)
    image_filter = ImageFilter(config)
    deduper = ImageDeduplicator(config)
    converter = ImageConverter(config)
    ml_model = load_ml_model(config) if config["LOGO_DETECTION_BACKEND"] == "ml" else None

    for row in fh.iter_input_rows(config, next_row):
        await process_row(row, config, scraper, image_filter, deduper, converter, fh, ml_model)
        update_next_row(config, int(row['Row']) + 1)

    print("Processing complete.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Interrupted by user. Exiting.")
