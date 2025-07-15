# run.py

import asyncio
import pandas as pd
import json
import aiohttp
import multiprocessing
from concurrent.futures import ThreadPoolExecutor
from config_manager import load_config
from logger import setup_logging
from processor import process_row

async def main():
    cfg = load_config()

    # Auto-tune per-instance CPU slice
    total_cpus = multiprocessing.cpu_count()
    per_bot = max(1, total_cpus // cfg.get('instances', 1))
    cfg['executor_workers'] = per_bot
    cfg['download_concurrency'] = per_bot

    setup_logging(cfg['log_level'])
    executor = ThreadPoolExecutor(max_workers=cfg['executor_workers'])
    loop = asyncio.get_event_loop()
    loop.set_default_executor(executor)

    df = pd.read_excel(cfg['input_excel'])
    start = cfg['last_processed_row']
    summary = []
    async with aiohttp.ClientSession() as session:
        for idx, row in df.iloc[start:].iterrows():
            await process_row(
                session,
                idx,
                row['Type'],
                row['ActivityId'],
                row['Website'],
                summary,
                cfg
            )

    with open(cfg['summary_json'], 'w') as f:
        json.dump(summary, f, indent=2)

if __name__ == '__main__':
    asyncio.run(main())
