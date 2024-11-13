# Performance-Based Compensation Extractor

This Python script processes HTML filings to extract performance-based compensation data. The HTML files, located in the `filings` folder, contain data sourced from the WRDS (Wharton Research Data Services) and organized through the SEC API. The files are divided alphabetically by company name into six groups, and were downloaded in parallel for efficiency.

## Prerequisites

- **Python 3.7+**
- **Libraries**:
  - `pandas`
  - `bs4` (BeautifulSoup)
  - `Pillow`
  - `pytesseract`
  - `requests`

Install the necessary libraries via:

```bash
pip install pandas beautifulsoup4 pillow pytesseract requests
```

### Additional Setup

1. **Tesseract OCR**: For OCR text extraction from images, install Tesseract. Download from: https://github.com/tesseract-ocr/tesseract.

2. **filings Directory**: The `filings` folder should contain HTML files organized into six groups (A-F), each covering companies in alphabetical order. 

   - **Groups**:
     - Group 1: A-C
     - Group 2: D-F
     - Group 3: G-I
     - Group 4: J-L
     - Group 5: M-O
     - Group 6: P-Z

   - **SEC API**: The files were downloaded using the SEC API, which limits data from 2000 to 2023. Companies were split into the above alphabetical groups to manage the number of requests and balance load through parallel processing.

## Code Overview

The script processes each file to extract and compute performance-based compensation values using text, images, and table data. The final results are saved in an Excel file.

### Functions

#### 1. `extract_words_from_html(filepath)`
   - Reads and extracts text from an HTML file.
   - Handles encoding differences for compatibility.

#### 2. `extract_images_from_html(filepath)`
   - Finds and returns a list of image URLs from HTML content.

#### 3. `ocr_image(url)`
   - Downloads and performs OCR on image URLs to extract text.

#### 4. `extract_tables_from_html(filepath)`
   - Parses HTML tables and stores data for further analysis.

#### 5. `extract_performance_based_compensation(filepath)`
   - **Extraction Steps**:
     - **Text**: Scans for terms like “performance-based” and looks for nearby percentages associated with compensation-related terms.
     - **Images**: If text search fails, performs OCR on images to check for similar compensation data.
     - **Tables**: If both text and images fail, it searches tables for a "Compensation Summary" table and calculates the percentage of "Performance Stock Units" relative to "Total Compensation."

#### 6. `extract_year_from_html(filepath)`
   - Extracts the filing year from metadata.

### Main Function `main()`

1. **Directory Setup**: The `filings` folder is checked for files. If none are found, the script terminates.
2. **Data Processing**:
   - Processes each file to extract **Ticker**, **Filename**, **Year**, and **Performance Based Compensation**.
   - Each file is marked as processed to avoid duplication.
3. **Output to Excel**: Saves the data to `final_performance_data.xlsx`.

## Usage

To run the script:

```bash
python script_name.py
```

This script does not redownload files but checks only those stored in the `filings` folder, making it suitable for batch processing.

## Output

The script produces an Excel file with columns for:
- **Ticker**: The stock ticker (from filename).
- **Filename**: Name of the processed file.
- **Year**: Filing year.
- **Performance Based Compensation**: Highest calculated performance-based compensation percentage.

## Data Source

1. **WRDS**: Data for the S&P 500 companies was initially downloaded from WRDS.
2. **SEC API**: Filings were retrieved through the SEC API, which limits available data to filings from 2000-2023.

## Parallel Downloading

The SEC data was divided into six alphabetical groups, processed in parallel for efficiency. Each file represents a subset of S&P 500 companies, helping manage API limits and processing time.

---

This README explains the data extraction process, folder setup, data organization, and the intended outputs, allowing other users to understand and replicate this methodology.
