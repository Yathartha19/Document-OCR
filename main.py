import os, cv2, re, gc
from tqdm import tqdm
from pdf2image import convert_from_path
from doctr.models import ocr_predictor
import torch
from rapidfuzz import process, fuzz
import pandas as pd

INPUT_DIR = "data/input"
OUTPUT_DIR = "data/output"
TEMPLATE_PATH = "data/template.txt"
EXCEL_PATH = os.path.join(OUTPUT_DIR, "results.xlsx")
os.makedirs(OUTPUT_DIR, exist_ok=True)

device = "cuda" if torch.cuda.is_available() else "cpu"
ocr_model = ocr_predictor(pretrained=True).to(device)

# ---------- preprocess ----------
def preprocess_image(path):
    img = cv2.imread(path)
    if img is None:
        raise FileNotFoundError(path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = cv2.bilateralFilter(img, 9, 17, 17)
    return img

# ---------- OCR ----------
def extract_text_lines(img):
    result = ocr_model([img])
    lines = []
    for block in result.export()["pages"][0]["blocks"]:
        for line in block["lines"]:
            txt = " ".join([w["value"] for w in line["words"]]).strip()
            if txt:
                lines.append(txt)
    return lines

# ---------- align ----------
def load_template_keys(path):
    with open(path, "r", encoding="utf-8") as f:
        keys = [line.strip() for line in f if line.strip()]
    return keys

def align_to_template(ocr_lines, template_keys, threshold=75):
    joined_text = " ".join(ocr_lines)
    joined_text = re.sub(r"\s*:\s*", " : ", joined_text)

    pattern = "|".join(re.escape(k).replace("\\ ", "\\s*") for k in template_keys)
    matches = list(re.finditer(pattern, joined_text, flags=re.IGNORECASE))

    kv_pairs = {}
    for i, m in enumerate(matches):
        key = template_keys[
            process.extractOne(m.group(), template_keys, scorer=fuzz.token_sort_ratio)[2]
        ]
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(joined_text)
        value = joined_text[start:end].strip(" :-\n\t")
        value = re.sub(r"\s{2,}", " ", value)
        kv_pairs[key] = value

    for k in template_keys:
        if k not in kv_pairs:
            kv_pairs[k] = ""
    return kv_pairs

# ---------- save outputs ----------
def save_outputs(ocr_lines, kv, base):
    base_dir = os.path.join(OUTPUT_DIR, base)
    os.makedirs(base_dir, exist_ok=True)

    raw_path = os.path.join(base_dir, "raw_ocr.txt")
    aligned_path = os.path.join(base_dir, "aligned.txt")

    with open(raw_path, "w", encoding="utf-8") as f:
        f.write("\n".join(ocr_lines))
    print(f"🧾 Saved raw OCR text → {raw_path}")

    with open(aligned_path, "w", encoding="utf-8") as f:
        for k, v in kv.items():
            f.write(f"{k} : {v.strip()}\n")
    print(f"✅ Saved aligned text → {aligned_path}")

# ---------- save to excel ----------
def save_to_excel(kv, base):
    df = pd.DataFrame([kv])
    df.insert(0, "FileName", base)

    if os.path.exists(EXCEL_PATH):
        existing_df = pd.read_excel(EXCEL_PATH)
        combined_df = pd.concat([existing_df, df], ignore_index=True)
        combined_df.to_excel(EXCEL_PATH, index=False)
    else:
        df.to_excel(EXCEL_PATH, index=False)

    print(f"📊 Updated Excel → {EXCEL_PATH}")

# ---------- process File ----------
def process_file(path, template_keys):
    name = os.path.basename(path)
    base, _ = os.path.splitext(name)
    print(f"\n📄 Processing: {name}")

    # Convert PDF → image
    if path.lower().endswith(".pdf"):
        pages = convert_from_path(path, dpi=300)
        img_path = os.path.join(OUTPUT_DIR, f"temp_{base}.png")
        pages[0].save(img_path, "PNG")
    else:
        img_path = path

    img = preprocess_image(img_path)
    ocr_lines = extract_text_lines(img)
    kv = align_to_template(ocr_lines, template_keys)

    save_outputs(ocr_lines, kv, base)
    save_to_excel(kv, base)

    preview_path = os.path.join(OUTPUT_DIR, base, "preview.png")
    cv2.imwrite(preview_path, cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
    gc.collect()

# ---------- main ----------
def main():
    if not os.path.exists(TEMPLATE_PATH):
        print("⚠️ Missing template.txt.")
        return

    template_keys = load_template_keys(TEMPLATE_PATH)
    print(f"📋 Loaded {len(template_keys)} keys from template")

    files = [
        os.path.join(INPUT_DIR, f)
        for f in os.listdir(INPUT_DIR)
        if f.lower().endswith((".pdf", ".jpg", ".jpeg", ".png"))
    ]
    if not files:
        print("⚠️ No input files found.")
        return

    for f in tqdm(files, ncols=90):
        process_file(f, template_keys)

    print("\n🎉 All files processed successfully!")

if __name__ == "__main__":
    main()
