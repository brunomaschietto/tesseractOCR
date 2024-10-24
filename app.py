from flask import Flask, request, jsonify
from flask_cors import CORS
import cv2
import pytesseract
from pdf2image import convert_from_path
import os
import unicodedata

app = Flask(__name__)
CORS(app, resources={r"/extract_text": {"origins": "https://www.legnet.com.br"}}) 
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100 MB limite por requisição

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def normalize_text(text):
    return unicodedata.normalize('NFKD', text)

def preprocess_image(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    return binary

def combine_chunks(file_name, total_chunks):
    """ Combina todos os chunks recebidos para formar o arquivo PDF completo """
    with open(file_name, 'wb') as output_file:
        for i in range(total_chunks):
            chunk_file = f"{file_name}_chunk_{i}"
            with open(chunk_file, 'rb') as chunk:
                output_file.write(chunk.read())
            os.remove(chunk_file)  # Remove o chunk após combinar

@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route('/extract_text', methods=['POST'])
def extract_text():
    if 'pdf_chunk' not in request.files:
        return jsonify({'error': 'Nenhum arquivo foi enviado.'}), 400

    chunk = request.files['pdf_chunk']
    chunk_index = int(request.form['chunk_index'])
    total_chunks = int(request.form['total_chunks'])

    file_name = os.path.join(UPLOAD_FOLDER, 'input.pdf')
    
    # Salva o chunk temporariamente
    chunk.save(f"{file_name}_chunk_{chunk_index}")
    
    # Se o último chunk foi recebido, combine todos e processe o PDF
    if chunk_index == total_chunks - 1:
        combine_chunks(file_name, total_chunks)

        # Processamento do arquivo combinado
        images = convert_from_path(file_name, 500)
        pages_text = []

        config = r'--oem 3 --psm 6'
        for i in range(len(images)):
            image_path = f'page{i}.jpg'
            images[i].save(image_path, 'JPEG')

            image = cv2.imread(image_path)
            processed_image = preprocess_image(image)

            text = pytesseract.image_to_string(processed_image, config=config, lang='por')
            normalized_text = normalize_text(text)
            pages_text.append(normalized_text)

            try:
                os.remove(image_path)
            except OSError as e:
                print(f"Erro ao apagar a imagem {image_path}: {e}")

        os.remove(file_name)  # Remove o PDF original após o processamento
        full_text = ' '.join(pages_text)
        tamanho = len(full_text)

        return jsonify({'text': full_text, 'tamanho': tamanho})
    else:
        return jsonify({'status': f'Chunk {chunk_index + 1}/{total_chunks} recebido.'})

if __name__ == '__main__':
    context = ('/etc/letsencrypt/live/www.legnet.com.br/fullchain.pem', 
               '/etc/letsencrypt/live/www.legnet.com.br/privkey.pem')
    app.run(debug=True, host='0.0.0.0', port=5001, ssl_context=context)
