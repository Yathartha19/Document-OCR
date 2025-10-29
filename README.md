# Document OCR

This project automates **data extraction from scanned documents or images** (like invoices, forms, certificates, etc.) using **OCR (Optical Character Recognition)** and aligns the extracted text to a **custom template** for consistent structured output.  
It supports both **image (`.png`, `.jpg`, `.jpeg`)** and **PDF** inputs and saves aligned results as `.txt`.
Saves all input documents into a single excel file for batch processing.

---

## Folder Structure
```text
project/
│
├── data/
│ ├── input/ # Place your input images or PDFs here
│ ├── output/ # Processed files and results will appear here
│ │ ├── <file_name>/ # Individual folders for each file
│ │ │ ├── raw_ocr.txt # Raw OCR text (as detected by model)
│ │ │ ├── aligned.txt # Text aligned to the template
│ │ │ └── preview.png # Cleaned image preview (optional)
│ │ └── results.xlsx # Master Excel file with all key-value results
│ │
│ ├── sample_input/ # Example input images
│ └── sample_output/ # Example output folders
│
├── template.txt # Template keys (one per line)
├── main.py # Main script
├── requirements.txt # Python dependencies
└── README.md # Project documentation
```

---

## How It Works

1. **Preprocessing**  
   Each image is cleaned using OpenCV (bilateral filtering) to improve OCR accuracy.

2. **OCR Extraction**  
   The [DocTR OCR model](https://mindee.github.io/doctr) extracts all text lines from the image.

3. **Template Alignment**  
   The script compares extracted text with the template keys using fuzzy matching (`rapidfuzz`) and extracts corresponding values.  
   Example:

Template Key: Domain Name
Extracted Text: Domain Name : example.com
Output: {"Domain Name": "example.com"}


4. **Saving Results**  
- Creates a new folder under `data/output/<file_name>/`  
- Saves `raw_ocr.txt`, `aligned.txt`, and `preview.png`  
- Appends results to `data/output/results.xlsx`  

---

## How to Use

### Install Dependencies

Create a virtual environment and install all required packages:

```bash
pip install -r requirements.txt
```

### Add Template Keys

Edit data/template.txt and add all key names you want to extract, one per line:

Domain Name
Expiry Date
Registrant Name
Registrant Email

### Add Input Files

Place all input images or PDFs in the data/input/ directory.

### Run the Script
python main.py

### View Output

After running:

Aligned and raw text → data/output/<file_name>/

Consolidated Excel → data/output/results.xlsx


## Author

Developed by Yathartha Aarush
For invoice automation, OCR alignment, and structured data extraction.


