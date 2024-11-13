import pandas as pd
import re
import requests
import time
import os
from bs4 import BeautifulSoup
from collections import defaultdict
from PIL import Image
import pytesseract
from io import BytesIO

# Set the path to your Tesseract executable if needed
# pytesseract.pytesseract.tesseract_cmd = r'/path/to/tesseract'

def extract_clean_tickers(excel_file, sheet_name=0):
    df = pd.read_excel(excel_file, sheet_name=sheet_name)
    if 'Ticker Symbol' not in df.columns:
        raise ValueError("The Excel file does not contain the 'Ticker Symbol' column.")
    tickers = df['Ticker Symbol'].dropna()
    tickers = tickers.str.strip()
    tickers = tickers.str.replace(r'\..*', '', regex=True)
    tickers = tickers[tickers.str.match(r'^[A-Za-z]+$')]
    tickers = tickers.str.upper()
    tickers = tickers.unique()
    tickers = sorted(tickers)
    return tickers

api_key = "4c760d9988d08a39c264deca0af915ca06b5dac43aa0de77b1ea137d839ed88c"

def fetch_def14a_filing_urls(ticker, from_year, to_year):
    base_query = {
        "query": f"ticker:{ticker} AND formType:DEF 14A AND filedAt:[{from_year}-01-01 TO {to_year}-12-31]",
        "from": "0",
        "size": "200"
    }
    filing_urls = []
    from_record = 0
    print(f"Fetching data starting from record {from_record} for {ticker}...")
    while True:
        base_query["from"] = str(from_record)
        response = requests.post("https://api.sec-api.io", headers={"Authorization": api_key}, json=base_query)
        if response.status_code == 200:
            data = response.json()
            filings = data.get("filings", [])
            if not filings:
                break
            for filing in filings:
                filing_urls.append(filing["linkToFilingDetails"])
            from_record += 200
            print(f"Fetched {len(filings)} filings. Total filings: {len(filing_urls)}")
            time.sleep(0.1)
        else:
            print(f"Error fetching data: {response.status_code} - {response.text}")
            break
    return filing_urls

