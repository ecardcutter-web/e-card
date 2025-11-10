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


@app.route('/ayushman-card')
def ayushman_card():
    return render_template('ayushman_crop.html')  # ✅ Corrected template name


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
           
            # ✅ UPDATED: Ayushman Card ratio added to main function
            if card_type == "aadhaar":
                left = int(w * 0.06)
                top = int(h * 0.72)
                card_width = int(w * 0.88)
                card_height = int(card_width / 2.9)
            elif card_type == "jan-aadhaar":
                left = int(w * 0.04)
                top = int(h * 0.54)
                card_width = int(w * 0.92)
                card_height = int(card_width / 3.35)
            elif card_type == "pan":
                left = int(w * 0.05)
                top = int(h * 0.72)
                card_width = int(w * 0.90)
                card_height = int(card_width / 2.59)
            elif card_type == "voter":
                left = int(w * 0.05)
                top = int(h * 0.11)
                card_width = int(w * 0.92)
                card_height = int(card_width / 3.48)
            elif card_type == "ayushman":  # ✅ NEW: Ayushman Card ratio
                left = int(w * 0.04)
                top = int(h * 0.22)
                card_width = int(w * 0.84)
                card_height = int(card_width / 2.55)
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

# ==================== AYUSHMAN CARD UPLOAD ====================

@app.route('/upload-ayushman', methods=['POST'])
def upload_ayushman():
    global cropped_files_info
   
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file selected'})
       
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'})
       
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({'success': False, 'error': 'Please upload a PDF file'})
       
        password = request.form.get('password', '')
       
        file_id = secrets.token_hex(8)
        pdf_filename = f"{file_id}.pdf"
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_filename)
        file.save(pdf_path)
       
        print(f"✂️ Processing Ayushman Card from PDF")
       
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
           
            # High quality for Ayushman card
            dpi = 300
            zoom = dpi / 72
            matrix = fitz.Matrix(zoom, zoom)
           
            pix = page.get_pixmap(matrix=matrix)
            w, h = pix.width, pix.height
            
            # Ayushman Card specific coordinates
            left = int(w * 0.12)
            top = int(h * 0.31)
            card_width = int(w * 0.77)
            card_height = int(card_width / 4.08)  # Standard card ratio
            
            # Ensure boundaries
            left = max(0, left)
            top = max(0, top)
            card_width = min(card_width, w - left)
            card_height = min(card_height, h - top)
            
            print(f"📐 Cropping Ayushman Card at {left},{top} size {card_width}x{card_height}")
            
            # Process image
            img_data = pix.tobytes("ppm")
            img = Image.open(io.BytesIO(img_data))
            cropped_img = img.crop((left, top, left + card_width, top + card_height))
            
            cropped_filename = f"{file_id}_cropped.png"
            cropped_path = os.path.join(app.config['CROPPED_FOLDER'], cropped_filename)
            cropped_img.save(cropped_path, dpi=(dpi, dpi), format='PNG', optimize=True)
            
            print(f"✅ Ayushman Card saved: {cropped_filename}")
            
            pdf_document.close()
            cropped_files_info.append(cropped_filename)
            
            return jsonify({
                'success': True,
                'message': 'Ayushman Card cropped successfully at 300 DPI! File auto-deletes in 5 minutes.',
                'file_id': file_id
            })
            
        except Exception as e:
            print(f"❌ Ayushman Card cropping error: {str(e)}")
            return jsonify({'success': False, 'error': f'Ayushman Card cropping failed: {str(e)}'})
        
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
        'tools': ['Aadhaar Crop', 'PAN Crop', 'Voter ID Crop', 'Janaadhaar Crop', 'Ayushman Card Crop', 'Image Converter'],
        'cropped_files': len(cropped_files_info),
        'converted_files': len(converted_files_info)
    })


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Endpoint not found',
        'available_endpoints': [
            'GET  / - Homepage',
            'GET  /aadhaar-crop - Aadhaar Card Crop Tool',
            'GET  /pan-crop - PAN Card Crop Tool',
            'GET  /voterid-crop - Voter ID Crop Tool',
            'GET  /janaadhaar-crop - Jan Aadhaar Crop Tool',
            'GET  /ayushman-card - Ayushman Card Crop Tool',
            'GET  /image-converter - Image Converter Tool',
            'POST /upload - Upload for E-Card Cutter',
            'POST /upload-ayushman - Upload for Ayushman Card',
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
    print("   • Homepage - /")
    print("   • Aadhaar Card Crop - /aadhaar-crop")
    print("   • PAN Card Crop - /pan-crop")
    print("   • Voter ID Crop - /voterid-crop")
    print("   • Jan Aadhaar Crop - /janaadhaar-crop")
    print("   • Ayushman Card Crop - /ayushman-card")
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
   
    app.run(debug=True, port=5000, host='127.0.0.1')