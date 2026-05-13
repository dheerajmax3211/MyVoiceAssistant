import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pytesseract
from PIL import Image
from bs4 import BeautifulSoup
import warnings
from bs4 import XMLParsedAsHTMLWarning
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

def _get_bbox(element):
    title = element.get("title", "")
    for part in title.split(";"):
        part = part.strip()
        if part.startswith("bbox"):
            coords = part.replace("bbox", "").strip().split()
            if len(coords) == 4:
                return [int(c) for c in coords]
    return None

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

img = Image.open(r"C:\Users\dheer\Downloads\WhatsApp Image 2026-05-13 at 3.03.30 PM.jpeg")
html = pytesseract.image_to_pdf_or_hocr(img, extension='hocr', config='--psm 3 --oem 3').decode('utf-8')

soup = BeautifulSoup(html, 'lxml')
all_lines = soup.find_all(class_="ocr_line")
line_data = []
for line in all_lines:
    text = " ".join([w.get_text(strip=True) for w in line.find_all(class_="ocrx_word")])
    text = text.strip()
    if not text:
        continue
    bbox = _get_bbox(line)
    if bbox:
        line_data.append({"text": text, "bbox": bbox})

if not line_data:
    print("No lines found")
    sys.exit(0)

line_data.sort(key=lambda x: x["bbox"][1])

import numpy as np
lefts = [ld["bbox"][0] for ld in line_data]
rights = [ld["bbox"][2] for ld in line_data]
heights = [ld["bbox"][3] - ld["bbox"][1] for ld in line_data]

median_left = np.median(lefts)
median_right = np.median(rights)
median_height = np.median(heights)

indent_threshold = median_left + (median_height * 0.8)
short_line_threshold = median_right - (median_height * 1.5)
gap_threshold = median_height * 0.5

print(f"Stats: med_L={median_left:.1f}, med_R={median_right:.1f}, med_H={median_height:.1f}")
print(f"Thresholds: indent={indent_threshold:.1f}, short={short_line_threshold:.1f}, gap={gap_threshold:.1f}")

groups = []
current_group = [line_data[0]]

for i in range(1, len(line_data)):
    prev = line_data[i-1]
    curr = line_data[i]
    
    gap = curr["bbox"][1] - prev["bbox"][3]
    
    is_new_par = False
    reason = ""
    if gap > gap_threshold:
        is_new_par = True
        reason = f"gap ({gap:.1f} > {gap_threshold:.1f})"
    elif prev["bbox"][2] < short_line_threshold:
        is_new_par = True
        reason = f"prev_short ({prev['bbox'][2]} < {short_line_threshold:.1f})"
    elif curr["bbox"][0] > indent_threshold:
        is_new_par = True
        reason = f"indent ({curr['bbox'][0]} > {indent_threshold:.1f})"
        
    if is_new_par:
        print(f"--- NEW PARAGRAPH --- Reason: {reason}")
        groups.append(current_group)
        current_group = [curr]
    else:
        current_group.append(curr)
    print(f"L: {curr['text'][:50]} (L:{curr['bbox'][0]} R:{curr['bbox'][2]} T:{curr['bbox'][1]} B:{curr['bbox'][3]})")
groups.append(current_group)

print(f"\nFound {len(groups)} paragraphs.")
for i, g in enumerate(groups):
    print(f"Par {i}: {' '.join([l['text'] for l in g])[:100]}...")

