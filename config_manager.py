# config_manager.py

import importlib

VARIABLES = [
    'input_excel', 'last_processed_row', 'max_images_per_site', 'min_image_size',
    'output_dir', 'log_excel', 'summary_json', 'download_concurrency',
    'request_retries', 'timeout', 'log_level', 'executor_workers', 'instances'
]

def load_config():
    """
    Reloads the config.py module and returns a dict of our VARIABLES.
    """
    import config as _cfg
    importlib.reload(_cfg)
    return {v: getattr(_cfg, v) for v in VARIABLES}

def update_last_row(row: int):
    """
    Updates last_processed_row in the *actual* config.py file on disk.
    """
    # Reload to pick up latest values
    cfg = load_config()

    # Set the new last_processed_row
    cfg['last_processed_row'] = row

    # Figure out exactly where config.py lives
    import config as _cfg_mod
    path = _cfg_mod.__file__
    # If it's a .pyc, strip that off
    if path.endswith('.pyc'):
        path = path[:-1]

    # Build the file contents
    lines = ['# config.py', '']
    for k in VARIABLES:
        lines.append(f"{k} = {repr(cfg[k])}")
    lines.append('')

    # Overwrite the real config.py
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
