"""Test the OCR pipeline against the two sample book page images."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image

# Import OCR functions from server
from server import ocr_image, process_page_elements

IMAGES = [
    r"C:\Users\dheer\Downloads\WhatsApp Image 2026-05-13 at 3.03.30 PM.jpeg",
    r"C:\Users\dheer\Downloads\1.jpeg",
]

for img_path in IMAGES:
    print(f"\n{'='*70}")
    print(f"IMAGE: {os.path.basename(img_path)}")
    print(f"{'='*70}")
    
    pil_img = Image.open(img_path)
    elements = ocr_image(pil_img)
    elements = process_page_elements(elements)
    
    print(f"Total elements: {len(elements)}\n")
    for i, el in enumerate(elements):
        tag = f"[{el['type'].upper()}"
        if el.get('level'):
            tag += f" L{el['level']}"
        tag += "]"
        print(f"  {i+1}. {tag}")
        # Indent the text for readability
        text = el['text']
        if len(text) > 120:
            print(f"     {text[:120]}...")
        else:
            print(f"     {text}")
        print()
