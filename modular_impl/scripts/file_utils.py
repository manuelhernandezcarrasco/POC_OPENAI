import fitz
from PIL import Image
import pytesseract

def extract_text_from_pdf(path: str) -> str:
    doc = fitz.open(path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text.strip()

def extract_text_from_image(path: str) -> str:
    image = Image.open(path)
    return pytesseract.image_to_string(image).strip()

def extract_text(path: str) -> str:
    if path.lower().endswith(".pdf"):
        return extract_text_from_pdf(path)
    else:
        return extract_text_from_image(path)
