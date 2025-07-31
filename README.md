# 📸 Ultra-Robust Image Scraper with Static + Dynamic Parsing

This project is an **enterprise-grade web image scraper** designed to extract high-quality images from websites listed in an Excel file. It uses a **multi-layered extraction system** combining HTML parsing, CSS background scanning, and Selenium-based dynamic scraping. Built for performance, reliability, and resilience.

---

## ⚙️ Features

- ✅ HTML parsing with BeautifulSoup
- 🔁 CSS background-image extraction
- 🧠 Dynamic fallback via headless Selenium (Chrome)
- 📦 Concurrent image downloading with size checks
- 🧹 Automatic deduplication via MD5 hash
- 📊 Per-row logging in Excel + JSON summary
- 🔐 Safe config update with `config.py` editing

---

## 🛠 Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/your-username/image-scraper.git
cd image-scraper
```

### 2. Install requirements
```bash
pip install -r requirements.txt
```

### 3. Install Selenium dependencies
- **Install Chrome** (if not already installed)
- **Install ChromeDriver** and ensure it's in your PATH:
  - Download: https://sites.google.com/chromium.org/driver/

---

## 🔧 Configuration

All settings are controlled in `config.py`:

```python
input_excel = 'input.xlsx'
last_processed_row = 0
max_images_per_site = 10
min_image_size = [250, 250]
output_dir = 'ScrapedImages/'
log_excel = 'Logs/log.xlsx'
summary_json = 'Logs/summary.json'
download_concurrency = 4
request_retries = 1
timeout = 10
log_level = 'INFO'
executor_workers = 4
instances = 6
```

To safely update the last processed row, use the included method:
```python
from config_manager import update_last_row
update_last_row(25)
```

---

## ▶️ How to Run

```bash
python run.py
```

- The script starts from `last_processed_row`.
- Logs each processed row to the Excel log.
- Generates a JSON summary at the end.

---

## 🧠 Module Overview

| File | Purpose |
|------|---------|
| `run.py` | Main driver script; handles row iteration and summary writing. |
| `config.py` | Stores all runtime config. |
| `config_manager.py` | Dynamically reloads and updates `config.py`. |
| `logger.py` | Sets up Python logging. |
| `processor.py` | Processes each row, launches `RowProcessor`, logs results. |
| `processor_core.py` | Core image fetching, filtering, deduplication logic. |
| `parser.py` | Extracts images from HTML, inline CSS, `<img>`, `<source>`. |
| `dynamic_fetcher.py` | Selenium-based dynamic scraper with scroll, click, and bg-image detection. |
| `fetcher.py` | HTML and CSS fetch logic with retry support. |
| `downloader.py` | Downloads and saves images to disk with size checks. |

---

## 📋 Excel Input Format

Must contain the following columns:
- `Type`
- `ActivityId`
- `Website`

---

## 🧪 Internal Flow

1. **Read Excel** from `input_excel` and start at `last_processed_row`.
2. For each row:
   - Try HTML fetch → parse images from tags, styles, and external CSS.
   - If not enough images: fallback to Selenium-based scraping.
   - Download images (concurrent) with minimum size check.
   - Deduplicate using hash.
   - Log each outcome in Excel and append to summary JSON.
3. Save updated row and config.

---

## ✅ Image Naming Convention

```
<ActivityId>_<Type>_<n>.ext
```

---

## 📄 Sample requirements.txt

```
aiohttp
openpyxl
pandas
beautifulsoup4
selenium
lxml
pillow
```

---
## Contributing

Yours truly
Subhojyoti :]

---
