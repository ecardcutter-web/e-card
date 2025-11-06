from flask import Flask, render_template, request, flash, redirect, url_for, send_file, jsonify
import os
import fitz
import secrets
from datetime import datetime, timedelta
import zipfile
import io
from PIL import Image
import time
import uuid
import json
from file_cleaner import FileCleaner

# ✅ Static folder support
app = Flask(__name__, static_folder='static')
app.secret_key = 'your-secret-key-123'

# Directory setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
CROPPED_FOLDER = os.path.join(BASE_DIR, 'cropped')
CONVERTED_FOLDER = os.path.join(BASE_DIR, 'converted')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CROPPED_FOLDER, exist_ok=True)
os.makedirs(CONVERTED_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['CROPPED_FOLDER'] = CROPPED_FOLDER
app.config['CONVERTED_FOLDER'] = CONVERTED_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# ✅ Initialize File Cleaner
file_cleaner = FileCleaner(
    upload_folder=UPLOAD_FOLDER,
    cropped_folder=CROPPED_FOLDER,
    converted_folder=CONVERTED_FOLDER,
    retention_minutes=5
)

# Store files info
cropped_files_info = []
converted_files_info = []

# ==================== ROUTES ====================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/aadhaar-crop')
def aadhaar_crop():
    return render_template('aadhaar_crop.html')

@app.route('/pan-crop')
def pan_crop():
    return render_template('pan_crop.html')

@app.route('/voterid-crop')
def voterid_crop():
    return render_template('voterid_crop.html')

@app.route('/janaadhaar-crop')
def janaadhaar_crop():
    return render_template('janaadhaar_crop.html')

@app.route('/pdf-converter')
def pdf_converter():
    return render_template('pdf_converter.html')

@app.route('/image-converter')
def image_converter():
    return render_template('image_converter.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/faq')
def faq():
    return render_template('faq.html')

# ==================== E-CARD CUTTER ====================

@app.route('/upload', methods=['POST'])
def upload_file():
    global cropped_files_info
    
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file selected'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'})
        
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({'success': False, 'error': 'Please upload a PDF file'})
        
        card_type = request.form.get('card_type', 'aadhaar')
        password = request.form.get('password', '')
        
        file_id = secrets.token_hex(8)
        pdf_filename = f"{file_id}.pdf"
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_filename)
        file.save(pdf_path)
        
        print(f"✂️ Processing {card_type} card from PDF")
        print(f"🎯 Quality: 300 DPI (Premium)")
        print(f"🕒 Files will auto-delete in 5 minutes")
        
        try:
            if password:
                pdf_document = fitz.open(pdf_path)
                if pdf_document.needs_pass:
                    authenticated = pdf_document.authenticate(password)
                    if not authenticated:
                        return jsonify({'success': False, 'error': 'Invalid PDF password'})
            else:
                pdf_document = fitz.open(pdf_path)
            
            page = pdf_document.load_page(0)
            
            dpi = 300
            zoom = dpi / 72
            matrix = fitz.Matrix(zoom, zoom)
            
            pix = page.get_pixmap(matrix=matrix)
            w, h = pix.width, pix.height
            print(f"📐 Image dimensions: {w} x {h}")
            
            if card_type == "aadhaar":
                left = int(w * 0.06)
                top = int(h * 0.71)
                card_width = int(w * 0.88)
                card_height = int(card_width / 2.9)
            elif card_type == "jan-aadhaar":
                left = int(w * 0.04)
                top = int(h * 0.54)
                card_width = int(w * 0.92)
                card_height = int(card_width / 3.35)
            elif card_type == "pan":
                left = int(w * 0.15)
                top = int(h * 0.15)
                card_width = int(w * 0.70)
                card_height = int(card_width / 1.58)
            elif card_type == "voter":
                left = int(w * 0.10)
                top = int(h * 0.25)
                card_width = int(w * 0.80)
                card_height = int(card_width / 1.42)
            else:
                left = int(w * 0.10)
                top = int(h * 0.20)
                card_width = int(w * 0.80)
                card_height = int(card_width / 1.62)
            
            left = max(0, left)
            top = max(0, top)
            card_width = min(card_width, w - left)
            card_height = min(card_height, h - top)
            
            print(f"✂️ Cropping area: {left},{top} to {left+card_width},{top+card_height}")
            
            img_data = pix.tobytes("ppm")
            img = Image.open(io.BytesIO(img_data))
            cropped_img = img.crop((left, top, left + card_width, top + card_height))
            
            cropped_filename = f"{file_id}_cropped.png"
            cropped_path = os.path.join(app.config['CROPPED_FOLDER'], cropped_filename)
            cropped_img.save(cropped_path, dpi=(dpi, dpi), format='PNG', optimize=True)
            
            print(f"✅ Cropped image saved: {cropped_filename} ({cropped_img.size[0]}x{cropped_img.size[1]})")
            
            pdf_document.close()
            cropped_files_info.append(cropped_filename)
            
            return jsonify({
                'success': True,
                'message': f'{card_type.title()} card cropped successfully at 300 DPI! File auto-deletes in 5 minutes.',
                'file_id': file_id,
                'card_type': card_type
            })
            
        except Exception as e:
            print(f"❌ Card cropping error: {str(e)}")
            return jsonify({'success': False, 'error': f'Card cropping failed: {str(e)}'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Upload failed: {str(e)}'})

# ==================== IMAGE CONVERTER ====================

@app.route('/convert-image', methods=['POST'])
def convert_image():
    global converted_files_info
    
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file selected'})
        
        file = request.files['file']
        format_type = request.form.get('format', 'jpg')
        quality = int(request.form.get('quality', 80))
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'})
        
        # Check if file is an image
        if not file.content_type.startswith('image/'):
            return jsonify({'success': False, 'error': 'Please upload a valid image file'})
        
        file_id = secrets.token_hex(8)
        original_filename = f"{file_id}_original"
        original_path = os.path.join(app.config['UPLOAD_FOLDER'], original_filename)
        file.save(original_path)
        
        print(f"🔄 Converting image to {format_type.upper()} (Quality: {quality}%)")
        print(f"📁 Original file: {file.filename}")
        
        try:
            # Open the image
            with Image.open(original_path) as img:
                # Convert to RGB if necessary (for JPEG)
                if format_type.lower() in ['jpg', 'jpeg']:
                    if img.mode in ('RGBA', 'P'):
                        img = img.convert('RGB')
                
                # Create output buffer
                output_buffer = io.BytesIO()
                
                # Save with quality settings for supported formats
                format_lower = format_type.lower()
                
                if format_lower in ['jpg', 'jpeg']:
                    quality_param = max(10, quality)
                    img.save(output_buffer, 'JPEG', quality=quality_param, optimize=True)
                    mime_type = 'image/jpeg'
                    ext = 'jpg'
                
                elif format_lower == 'png':
                    # PNG doesn't support quality parameter, but we can optimize
                    img.save(output_buffer, 'PNG', optimize=True)
                    mime_type = 'image/png'
                    ext = 'png'
                
                elif format_lower == 'webp':
                    quality_param = max(10, quality)
                    img.save(output_buffer, 'WEBP', quality=quality_param)
                    mime_type = 'image/webp'
                    ext = 'webp'
                
                elif format_lower == 'gif':
                    img.save(output_buffer, 'GIF', optimize=True)
                    mime_type = 'image/gif'
                    ext = 'gif'
                
                elif format_lower == 'bmp':
                    img.save(output_buffer, 'BMP')
                    mime_type = 'image/bmp'
                    ext = 'bmp'
                
                elif format_lower == 'tiff':
                    quality_param = max(10, quality)
                    img.save(output_buffer, 'TIFF', compression='tiff_deflate', quality=quality_param)
                    mime_type = 'image/tiff'
                    ext = 'tiff'
                
                elif format_lower == 'ico':
                    # For ICO, we need to ensure proper size
                    if img.size[0] > 256 or img.size[1] > 256:
                        img.thumbnail((256, 256), Image.Resampling.LANCZOS)
                    img.save(output_buffer, 'ICO')
                    mime_type = 'image/x-icon'
                    ext = 'ico'
                
                elif format_lower == 'pdf':
                    # Convert image to PDF
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    img.save(output_buffer, 'PDF', resolution=100.0, quality=quality)
                    mime_type = 'application/pdf'
                    ext = 'pdf'
                
                else:
                    # For other formats, save with default settings
                    img.save(output_buffer, format_type.upper())
                    mime_type = f'image/{format_type}'
                    ext = format_type
                
                output_buffer.seek(0)
                file_data = output_buffer.getvalue()
            
            # Clean up original file
            if os.path.exists(original_path):
                os.remove(original_path)
            
            # Create response
            original_name = os.path.splitext(file.filename)[0]
            download_name = f"{original_name}.{ext}"
            
            converted_filename = f"{file_id}.{ext}"
            converted_path = os.path.join(app.config['CONVERTED_FOLDER'], converted_filename)
            
            with open(converted_path, 'wb') as f:
                f.write(file_data)
            
            converted_files_info.append(converted_filename)
            
            return send_file(
                io.BytesIO(file_data),
                as_attachment=True,
                download_name=download_name,
                mimetype=mime_type
            )
            
        except Exception as e:
            print(f"❌ Image conversion error: {str(e)}")
            # Clean up original file if it exists
            if os.path.exists(original_path):
                os.remove(original_path)
            return jsonify({'success': False, 'error': f'Image conversion failed: {str(e)}'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Upload failed: {str(e)}'})

# ==================== PDF CONVERTER ENHANCED FUNCTIONS ====================

def convert_text_to_csv(text):
    """Convert extracted text to structured CSV"""
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    csv_lines = ["Line Number,Content"]
    for i, line in enumerate(lines, 1):
        if line:
            escaped_line = line.replace('"', '""')
            if ',' in line or '"' in line:
                escaped_line = f'"{escaped_line}"'
            csv_lines.append(f'{i},{escaped_line}')
    
    return '\n'.join(csv_lines)

def convert_text_to_json(text):
    """Convert extracted text to JSON format"""
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    json_data = {
        "metadata": {
            "pages": len([p for p in text.split('\n\n') if p.strip()]),
            "total_lines": len(lines),
            "conversion_date": datetime.now().isoformat()
        },
        "content": lines
    }
    
    return json.dumps(json_data, indent=2, ensure_ascii=False)

def convert_text_to_xml(text, title):
    """Convert extracted text to XML format"""
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    # Build XML using list join method (no backslash issues)
    xml_lines = []
    xml_lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    xml_lines.append('<document>')
    xml_lines.append('    <metadata>')
    xml_lines.append('        <title>' + title + '</title>')
    xml_lines.append('        <pages>' + str(len([p for p in text.split('\n\n') if p.strip()])) + '</pages>')
    xml_lines.append('        <lines>' + str(len(lines)) + '</lines>')
    xml_lines.append('        <conversion_date>' + datetime.now().isoformat() + '</conversion_date>')
    xml_lines.append('    </metadata>')
    xml_lines.append('    <content>')
    
    for i, line in enumerate(lines, 1):
        escaped_line = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        xml_lines.append('        <line number="' + str(i) + '">' + escaped_line + '</line>')
    
    xml_lines.append('    </content>')
    xml_lines.append('</document>')
    
    # Join with newlines
    return '\n'.join(xml_lines)

def convert_text_to_html(text, title):
    """Convert extracted text to HTML format"""
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    html_content = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
        .content {{ max-width: 800px; margin: 0 auto; }}
        .line {{ margin-bottom: 10px; padding: 5px; border-left: 3px solid #007bff; }}
        .metadata {{ background: #f5f5f5; padding: 20px; border-radius: 5px; margin-bottom: 30px; }}
    </style>
</head>
<body>
    <div class="content">
        <div class="metadata">
            <h1>{title}</h1>
            <p>Pages: {len([p for p in text.split('\n\n') if p.strip()])} | Lines: {len(lines)}</p>
            <p>Converted on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        </div>
        <div class="text-content">
'''
    
    for i, line in enumerate(lines, 1):
        escaped_line = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        html_content += f'            <div class="line"><strong>{i}.</strong> {escaped_line}</div>\n'
    
    html_content += '''        </div>
    </div>
</body>
</html>'''
    return html_content

def create_document_content(text, format_type, title):
    """Create enhanced document content with proper structure"""
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    if format_type in ['doc', 'docx']:
        doc_content = f"""TITLE: {title}
CONVERSION DATE: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
PAGES: {len([p for p in text.split('\n\n') if p.strip()])}
TOTAL LINES: {len(lines)}

DOCUMENT CONTENT:
{'=' * 60}

"""
        for i, line in enumerate(lines, 1):
            if line:
                doc_content += f"{i}. {line}\n"
        
        return doc_content
    
    elif format_type == 'rtf':
        rtf_content = f"""{{\\rtf1\\ansi\\deff0
{{\\fonttbl {{\\f0 Times New Roman;}}}}
\\f0\\fs24

{{\\b {title}}}\\\\
\\par
Conversion Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\\\\
Pages: {len([p for p in text.split('\n\n') if p.strip()])}\\\\
Lines: {len(lines)}\\\\
\\par
\\par
{{\\b DOCUMENT CONTENT:}}\\\\
\\par
{'=' * 60}
\\par
\\par
"""
        for i, line in enumerate(lines, 1):
            if line:
                rtf_content += f"{i}. {line}\\\\\\par\n"
        
        rtf_content += "}"
        return rtf_content
    
    elif format_type == 'odt':
        odt_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<document>
  <title>{title}</title>
  <metadata>
    <creator>PDF Converter</creator>
    <date>{datetime.now().isoformat()}</date>
  </metadata>
  <content>
"""
        for i, line in enumerate(lines, 1):
            if line:
                odt_content += f"    <line number='{i}'>{line}</line>\n"
        
        odt_content += "  </content>\n</document>"
        return odt_content
    
    else:
        return f"{title}\n\n{text}"

def create_svg_from_page(page, quality):
    width, height = page.rect.width, page.rect.height
    scale = quality / 100.0
    
    svg_content = f'''<svg width="{width * scale}" height="{height * scale}" xmlns="http://www.w3.org/2000/svg">
    <rect width="100%" height="100%" fill="white"/>
    <text x="50" y="50" font-family="Arial" font-size="12" fill="black">
        PDF to SVG Conversion
    </text>
</svg>'''
    return svg_content

def convert_text_to_excel(text, format_type):
    csv_content = convert_text_to_csv(text)
    return csv_content.encode('utf-8')

def create_presentation_content(text, format_type, title):
    pages = [p.strip() for p in text.split('\n\n') if p.strip()]
    
    ppt_content = f"""PRESENTATION: {title}
SLIDES: {len(pages)}
CONVERSION DATE: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

SLIDE CONTENT:
{'=' * 50}

"""
    
    for i, page in enumerate(pages, 1):
        ppt_content += f"\nSLIDE {i}:\n{page}\n{'-' * 40}\n"
    
    return ppt_content

def create_ebook_content(text, format_type, title):
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    ebook_content = f"""TITLE: {title}
AUTHOR: PDF Converter
DATE: {datetime.now().strftime("%Y-%m-%d")}

CONTENT:
{'=' * 50}

"""
    for i, line in enumerate(lines, 1):
        ebook_content += f"{i}. {line}\n"
    
    return ebook_content

# ==================== ENHANCED PDF CONVERTER ROUTE ====================

@app.route('/convert-pdf', methods=['POST'])
def convert_pdf():
    global converted_files_info
    
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file selected'})
        
        file = request.files['file']
        format_type = request.form.get('format', 'jpg')
        quality = int(request.form.get('quality', 100))
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'})
        
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({'success': False, 'error': 'Please upload a PDF file'})
        
        file_id = secrets.token_hex(8)
        pdf_filename = f"{file_id}.pdf"
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_filename)
        file.save(pdf_path)
        
        print(f"🔄 Converting PDF to {format_type.upper()} (Quality: {quality}%)")
        print(f"📁 Original file: {file.filename}")
        
        try:
            pdf_document = fitz.open(pdf_path)
            
            # Image formats conversion
            if format_type.lower() in ['jpg', 'jpeg', 'png', 'webp', 'tiff', 'bmp', 'gif', 'svg']:
                images = []
                for page_num in range(len(pdf_document)):
                    page = pdf_document[page_num]
                    
                    base_dpi = 300
                    quality_dpi = int(base_dpi * (quality / 100))
                    zoom = quality_dpi / 72
                    matrix = fitz.Matrix(zoom, zoom)
                    
                    pix = page.get_pixmap(matrix=matrix)
                    img_data = pix.tobytes("ppm")
                    
                    img = Image.open(io.BytesIO(img_data))
                    img_io = io.BytesIO()
                    format_lower = format_type.lower()
                    
                    if format_lower in ['jpg', 'jpeg']:
                        img = img.convert('RGB')
                        quality_param = max(10, quality)
                        img.save(img_io, 'JPEG', quality=quality_param, optimize=True)
                        mime_type = 'image/jpeg'
                        ext = 'jpg'
                    elif format_lower == 'png':
                        img.save(img_io, 'PNG', optimize=True)
                        mime_type = 'image/png'
                        ext = 'png'
                    elif format_lower == 'webp':
                        quality_param = max(10, quality)
                        img.save(img_io, 'WEBP', quality=quality_param)
                        mime_type = 'image/webp'
                        ext = 'webp'
                    elif format_lower == 'tiff':
                        img.save(img_io, 'TIFF', compression='tiff_deflate')
                        mime_type = 'image/tiff'
                        ext = 'tiff'
                    elif format_lower == 'bmp':
                        img.save(img_io, 'BMP')
                        mime_type = 'image/bmp'
                        ext = 'bmp'
                    elif format_lower == 'gif':
                        img = img.convert('P', palette=Image.ADAPTIVE)
                        img.save(img_io, 'GIF', optimize=True)
                        mime_type = 'image/gif'
                        ext = 'gif'
                    elif format_lower == 'svg':
                        svg_content = create_svg_from_page(page, quality)
                        img_io.write(svg_content.encode('utf-8'))
                        mime_type = 'image/svg+xml'
                        ext = 'svg'
                    
                    img_io.seek(0)
                    images.append((img_io, mime_type, ext))
                
                pdf_document.close()
                
                if len(images) == 1:
                    img_io, mime_type, ext = images[0]
                    original_name = os.path.splitext(file.filename)[0]
                    download_name = f"{original_name}.{ext}"
                    
                    converted_filename = f"{file_id}.{ext}"
                    converted_path = os.path.join(app.config['CONVERTED_FOLDER'], converted_filename)
                    with open(converted_path, 'wb') as f:
                        f.write(img_io.getvalue())
                    
                    converted_files_info.append(converted_filename)
                    
                    return send_file(
                        img_io,
                        as_attachment=True,
                        download_name=download_name,
                        mimetype=mime_type
                    )
                else:
                    zip_io = io.BytesIO()
                    with zipfile.ZipFile(zip_io, 'w') as zip_file:
                        for i, (img_io, mime_type, ext) in enumerate(images):
                            zip_file.writestr(f'page_{i+1}.{ext}', img_io.getvalue())
                    zip_io.seek(0)
                    
                    zip_filename = f"{file_id}.zip"
                    zip_path = os.path.join(app.config['CONVERTED_FOLDER'], zip_filename)
                    with open(zip_path, 'wb') as f:
                        f.write(zip_io.getvalue())
                    
                    converted_files_info.append(zip_filename)
                    
                    original_name = os.path.splitext(file.filename)[0]
                    return send_file(
                        zip_io,
                        as_attachment=True,
                        download_name=f'{original_name}_pages.zip',
                        mimetype='application/zip'
                    )
            
            else:
                # Text-based and document formats
                text_content = ""
                for page_num in range(len(pdf_document)):
                    page = pdf_document[page_num]
                    text_content += page.get_text() + "\n\n"
                
                pdf_document.close()
                
                output_io = io.BytesIO()
                original_name = os.path.splitext(file.filename)[0]
                format_lower = format_type.lower()
                
                if format_lower == 'txt':
                    output_io.write(text_content.encode('utf-8'))
                    mime_type = 'text/plain'
                    download_name = f"{original_name}.txt"
                    ext = 'txt'
                    
                elif format_lower == 'csv':
                    csv_content = convert_text_to_csv(text_content)
                    output_io.write(csv_content.encode('utf-8'))
                    mime_type = 'text/csv'
                    download_name = f"{original_name}.csv"
                    ext = 'csv'
                    
                elif format_lower == 'json':
                    json_content = convert_text_to_json(text_content)
                    output_io.write(json_content.encode('utf-8'))
                    mime_type = 'application/json'
                    download_name = f"{original_name}.json"
                    ext = 'json'
                    
                elif format_lower in ['xml', 'html']:
                    if format_lower == 'xml':
                        xml_content = convert_text_to_xml(text_content, original_name)
                        output_io.write(xml_content.encode('utf-8'))
                        mime_type = 'application/xml'
                        download_name = f"{original_name}.xml"
                        ext = 'xml'
                    else:
                        html_content = convert_text_to_html(text_content, original_name)
                        output_io.write(html_content.encode('utf-8'))
                        mime_type = 'text/html'
                        download_name = f"{original_name}.html"
                        ext = 'html'
                        
                elif format_lower in ['doc', 'docx', 'odt', 'rtf']:
                    doc_content = create_document_content(text_content, format_lower, original_name)
                    output_io.write(doc_content.encode('utf-8'))
                    
                    if format_lower == 'docx':
                        mime_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                    elif format_lower == 'doc':
                        mime_type = 'application/msword'
                    elif format_lower == 'odt':
                        mime_type = 'application/vnd.oasis.opendocument.text'
                    else:
                        mime_type = 'application/rtf'
                    
                    download_name = f"{original_name}.{format_lower}"
                    ext = format_lower
                    
                elif format_lower in ['xls', 'xlsx']:
                    excel_content = convert_text_to_excel(text_content, format_lower)
                    output_io.write(excel_content)
                    
                    if format_lower == 'xlsx':
                        mime_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                    else:
                        mime_type = 'application/vnd.ms-excel'
                    
                    download_name = f"{original_name}.{format_lower}"
                    ext = format_lower
                    
                elif format_lower in ['ppt', 'pptx']:
                    ppt_content = create_presentation_content(text_content, format_lower, original_name)
                    output_io.write(ppt_content.encode('utf-8'))
                    
                    if format_lower == 'pptx':
                        mime_type = 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
                    else:
                        mime_type = 'application/vnd.ms-powerpoint'
                    
                    download_name = f"{original_name}.{format_lower}"
                    ext = format_lower
                    
                elif format_lower in ['epub', 'mobi']:
                    ebook_content = create_ebook_content(text_content, format_lower, original_name)
                    output_io.write(ebook_content.encode('utf-8'))
                    
                    if format_lower == 'epub':
                        mime_type = 'application/epub+zip'
                    else:
                        mime_type = 'application/x-mobipocket-ebook'
                    
                    download_name = f"{original_name}.{format_lower}"
                    ext = format_lower
                    
                else:
                    output_io.write(text_content.encode('utf-8'))
                    mime_type = 'text/plain'
                    download_name = f"{original_name}.{format_type}"
                    ext = format_type
                
                output_io.seek(0)
                
                converted_filename = f"{file_id}.{ext}"
                converted_path = os.path.join(app.config['CONVERTED_FOLDER'], converted_filename)
                with open(converted_path, 'wb') as f:
                    f.write(output_io.getvalue())
                
                converted_files_info.append(converted_filename)
                
                return send_file(
                    output_io,
                    as_attachment=True,
                    download_name=download_name,
                    mimetype=mime_type
                )
                
        except Exception as e:
            print(f"❌ PDF conversion error: {str(e)}")
            return jsonify({'success': False, 'error': f'PDF conversion failed: {str(e)}'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Upload failed: {str(e)}'})

# ==================== COMMON ENDPOINTS ====================

@app.route('/download/<filename>')
def download_file(filename):
    try:
        file_path = os.path.join(app.config['CROPPED_FOLDER'], filename)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True, download_name=filename)
        
        file_path = os.path.join(app.config['CONVERTED_FOLDER'], filename)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True, download_name=filename)
        
        return jsonify({"error": "File not found"}), 404
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/preview/<filename>')
def serve_image(filename):
    try:
        file_path = os.path.join(app.config['CROPPED_FOLDER'], filename)
        if os.path.exists(file_path):
            return send_file(file_path)
        
        return jsonify({"error": "Preview file not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/clear-files', methods=['POST'])
def clear_files():
    global cropped_files_info, converted_files_info
    
    try:
        for filename in cropped_files_info:
            file_path = os.path.join(app.config['CROPPED_FOLDER'], filename)
            if os.path.exists(file_path):
                os.remove(file_path)
        
        for filename in converted_files_info:
            file_path = os.path.join(app.config['CONVERTED_FOLDER'], filename)
            if os.path.exists(file_path):
                os.remove(file_path)
        
        for filename in os.listdir(app.config['UPLOAD_FOLDER']):
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if os.path.exists(file_path):
                os.remove(file_path)
        
        cropped_files_info = []
        converted_files_info = []
        
        return jsonify({'success': True, 'message': 'All files cleared successfully'})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'tools': ['E-Card Cutter', 'PDF Converter', 'Image Converter'],
        'cropped_files': len(cropped_files_info),
        'converted_files': len(converted_files_info)
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Endpoint not found', 
        'available_endpoints': [
            'GET  / - E-Card Cutter',
            'GET  /aadhaar-crop - Aadhaar Card Crop Tool',
            'GET  /pan-crop - PAN Card Crop Tool',
            'GET  /voterid-crop - Voter ID Crop Tool',
            'GET  /janaadhaar-crop - Jan Aadhaar Crop Tool',
            'GET  /pdf-converter - PDF Converter Tool',
            'GET  /image-converter - Image Converter Tool',
            'POST /upload - Upload for E-Card Cutter',
            'POST /convert-pdf - Convert PDF files',
            'POST /convert-image - Convert Image files',
            'GET  /download/<filename> - Download file',
            'GET  /preview/<filename> - Preview image',
            'POST /clear-files - Clear all files',
            'GET  /health - Health check',
            'GET  /about - About Us',
            'GET  /privacy - Privacy Policy',
            'GET  /terms - Terms of Service',
            'GET  /contact - Contact Us',
            'GET  /faq - FAQ'
        ]
    }), 404

if __name__ == '__main__':
    print("🚀 Starting E-Card Cutter...")
    print(f"📁 Upload folder: {UPLOAD_FOLDER}")
    print(f"📁 Cropped folder: {CROPPED_FOLDER}")
    print(f"📁 Converted folder: {CONVERTED_FOLDER}")
    print("\n🛠️ Available Tools:")
    print("   • E-Card Cutter - /")
    print("   • Aadhaar Card Crop - /aadhaar-crop")
    print("   • PAN Card Crop - /pan-crop")
    print("   • Voter ID Crop - /voterid-crop")
    print("   • Jan Aadhaar Crop - /janaadhaar-crop")
    print("   • PDF Converter - /pdf-converter")
    print("   • Image Converter - /image-converter")
    print("\n📄 Additional Pages:")
    print("   • About Us - /about")
    print("   • Privacy Policy - /privacy") 
    print("   • Terms of Service - /terms")
    print("   • Contact Us - /contact")
    print("   • FAQ - /faq")
    
    file_cleaner.start_auto_cleanup()
    print(f"🕒 Auto-delete enabled: Files will be deleted after 5 minutes")
    
    print("\n🌐 Server running on: http://localhost:5000")
    
    app.run(debug=False, port=5000, host='0.0.0.0')