from flask import Flask, request, jsonify
from flask_cors import CORS
import cv2
import pytesseract
from pdf2image import convert_from_path
import os
import unicodedata

app = Flask(__name__)
CORS(app, resources={r"/extract_text": {"origins": "https://www.legnet.com.br"}}) 
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # Limite de 100 MB

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def normalize_text(text):
    return unicodedata.normalize('NFKD', text)

def preprocess_image(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    return binary

@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route('/extract_text', methods=['POST'])
def extract_text():
    if 'pdf' not in request.files:
        return jsonify({'error': 'Nenhum arquivo foi enviado.'}), 400

    file = request.files['pdf']
    file.save(os.path.join(UPLOAD_FOLDER, 'input.pdf'))

    # Converte o PDF em imagens
    images = convert_from_path(os.path.join(UPLOAD_FOLDER, 'input.pdf'), 500)
    pages_text = []

    config = r'--oem 3 --psm 6'

    for i, image in enumerate(images):
        # Processa cada página
        processed_image = preprocess_image(image)

        # Converte a imagem em texto
        text = pytesseract.image_to_string(processed_image, config=config, lang='por')
        normalized_text = normalize_text(text)
        pages_text.append(normalized_text)

        # Aqui você pode querer dividir o texto em pedaços, se necessário
        # Se o texto for muito grande, você pode armazenar em uma lista ou apenas
        # dividir em partes menores
        if len(pages_text) > 0 and len(pages_text[-1]) > 10000:  # Exemplo: dividir se maior que 10.000 caracteres
            pages_text[-1] = pages_text[-1][:10000]  # Limita a 10.000 caracteres
            pages_text.append("...")  # Indicador de que o texto foi cortado

    os.remove(os.path.join(UPLOAD_FOLDER, 'input.pdf'))  # Remove o PDF original após o processamento
    full_text = ' '.join(pages_text)
    tamanho = len(full_text)

    return jsonify({'text': full_text, 'tamanho': tamanho})

if __name__ == '__main__':
    context = ('/etc/letsencrypt/live/www.legnet.com.br/fullchain.pem', 
               '/etc/letsencrypt/live/www.legnet.com.br/privkey.pem')
    app.run(debug=True, host='0.0.0.0', port=5001, ssl_context=context)