def download_filing(url):
    try:
        parts = url.split('/')
        if len(parts) < 9:
            print(f"Skipping invalid URL: {url}")
            return None

        cik = parts[6]
        accession_number = parts[7].replace('-', '')
        filename = parts[8]
        year = filename.split('_')[-1].split('.')[0]

        filepath = f"filings/{filename}"
        if os.path.exists(filepath):
            print(f"File {filename} already exists. Skipping download.")
            return filepath, year
        
        download_url = f"https://archive.sec-api.io/{cik}/{accession_number}/{filename}?token={api_key}"
        
        print(f"Downloading {filename} from {download_url}...")
        response = requests.get(download_url)
        if response.status_code == 200:
            with open(filepath, "wb") as f:
                f.write(response.content)
            print(f"Downloaded and saved {filename}.")
            time.sleep(0.1)
            return filepath, year
        else:
            print(f"Error downloading {filename}: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return None

def extract_words_from_html(filepath):
    encodings = ['utf-8', 'latin-1', 'iso-8859-1']
    for encoding in encodings:
        try:
            with open(filepath, 'r', encoding=encoding) as file:
                soup = BeautifulSoup(file, 'html.parser')
                text = soup.get_text()
                words = text.split()
                return words
        except UnicodeDecodeError:
            continue
    print(f"Skipping file {filepath} due to incompatible encodings.")
    return None

def extract_images_from_html(filepath):
    image_urls = []
    with open(filepath, 'r', encoding='utf-8') as file:
        soup = BeautifulSoup(file, 'html.parser')
        images = soup.find_all('img')
        image_urls = [img['src'] for img in images if 'src' in img.attrs]
    return image_urls

def ocr_image(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            img = Image.open(BytesIO(response.content))
            text = pytesseract.image_to_string(img)
            return text
        else:
            return ""
    except Exception as e:
        return ""

def extract_tables_from_html(filepath):
    tables = []
    with open(filepath, 'r', encoding='utf-8') as file:
        soup = BeautifulSoup(file, 'html.parser')
        table_elements = soup.find_all('table')
        for table in table_elements:
            rows = table.find_all('tr')
            table_data = []
            for row in rows:
                cols = row.find_all('td')
                cols = [ele.text.strip() for ele in cols]
                table_data.append(cols)
            tables.append(table_data)
    return tables

def extract_performance_based_compensation(filepath):
    percentages = []
    
    words = extract_words_from_html(filepath)
    if words is None:
        return ["No data found"]
    
    pattern = re.compile(r'performance[- ]based', re.IGNORECASE)
    indices = [i for i, word in enumerate(words) if pattern.match(word)]
    
    for index in indices:
        window_start = max(0, index - 10)
        window_end = min(len(words), index + 11)
        window = words[window_start:window_end]
        context = ' '.join(window)
        for word in window:
            match = re.search(r'(\d{1,2}(?:\.\d{1,2})?)%', word)
            if match:
                if re.search(r'\b(compensation|vested|earned|target|threshold|goal|award)\b', context, re.IGNORECASE):
                    if float(match.group(1)) > 10:
                        percentages.append(float(match.group(1)))
    
    if not percentages:
        image_urls = extract_images_from_html(filepath)
        for img_url in image_urls:
            ocr_text = ocr_image(img_url)
            if ocr_text:
                ocr_words = ocr_text.split()
                ocr_indices = [i for i, word in enumerate(ocr_words) if pattern.match(word)]
                for index in ocr_indices:
                    window_start = max(0, index - 10)
                    window_end = min(len(ocr_words), index + 11)
                    window = ocr_words[window_start:window_end]
                    context = ' '.join(window)
                    for word in window:
                        match = re.search(r'(\d{1,2}(?:\.\d{1,2})?)%', word)
                        if match:
                            if re.search(r'\b(compensation|vested|earned|target|threshold|goal|award)\b', context, re.IGNORECASE):
                                if float(match.group(1)) > 10:
                                    percentages.append(float(match.group(1)))
    
    if not percentages:
        tables = extract_tables_from_html(filepath)
        for table in tables:
            for row in table:
                for cell in row:
                    cell_words = cell.split()
                    for word in cell_words:
                        match = re.search(r'(\d{1,2}(?:\.\d{1,2})?)%', word)
                        if match:
                            if re.search(r'\b(compensation|vested|earned|target|threshold|goal|award)\b', cell, re.IGNORECASE):
                                if float(match.group(1)) > 10:
                                    percentages.append(float(match.group(1)))
    
    if percentages:
        highest_percentage = max(percentages)
        return [highest_percentage]
    else:
        return ["No data found"]

def main():
    excel_file = "/Users/milindsm2pro/Desktop/Summer Research/final data.xlsx"
    tickers = extract_clean_tickers(excel_file)
    from_year = 1994
    to_year = 2023
    excel_file_2 = "/Users/milindsm2pro/Desktop/Summer Research/final compensation data-iterative.xlsx"
    
    if not os.path.exists("filings"):
        os.makedirs("filings")
    
    data = defaultdict(list)
    
    for ticker in tickers:
        filing_urls = fetch_def14a_filing_urls(ticker, from_year, to_year)
        
        for url in filing_urls:
            result = download_filing(url)
            if result:
                filepath, year = result
                if os.path.isfile(filepath):
                    print(f"Processing file for year {year}...")
                    percentages = extract_performance_based_compensation(filepath)
                    data['Ticker'].append(ticker)
                    data['Year'].append(year)
                    data['Performance Based Compensation'].append(percentages)
                    
                    # Save to Excel after each ticker is processed
                    df = pd.DataFrame(data)
                    df.to_excel(excel_file_2, index=False)
                    print(f"Data for {ticker} saved to {excel_file}.")
    
    print("Data extraction and saving complete.")

if __name__ == "__main__":
    main()
