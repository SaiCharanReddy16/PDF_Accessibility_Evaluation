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

app = Flask(__name__)

# Define the folder where uploaded files will be stored
UPLOAD_FOLDER = './'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# HTML template for the file upload form
upload_template = """
<!doctype html>
<html>
  <head>
    <title>File Upload</title>
  </head>
  <body>
    <h1>File Upload</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file>
      <input type=submit value=Upload>
    </form>
    {% if message %}
    <p>{{ message }}</p>
    {% endif %}
  </body>
</html>
"""


def extract_title_from_pdf(file_path, num):
    try:
        print(file_path)
        text = ''
        for page_layout in extract_pages(file_path):
            print('*' * 10)
            print('*' * 10)
            c = 0
            k = 0
            l = list()
            for element in page_layout:
                if isinstance(element, LTTextBox):
                    print(element)
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
                                
                if c==num:
                    break
            m = max(l) -2
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
                            if k>=m:
                                text += text_line.get_text()
                        except:
                            continue
                                        
                if c==num:
                    break
            
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
    except:
        return file_path

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':

        if 'file' not in request.files:
            return redirect(request.url)

        file = request.files['file']

        if file.filename == '':
            return redirect(request.url)

        
        file.save(f"{app.config['UPLOAD_FOLDER']}/{file.filename}")

        title = extract_title_from_pdf(file.filename, 20)
        message = "Extracted Title : "+title

        return render_template_string(upload_template, message=message)

    return render_template_string(upload_template, message=None)

if __name__ == '__main__':
    app.run(debug=True)
