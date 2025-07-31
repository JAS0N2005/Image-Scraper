# 🧠 Advanced Website Image Scraper with Filtering, Deduplication & OCR

This program is a **high-performance, AI-assisted image scraper** built to extract clean, high-quality images from websites listed in an Excel file. It includes:

- Website scraping via Playwright
- Asynchronous downloading with filtering
- OCR & logo detection (OpenCV & ML-based)
- Image format conversion
- Hash-based deduplication
- CSV logging, retry, and resume support

---

## 📦 Features

- ✅ Scrapes images from websites while skipping social media links
- 📜 Logs every attempt in a `log.csv` file
- 🧼 Filters out images with logos or text using OCR or ML
- 🔁 Automatically retries on failure (configurable)
- 🧠 Converts `.webp`, `.svg`, `.tmp` to `.png`
- 📂 Outputs well-named files into a configured output directory
- 🔐 Locks CSVs for safe concurrent access

---

## ⚙️ Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/your-username/your-repo.git
cd your-repo
```

### 2. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 3. Install additional dependencies

- **Playwright (headless browser engine)**
```bash
pip install playwright
playwright install
```

- **Tesseract OCR** (for text/logo detection)

Install from: https://github.com/tesseract-ocr/tesseract  
And set the path in `ocr_logo_detector.py`:
```python
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
```

- **CairoSVG** (for converting SVGs)
```bash
pip install cairosvg
```

---

## 📁 Input/Output Structure

### `config.json` (example)
```json
{
  "INPUT_EXCEL": "path/to/input.xlsx",
  "DATA_LOG_CSV": "Logs/log.csv",
  "LOG_FILE": "Logs/logfile.log",
  "OUTPUT_FOLDER": "ScrapedImages/",
  "IMAGES_PER_SITE": 10,
  "MIN_IMG_SIZE": 250,
  "DETECTION_MODE": "Flag",
  "LOGO_DETECTION_BACKEND": "opencv",
  "LOGO_MODEL_PATH": "",
  "HEADLESS": false,
  "MAX_RETRIES": 2,
  "RETRY_BACKOFF": 2,
  "DOWNLOAD_CONCURRENCY": 10,
  "NEXT_ROW": 1
}
```

---

## ▶️ How to Run

```bash
python main.py
```

- On first run, it will parse the Excel and create `log.csv`.
- It will skip rows with social media links or invalid URLs.
- It resumes from the last `NEXT_ROW` position.
- Images are named like: `ActivityId_Type_Slno_[FLAG].png`

---

## 📘 Excel Format

The Excel file must contain the following columns:
- `Name`
- `Type`
- `Website` (must start with `http`)
- `ActivityId`

---

## 🧠 Module Overview

| File | Purpose |
|------|---------|
| `main.py` | Orchestrates the scraping, filtering, deduplication, conversion and logging pipeline. |
| `input_processor.py` | Reads Excel and creates `log.csv` with status tracking. |
| `image_scraper.py` | Uses Playwright to load websites and extract image URLs (with scroll). |
| `image_filter.py` | Downloads and filters images with OCR/logo detection. |
| `ocr_logo_detector.py` | Detects text and logos using Tesseract, OpenCV, or ML (TFLite). |
| `image_deduplicator.py` | Avoids duplicates by comparing hashes and image area. |
| `image_converter.py` | Converts WebP, SVG, or other formats to PNG. |
| `file_handler.py` | Handles image saving, naming, and row iteration with file locking. |
| `utils.py` | Helpers for logging, config handling, retry logic, and CSV lock-safe operations. |

---

## 🛠 Advanced Features

- **Detection Modes:**
  - `"Flag"`: Tags images but keeps them
  - `"Erase"`: Discards images with detected logo/text

- **Logo Detection Engines:**
  - `"opencv"`: Uses classical techniques
  - `"ml"`: Requires TFLite model (path in `LOGO_MODEL_PATH`)

- **Automatic Retry with Backoff**
  - Configurable via `MAX_RETRIES` and `RETRY_BACKOFF`

- **CSV Locking with `portalocker`**
  - Ensures safe read/write in concurrent environments

---

## 📄 Sample `requirements.txt`

```
aiohttp
pandas
openpyxl
pillow
playwright
cairosvg
tqdm
portalocker
pytesseract
scikit-image
opencv-python
tensorflow
```

---

## 🧪 Example Workflow

1. Prepare Excel with valid websites.
2. Adjust `config.json`.
3. Run `python main.py`.
4. Check progress in `log.csv` and output images in your configured folder.

---

## 📬 Support

Raise an issue or contact the maintainer for questions, bugs, or feature requests.

