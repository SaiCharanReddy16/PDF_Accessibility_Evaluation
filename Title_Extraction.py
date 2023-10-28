from flask import Flask, render_template_string, request, redirect, url_for, Response
import os
from werkzeug.utils import secure_filename
from flask import Flask, request, render_template_string, redirect, url_for
import os
import re
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer3.layout import LAParams, LTTextBox
from pdfminer3.pdfpage import PDFPage
from pdfminer3.pdfinterp import PDFResourceManager
from pdfminer3.pdfinterp import PDFPageInterpreter
from pdfminer3.converter import PDFPageAggregator
from pdfminer3.converter import TextConverter
import io
import pdfminer
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTChar, LTTextBox
import magic
from pdfminer.high_level import extract_text
import subprocess

import fitz  # PyMuPDF
from PIL import Image
import io
import imagehash
from IPython.display import display
import os
import pytesseract
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
import cv2
import base64


app = Flask(__name__)
UPLOAD_FOLDER = './'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def is_pdf(file_path):
    mime = magic.Magic()
    file_type = mime.from_file(file_path)
    return "PDF" in file_type

def extract_title_from_pdf(file_path, num):
    if not is_pdf(file_path):
        return "Uploaded file is not a PDF."

    text = ''
    for page_layout in extract_pages(file_path):
        c = 0
        k = 0
        l = list()
        for element in page_layout:
            if isinstance(element, LTTextBox):
                c += 1
            if isinstance(element, LTTextContainer):
                for text_line in element:
                    try:
                        for character in text_line:
                            if isinstance(character, LTChar):
                                k = character.size
                        l.append(k)
                    except:
                        continue

            if c == num:
                break
        m = max(l) - 2
        c = 0
        k = 0
        l = list()
        for element in page_layout:
            if isinstance(element, LTTextBox):
                c += 1
            if isinstance(element, LTTextContainer):
                for text_line in element:
                    try:
                        for character in text_line:
                            if isinstance(character, LTChar):
                                k = character.size
                        if k >= m:
                            text += text_line.get_text()
                    except:
                        continue

            if c == num:
                break

        title_regex = r'[\d\s]*([\w\s.,-:()\/\[\]]+)[\n]+(?:[\w\s.,-:()\/\[\]]+[\n]+)*'
        match = re.search(title_regex, text, re.MULTILINE)
        if match:
            title = match.group(1).strip()
        else:
            return file_path

        if title:
            title = re.sub(r'(\n|\s{2,})', ' ', title)
            title = title.strip()
        if len(title) == 1:
            return file_path
        return title
    

def display_non_duplicate_images_from_pdf(file_path):
    pdf_document = fitz.open(file_path)
    image_hashes = {}

    for page_number in range(pdf_document.page_count):
        page = pdf_document.load_page(page_number)

        image_list = page.get_images(full=True)
        for img_index, img in enumerate(image_list):
            xref = img[0]
            base_image = pdf_document.extract_image(xref)
            image_data = base_image["image"]
            image = Image.open(io.BytesIO(image_data))
            image_hash = imagehash.phash(image)
            if image_hash in image_hashes:
                continue
            else:
                image_hashes[image_hash] = None
                img_data = io.BytesIO()
                image.save(img_data, format='JPEG')
                img_data.seek(0)
                img_base64 = base64.b64encode(img_data.read()).decode('utf-8')
                yield image

    pdf_document.close()


def generate_image(images):
    for image in images:
        img_io = io.BytesIO()
        image.save(img_io, format='JPEG')
        img_io.seek(0)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + img_io.read() + b'\r\n')


@app.route('/')
def index():
    html_code = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>PDF Processing Options</title>
    </head>
    <body>
        <h1>Upload a PDF File and Select Processing Options</h1>
        <form method="POST" enctype="multipart/form-data" action="/upload">
            <input type="file" name="file" accept=".pdf" required>
            <br><br>
            <input type="checkbox" name="extract_images" value="yes"> Extract Images<br>
            <input type="checkbox" name="extract_title" value="yes"> Extract Title<br>
            <input type="checkbox" name="extract_font_size" value="yes"> Extract Font Size<br>
            <br>
            <input type="submit" value="Upload and Process">
        </form>
    </body>
    </html>
    """
    return render_template_string(html_code)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    
    file = request.files['file']
    
    if file.filename == '':
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        # Check the selected options
        extract_images = 'extract_images' in request.form
        extract_title = 'extract_title' in request.form
        extract_font_size = 'extract_font_size' in request.form
        
        response = f'File {filename} has been uploaded successfully!<br>'
        
        if extract_images:
            images = list(display_non_duplicate_images_from_pdf(os.path.join(app.config['UPLOAD_FOLDER'], filename)))
            if images:
                response += '<h2>Extracted Images</h2>'
                for img in images:
                    response += f'<img src="data:image/jpeg;base64,{img}" alt="Extracted Image"><br><br>'
            else:
                response += '\nNo images found in the PDF.<br>'
        
        if extract_title:
            title = extract_title_from_pdf(os.path.join(app.config['UPLOAD_FOLDER'], filename), num=1)
            response += f'\nTitle: {title}<br>'
        
        if extract_font_size:
            response += 'Font sizes will be extracted.\n'
        
        return response
    else:
        return 'Invalid file format. Please upload a PDF file.<br>'

if __name__ == '__main__':
    app.run(debug=True)
