import cv2
import pytesseract
from pdf2image import convert_from_path
import os
import json
import unicodedata

def normalize_text(text):
    return unicodedata.normalize('NFKD', text)

def preprocess_image(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    return binary

images = convert_from_path('L4320.pdf', 500, poppler_path=r'C:\Program Files\poppler-24.02.0\Library\bin')
pytesseract.pytesseract.tesseract_cmd = "C:\Program Files\Tesseract-OCR\Tesseract.exe"

pages_text = {}

tessdata_dir_config = r'--tessdata-dir "C:\Program Files\Tesseract-OCR\tessdata"'

config = r'--oem 3 --psm 6 ' + tessdata_dir_config

for i in range(len(images)):
    image_path = 'page' + str(i) + '.jpg'
    images[i].save(image_path, 'JPEG')

    image = cv2.imread(image_path)


    processed_image = preprocess_image(image)

    text = pytesseract.image_to_string(processed_image, config=config, lang='por')

    normalized_text = normalize_text(text)

    pages_text[f'page_{i}'] = normalized_text

    try:
        os.remove(image_path)
        print(f"Imagem {image_path} apagada com sucesso.")
    except OSError as e:
        print(f"Erro ao apagar a imagem {image_path}: {e}")

pages_text_json = json.dumps(pages_text, indent=4, ensure_ascii=False)

with open('output.json', 'w', encoding='utf-8') as json_file:
    json_file.write(pages_text_json)

print("Texto extraído salvo em output.json")