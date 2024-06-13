import os
from flask import Flask, request, redirect, url_for, render_template
import fitz  # PyMuPDF
import cv2
import numpy as np
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def upload_file():
    return render_template('upload.html')

@app.route('/uploader', methods=['POST'])
def uploader():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Если загружен PDF, конвертировать в PNG
            if filename.rsplit('.', 1)[1].lower() == 'pdf':
                convert_pdf_to_png(filepath, app.config['UPLOAD_FOLDER'])
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'page_1.png')
            else:
                image_path = filepath
            
            coordinates = process_image(image_path)
            return render_template('result.html', coordinates=coordinates)
    return redirect(url_for('upload_file'))

def convert_pdf_to_png(pdf_path, output_folder):
    pdf_document = fitz.open(pdf_path)
    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        pix = page.get_pixmap()
        output_path = f"{output_folder}/page_{page_num + 1}.png"
        pix.save(output_path)
        print(f"Saved {output_path}")
    pdf_document.close()

def process_image(image_path):
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    coordinates = []
    for contour in contours:
        for point in contour:
            x, y = point[0]
            coordinates.append((x, y))
    
    return coordinates

if __name__ == '__main__':
    app.run(debug=True)
