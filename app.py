from flask import Flask, render_template, request, flash, redirect, url_for, send_file, jsonify
import os
import fitz
import secrets
from datetime import datetime, timedelta
import zipfile
import io
from PIL import Image, ImageDraw, ImageFont
import time
import uuid
import json
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, mm
from reportlab.lib.utils import ImageReader
import tempfile

# Static folder support
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

# Store files info
cropped_files_info = []
converted_files_info = []

# File Cleaner Class
class FileCleaner:
    def __init__(self, upload_folder, cropped_folder, converted_folder, retention_minutes=5):
        self.upload_folder = upload_folder
        self.cropped_folder = cropped_folder
        self.converted_folder = converted_folder
        self.retention_minutes = retention_minutes
    
    def cleanup_old_files(self):
        try:
            current_time = time.time()
            folders = [self.upload_folder, self.cropped_folder, self.converted_folder]
            deleted_count = 0
            
            for folder in folders:
                if os.path.exists(folder):
                    for filename in os.listdir(folder):
                        file_path = os.path.join(folder, filename)
                        if os.path.isfile(file_path):
                            # Check if file is older than retention period
                            file_age = current_time - os.path.getctime(file_path)
                            if file_age > (self.retention_minutes * 60):
                                os.remove(file_path)
                                deleted_count += 1
                                print(f"Deleted old file: {filename}")
            
            print(f"Auto-cleanup: Deleted {deleted_count} old files")
            return deleted_count
            
        except Exception as e:
            print(f"Cleanup error: {e}")
            return 0
    
    def start_auto_cleanup(self):
        def cleanup_loop():
            while True:
                self.cleanup_old_files()
                time.sleep(60)  # Check every minute
        
        import threading
        cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
        cleanup_thread.start()
        print("Auto-cleanup started")

# Initialize File Cleaner
file_cleaner = FileCleaner(
    upload_folder=UPLOAD_FOLDER,
    cropped_folder=CROPPED_FOLDER,
    converted_folder=CONVERTED_FOLDER,
    retention_minutes=5
)

# ==================== CARD CROPPER FUNCTIONS ====================

def process_pdf_front_back(pdf_path, output_dir, card_type='aadhaar', pdf_password=None):
    """Extract Card Front & Back sides automatically with 300 DPI clarity - TIGHT CROPPING"""
    
    dpi = 300
    
    print(f"Processing PDF for Front & Back: {pdf_path}")
    print(f"Card type: {card_type}")
    
    try:
        # PDF open karein
        doc = fitz.open(pdf_path)
        
        # Password check agar PDF protected hai
        if doc.needs_pass:
            if pdf_password:
                if not doc.authenticate(pdf_password):
                    doc.close()
                    return {'success': False, 'error': "Invalid PDF password"}
            else:
                doc.close()
                return {'success': False, 'error': "PDF is password protected but no password provided."}

        # First page load karein
        page = doc.load_page(0)
        
        # High quality
        matrix = fitz.Matrix(dpi/72, dpi/72)
        pix = page.get_pixmap(matrix=matrix)
        w, h = pix.width, pix.height
        
        print(f"PDF dimensions: {w} x {h}")

        # PERFECT TIGHT CROP COORDINATES FOR ALL CARDS - Aadhaar pattern
        if card_type == "aadhaar":
            # Aadhaar card actual dimensions (excluding black border)
            card_width = int(w * 0.42)
            card_height = int(card_width / 1.60)
            
            total_cards_width = (card_width * 2) + (w * 0.010)
            start_x = (w - total_cards_width) / 2
            
            # Front Side (Left side - Personal details with photo)
            front_left = int(start_x + w * 0.009)
            front_top = int(h * 0.729)
            front_width = card_width - int(w * 0.01)
            front_height = card_height - int(h * 0.01)
            
            # Back Side (Right side - Address and QR Code)
            back_left = int(start_x + card_width + (w * 0.016))
            back_top = int(h * 0.729)
            back_width = card_width - int(w * 0.01)
            back_height = card_height - int(h * 0.01)

        elif card_type == "jan-aadhaar":
            # Jan-Aadhaar - Same pattern as Aadhaar
            card_width = int(w * 0.44)
            card_height = int(card_width / 1.61)
            
            total_cards_width = (card_width * 2) + (w * 0.010)
            start_x = (w - total_cards_width) / 2
            
            front_left = int(start_x + w * 0.009)
            front_top = int(h * 0.55)
            front_width = card_width - int(w * 0.01)
            front_height = card_height - int(h * 0.02)
            
            back_left = int(start_x + card_width + (w * 0.015))
            back_top = int(h * 0.55)
            back_width = card_width - int(w * 0.01)
            back_height = card_height - int(h * 0.02)
            
        elif card_type == "pan":
            # PAN Card - Same pattern as Aadhaar
            card_width = int(w * 0.42)
            card_height = int(card_width / 1.62)
            
            total_cards_width = (card_width * 2) + (w * 0.025)
            start_x = (w - total_cards_width) / 2
            
            front_left = int(start_x + w * 0.007)
            front_top = int(h * 0.79)
            front_width = card_width - int(w * 0.03)
            front_height = card_height - int(h * 0.01)
            
            back_left = int(start_x + card_width + (w * 0.05))
            back_top = int(h * 0.79)
            back_width = card_width - int(w * 0.03)
            back_height = card_height - int(h * 0.01)
            
        elif card_type == "voter":
            # Voter ID - Same pattern as Aadhaar
            card_width = int(w * 0.44)
            card_height = int(card_width / 1.67)
            
            total_cards_width = (card_width * 2) + (w * 0.025)
            start_x = (w - total_cards_width) / 2
            
            front_left = int(start_x + w * 0.007)
            front_top = int(h * 0.12)
            front_width = card_width - int(w * 0.04)
            front_height = card_height - int(h * 0.01)
            
            back_left = int(start_x + card_width + (w * 0.08))
            back_top = int(h * 0.12)
            back_width = card_width - int(w * 0.05)
            back_height = card_height - int(h * 0.01)
            
        elif card_type == "ayushman":
            # Ayushman Card - Same pattern as Aadhaar
            card_width = int(w * 0.41)
            card_height = int(card_width / 1.70)
            
            total_cards_width = (card_width * 2) + (w * 0.015)
            start_x = (w - total_cards_width) / 2
            
            front_left = int(start_x + w * 0.05)
            front_top = int(h * 0.32)
            front_width = card_width - int(w * 0.06)
            front_height = card_height - int(h * 0.18)
            
            back_left = int(start_x + card_width + (w * 0.05))
            back_top = int(h * 0.32)
            back_width = card_width - int(w * 0.07)
            back_height = card_height - int(h * 0.18)
            
        elif card_type == "labour":
            # Labour Card - Same pattern as Aadhaar
            card_width = int(w * 0.41)
            card_height = int(card_width / 1.05)
            
            total_cards_width = (card_width * 2) + (w * 0.020)
            start_x = (w - total_cards_width) / 2
            
            front_left = int(start_x + w * 0.007)
            front_top = int(h * 0.07)
            front_width = card_width - int(w * 0.01)
            front_height = card_height - int(h * 0.02)
            
            back_left = int(start_x + card_width + (w * 0.023))
            back_top = int(h * 0.10)
            back_width = card_width - int(w * 0.02)
            back_height = card_height - int(h * 0.04)
            
        else:
            # Default - Same pattern as Aadhaar for any other card
            card_width = int(w * 0.42)
            card_height = int(card_width / 1.59)
            
            total_cards_width = (card_width * 2) + (w * 0.008)
            start_x = (w - total_cards_width) / 2
            
            front_left = int(start_x + w * 0.005)
            front_top = int(h * 0.729)
            front_width = card_width - int(w * 0.01)
            front_height = card_height - int(h * 0.01)
            
            back_left = int(start_x + card_width + (w * 0.013))
            back_top = int(h * 0.729)
            back_width = card_width - int(w * 0.01)
            back_height = card_height - int(h * 0.01)

        print(f"FRONT Coordinates: left={front_left}, top={front_top}, width={front_width}, height={front_height}")
        print(f"BACK Coordinates: left={back_left}, top={back_top}, width={back_width}, height={back_height}")
        print(f"Card Size: {card_width} x {card_height} pixels")
        print(f"Tight Crop: Only card content (excluding black border)")

        # Process images
        img_data = pix.tobytes("ppm")
        img = Image.open(io.BytesIO(img_data))
        
        # Crop front and back with TIGHT boundaries
        front_img = img.crop((front_left, front_top, front_left + front_width, front_top + front_height))
        back_img = img.crop((back_left, back_top, back_left + back_width, back_top + back_height))
        
        # Optional: Add slight padding for better appearance (2px white border)
        padding = 2
        front_final = Image.new('RGB', (front_width + padding*2, front_height + padding*2), 'white')
        front_final.paste(front_img, (padding, padding))
        
        back_final = Image.new('RGB', (back_width + padding*2, back_height + padding*2), 'white')
        back_final.paste(back_img, (padding, padding))
        
        # Save both images
        file_id = str(uuid.uuid4())[:8]
        front_filename = f"{file_id}_front.png"
        back_filename = f"{file_id}_back.png"
        
        front_path = os.path.join(output_dir, front_filename)
        back_path = os.path.join(output_dir, back_filename)
        
        front_final.save(front_path, dpi=(dpi, dpi), format='PNG', optimize=True)
        back_final.save(back_path, dpi=(dpi, dpi), format='PNG', optimize=True)
        
        print(f"Front saved: {front_filename} ({front_final.size[0]}x{front_final.size[1]})")
        print(f"Back saved: {back_filename} ({back_final.size[0]}x{back_final.size[1]})")
        print(f"Crop Result: Black border excluded, only card content captured")
        
        doc.close()
        
        return {
            'success': True,
            'front_file': front_filename,
            'back_file': back_filename,
            'file_id': file_id,
            'message': 'Front & Back sides extracted with tight cropping (no black border)!'
        }
        
    except Exception as e:
        print(f"Error in process_pdf_front_back: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return {'success': False, 'error': str(e)}

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
    return render_template('ayushman_crop.html')

@app.route('/labour-card')
def labour_card():
    return render_template('labour_crop.html')

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

# ==================== AUTO FRONT-BACK CROPPING FOR ALL CARDS ====================

@app.route('/upload-card-both', methods=['POST'])
def upload_card_both():
    """Main endpoint for ALL card types front-back cropping"""
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
        
        print(f"Auto cropping {card_type.upper()} Front & Back")
        
        # Use the auto front-back cropper for ALL card types
        result = process_pdf_front_back(
            pdf_path=pdf_path,
            output_dir=app.config['CROPPED_FOLDER'],
            card_type=card_type,
            pdf_password=password
        )
        
        if result['success']:
            cropped_files_info.extend([result['front_file'], result['back_file']])
            
            card_names = {
                'aadhaar': 'Aadhaar',
                'pan': 'PAN', 
                'voter': 'Voter ID',
                'jan-aadhaar': 'Jan-Aadhaar',
                'ayushman': 'Ayushman Card',
                'labour': 'Labour Card'
            }
            
            card_name = card_names.get(card_type, 'Card')
            
            return jsonify({
                'success': True,
                'message': f'{card_name} Front & Back cropped successfully!',
                'file_id': result['file_id'],
                'front_file': result['front_file'],
                'back_file': result['back_file'],
                'card_type': card_type
            })
        else:
            return jsonify({'success': False, 'error': result['error']})
        
    except Exception as e:
        print(f"Auto crop error: {str(e)}")
        return jsonify({'success': False, 'error': f'Processing failed: {str(e)}'})

# ==================== BACKWARD COMPATIBILITY ROUTES ====================

@app.route('/upload-aadhaar-both', methods=['POST'])
def upload_aadhaar_both():
    """Backward compatibility for Aadhaar"""
    return upload_card_both()

@app.route('/upload-janaadhaar-both', methods=['POST'])
def upload_janaadhaar_both():
    """Backward compatibility for Jan-Aadhaar"""
    return upload_card_both()

@app.route('/upload-pan-both', methods=['POST'])
def upload_pan_both():
    """Backward compatibility for PAN"""
    return upload_card_both()

@app.route('/upload-voterid-both', methods=['POST'])
def upload_voterid_both():
    """Voter ID ke liye specific route"""
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
        
        print(f"Auto cropping VOTER ID Front & Back")
        
        # Use the auto front-back cropper for Voter ID
        result = process_pdf_front_back(
            pdf_path=pdf_path,
            output_dir=app.config['CROPPED_FOLDER'],
            card_type='voter',
            pdf_password=password
        )
        
        if result['success']:
            cropped_files_info.extend([result['front_file'], result['back_file']])
            
            return jsonify({
                'success': True,
                'message': 'Voter ID Card Front & Back cropped successfully!',
                'file_id': result['file_id'],
                'front_file': result['front_file'],
                'back_file': result['back_file'],
                'card_type': 'voter'
            })
        else:
            return jsonify({'success': False, 'error': result['error']})
        
    except Exception as e:
        print(f"Voter ID crop error: {str(e)}")
        return jsonify({'success': False, 'error': f'Processing failed: {str(e)}'})

@app.route('/upload-ayushman-both', methods=['POST'])
def upload_ayushman_both():
    """Backward compatibility for Ayushman Card"""
    return upload_card_both()

@app.route('/upload-labour-both', methods=['POST'])
def upload_labour_both():
    """Labour Card ke liye specific route"""
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
        
        print(f"Auto cropping LABOUR CARD Front & Back")
        
        # Use the auto front-back cropper for Labour Card
        result = process_pdf_front_back(
            pdf_path=pdf_path,
            output_dir=app.config['CROPPED_FOLDER'],
            card_type='labour',
            pdf_password=password
        )
        
        if result['success']:
            cropped_files_info.extend([result['front_file'], result['back_file']])
            
            return jsonify({
                'success': True,
                'message': 'Labour Card Front & Back cropped successfully!',
                'file_id': result['file_id'],
                'front_file': result['front_file'],
                'back_file': result['back_file'],
                'card_type': 'labour'
            })
        else:
            return jsonify({'success': False, 'error': result['error']})
        
    except Exception as e:
        print(f"Labour Card crop error: {str(e)}")
        return jsonify({'success': False, 'error': f'Processing failed: {str(e)}'})

# ==================== PVC CARD CONVERSION FOR ALL CARDS ====================

@app.route('/convert-to-pvc-card', methods=['POST'])
def convert_to_pvc_card():
    """PVC conversion for ALL card types"""
    try:
        data = request.json
        front_file = data.get('front_file')
        back_file = data.get('back_file')
        card_type = data.get('card_type', 'aadhaar')
        
        if not front_file or not back_file:
            return jsonify({'success': False, 'error': 'Front and back files are required'})
        
        front_path = os.path.join(app.config['CROPPED_FOLDER'], front_file)
        back_path = os.path.join(app.config['CROPPED_FOLDER'], back_file)
        
        if not os.path.exists(front_path) or not os.path.exists(back_path):
            return jsonify({'success': False, 'error': 'Files not found'})
        
        # PVC card dimensions in pixels (300 DPI) - Exact 8.6cm x 5.4cm
        pvc_width_mm = 86  # 8.6 cm
        pvc_height_mm = 54  # 5.4 cm
        pvc_width = int(pvc_width_mm * 300 / 25.4)  # Convert mm to pixels at 300 DPI
        pvc_height = int(pvc_height_mm * 300 / 25.4)
        
        print(f"PVC Target Size: {pvc_width_mm}mm x {pvc_height_mm}mm")
        print(f"PVC Pixel Size: {pvc_width} x {pvc_height} pixels (300 DPI)")
        print(f"Card Type: {card_type}")
        
        # Process front image - NO BORDER
        with Image.open(front_path) as front_img:
            # Resize to exact PVC dimensions without border
            pvc_front = front_img.resize((pvc_width, pvc_height), Image.Resampling.LANCZOS)
        
        # Process back image - NO BORDER  
        with Image.open(back_path) as back_img:
            # Resize to exact PVC dimensions without border
            pvc_back = back_img.resize((pvc_width, pvc_height), Image.Resampling.LANCZOS)
        
        # Save PVC images without border
        file_id = str(uuid.uuid4())[:8]
        pvc_front_filename = f"{file_id}_pvc_front.png"
        pvc_back_filename = f"{file_id}_pvc_back.png"
        
        pvc_front_path = os.path.join(app.config['CROPPED_FOLDER'], pvc_front_filename)
        pvc_back_path = os.path.join(app.config['CROPPED_FOLDER'], pvc_back_filename)
        
        pvc_front.save(pvc_front_path, dpi=(300, 300), format='PNG', optimize=True)
        pvc_back.save(pvc_back_path, dpi=(300, 300), format='PNG', optimize=True)
        
        cropped_files_info.extend([pvc_front_filename, pvc_back_filename])
        
        card_names = {
            'aadhaar': 'Aadhaar',
            'pan': 'PAN',
            'voter': 'Voter ID', 
            'jan-aadhaar': 'Jan-Aadhaar',
            'ayushman': 'Ayushman Card',
            'labour': 'Labour Card'
        }
        
        card_name = card_names.get(card_type, 'Card')
        
        return jsonify({
            'success': True,
            'pvc_front_file': pvc_front_filename,
            'pvc_back_file': pvc_back_filename,
            'message': f'{card_name} converted to PVC size (8.6cm × 5.4cm) successfully!',
            'pvc_size': f"{pvc_width_mm}mm x {pvc_height_mm}mm",
            'card_type': card_type
        })
        
    except Exception as e:
        print(f"PVC conversion error: {str(e)}")
        return jsonify({'success': False, 'error': f'PVC conversion failed: {str(e)}'})

# ==================== BACKWARD COMPATIBILITY PVC ROUTES ====================

@app.route('/convert-to-pvc-aadhaar', methods=['POST'])
def convert_to_pvc_aadhaar():
    """Backward compatibility for Aadhaar PVC"""
    return convert_to_pvc_card()

@app.route('/convert-to-pvc-voterid', methods=['POST'])
def convert_to_pvc_voterid():
    """Voter ID ke liye PVC conversion"""
    try:
        data = request.json
        front_file = data.get('front_file')
        back_file = data.get('back_file')
        
        if not front_file or not back_file:
            return jsonify({'success': False, 'error': 'Front and back files are required'})
        
        front_path = os.path.join(app.config['CROPPED_FOLDER'], front_file)
        back_path = os.path.join(app.config['CROPPED_FOLDER'], back_file)
        
        if not os.path.exists(front_path) or not os.path.exists(back_path):
            return jsonify({'success': False, 'error': 'Files not found'})
        
        # PVC card dimensions in pixels (300 DPI) - Exact 8.6cm x 5.4cm
        pvc_width_mm = 86  # 8.6 cm
        pvc_height_mm = 54  # 5.4 cm
        pvc_width = int(pvc_width_mm * 300 / 25.4)  # Convert mm to pixels at 300 DPI
        pvc_height = int(pvc_height_mm * 300 / 25.4)
        
        print(f"Voter ID PVC Target Size: {pvc_width_mm}mm x {pvc_height_mm}mm")
        print(f"Voter ID PVC Pixel Size: {pvc_width} x {pvc_height} pixels (300 DPI)")
        
        # Process front image - NO BORDER
        with Image.open(front_path) as front_img:
            # Resize to exact PVC dimensions without border
            pvc_front = front_img.resize((pvc_width, pvc_height), Image.Resampling.LANCZOS)
        
        # Process back image - NO BORDER  
        with Image.open(back_path) as back_img:
            # Resize to exact PVC dimensions without border
            pvc_back = back_img.resize((pvc_width, pvc_height), Image.Resampling.LANCZOS)
        
        # Save PVC images without border
        file_id = str(uuid.uuid4())[:8]
        pvc_front_filename = f"{file_id}_pvc_front.png"
        pvc_back_filename = f"{file_id}_pvc_back.png"
        
        pvc_front_path = os.path.join(app.config['CROPPED_FOLDER'], pvc_front_filename)
        pvc_back_path = os.path.join(app.config['CROPPED_FOLDER'], pvc_back_filename)
        
        pvc_front.save(pvc_front_path, dpi=(300, 300), format='PNG', optimize=True)
        pvc_back.save(pvc_back_path, dpi=(300, 300), format='PNG', optimize=True)
        
        cropped_files_info.extend([pvc_front_filename, pvc_back_filename])
        
        return jsonify({
            'success': True,
            'pvc_front_file': pvc_front_filename,
            'pvc_back_file': pvc_back_filename,
            'message': 'Voter ID converted to PVC size (8.6cm × 5.4cm) successfully!',
            'pvc_size': f"{pvc_width_mm}mm x {pvc_height_mm}mm",
            'card_type': 'voter'
        })
        
    except Exception as e:
        print(f"Voter ID PVC conversion error: {str(e)}")
        return jsonify({'success': False, 'error': f'PVC conversion failed: {str(e)}'})

@app.route('/convert-to-pvc-labour', methods=['POST'])
def convert_to_pvc_labour():
    """Labour Card ke liye PVC conversion"""
    try:
        data = request.json
        front_file = data.get('front_file')
        back_file = data.get('back_file')
        
        if not front_file or not back_file:
            return jsonify({'success': False, 'error': 'Front and back files are required'})
        
        front_path = os.path.join(app.config['CROPPED_FOLDER'], front_file)
        back_path = os.path.join(app.config['CROPPED_FOLDER'], back_file)
        
        if not os.path.exists(front_path) or not os.path.exists(back_path):
            return jsonify({'success': False, 'error': 'Files not found'})
        
        # PVC card dimensions in pixels (300 DPI) - Exact 8.6cm x 5.4cm
        pvc_width_mm = 86  # 8.6 cm
        pvc_height_mm = 54  # 5.4 cm
        pvc_width = int(pvc_width_mm * 300 / 25.4)  # Convert mm to pixels at 300 DPI
        pvc_height = int(pvc_height_mm * 300 / 25.4)
        
        print(f"Labour Card PVC Target Size: {pvc_width_mm}mm x {pvc_height_mm}mm")
        print(f"Labour Card PVC Pixel Size: {pvc_width} x {pvc_height} pixels (300 DPI)")
        
        # Process front image - NO BORDER
        with Image.open(front_path) as front_img:
            # Resize to exact PVC dimensions without border
            pvc_front = front_img.resize((pvc_width, pvc_height), Image.Resampling.LANCZOS)
        
        # Process back image - NO BORDER  
        with Image.open(back_path) as back_img:
            # Resize to exact PVC dimensions without border
            pvc_back = back_img.resize((pvc_width, pvc_height), Image.Resampling.LANCZOS)
        
        # Save PVC images without border
        file_id = str(uuid.uuid4())[:8]
        pvc_front_filename = f"{file_id}_pvc_front.png"
        pvc_back_filename = f"{file_id}_pvc_back.png"
        
        pvc_front_path = os.path.join(app.config['CROPPED_FOLDER'], pvc_front_filename)
        pvc_back_path = os.path.join(app.config['CROPPED_FOLDER'], pvc_back_filename)
        
        pvc_front.save(pvc_front_path, dpi=(300, 300), format='PNG', optimize=True)
        pvc_back.save(pvc_back_path, dpi=(300, 300), format='PNG', optimize=True)
        
        cropped_files_info.extend([pvc_front_filename, pvc_back_filename])
        
        return jsonify({
            'success': True,
            'pvc_front_file': pvc_front_filename,
            'pvc_back_file': pvc_back_filename,
            'message': 'Labour Card converted to PVC size (8.6cm × 5.4cm) successfully!',
            'pvc_size': f"{pvc_width_mm}mm x {pvc_height_mm}mm",
            'card_type': 'labour'
        })
        
    except Exception as e:
        print(f"Labour Card PVC conversion error: {str(e)}")
        return jsonify({'success': False, 'error': f'PVC conversion failed: {str(e)}'})

# ==================== BOTH SIDES DOWNLOAD (PNG/JPG) ====================

@app.route('/download-both-sides', methods=['POST'])
def download_both_sides():
    """Download both front and back sides as COMBINED IMAGE (not ZIP)"""
    try:
        data = request.json
        front_file = data.get('front_file')
        back_file = data.get('back_file')
        download_type = data.get('type', 'combined')  # combined or separate
        card_type = data.get('card_type', 'aadhaar')
        
        if not front_file or not back_file:
            return jsonify({'success': False, 'error': 'Both files are required'})
        
        front_path = os.path.join(app.config['CROPPED_FOLDER'], front_file)
        back_path = os.path.join(app.config['CROPPED_FOLDER'], back_file)
        
        if not os.path.exists(front_path) or not os.path.exists(back_path):
            return jsonify({'success': False, 'error': 'Files not found'})
        
        card_names = {
            'aadhaar': 'Aadhaar Card',
            'pan': 'PAN Card',
            'voter': 'Voter ID Card',
            'jan-aadhaar': 'Jan-Aadhaar Card', 
            'ayushman': 'Ayushman Card',
            'labour': 'Labour Card'
        }
        
        card_name = card_names.get(card_type, 'Card')
        
        if download_type == 'combined':
            # Create combined image with both cards side by side
            with Image.open(front_path) as front_img:
                with Image.open(back_path) as back_img:
                    # Create new image with both cards side by side
                    combined_width = front_img.width + back_img.width + 20  # 20px gap
                    combined_height = max(front_img.height, back_img.height) + 40  # Extra space for labels
                    
                    combined_img = Image.new('RGB', (combined_width, combined_height), 'white')
                    
                    # Paste front card
                    combined_img.paste(front_img, (0, 20))
                    
                    # Paste back card
                    combined_img.paste(back_img, (front_img.width + 20, 20))
                    
                    # Add labels
                    try:
                        draw = ImageDraw.Draw(combined_img)
                        try:
                            font = ImageFont.truetype("arial.ttf", 20)
                        except:
                            font = ImageFont.load_default()
                        
                        # Front label
                        front_text = "Front Side"
                        front_bbox = draw.textbbox((0, 0), front_text, font=font)
                        front_text_width = front_bbox[2] - front_bbox[0]
                        front_x = (front_img.width - front_text_width) // 2
                        draw.text((front_x, 0), front_text, fill='black', font=font)
                        
                        # Back label
                        back_text = "Back Side"
                        back_bbox = draw.textbbox((0, 0), back_text, font=font)
                        back_text_width = back_bbox[2] - back_bbox[0]
                        back_x = front_img.width + 20 + (back_img.width - back_text_width) // 2
                        draw.text((back_x, 0), back_text, fill='black', font=font)
                        
                    except Exception as e:
                        print(f"Label rendering error: {e}")
            
            # Save combined image
            file_id = str(uuid.uuid4())[:8]
            combined_filename = f"{file_id}_both_sides.png"
            combined_path = os.path.join(app.config['CROPPED_FOLDER'], combined_filename)
            
            combined_img.save(combined_path, dpi=(300, 300), format='PNG', optimize=True)
            cropped_files_info.append(combined_filename)
            
            return jsonify({
                'success': True,
                'download_file': combined_filename,
                'message': f'{card_name} both sides combined into single image!'
            })
        
        else:
            # For separate download, create a simple combined image
            with Image.open(front_path) as front_img:
                with Image.open(back_path) as back_img:
                    combined_width = front_img.width + back_img.width + 20
                    combined_height = max(front_img.height, back_img.height)
                    
                    combined_img = Image.new('RGB', (combined_width, combined_height), 'white')
                    combined_img.paste(front_img, (0, 0))
                    combined_img.paste(back_img, (front_img.width + 20, 0))
            
            file_id = str(uuid.uuid4())[:8]
            combined_filename = f"{file_id}_both_sides.jpg"
            combined_path = os.path.join(app.config['CROPPED_FOLDER'], combined_filename)
            
            combined_img.save(combined_path, dpi=(300, 300), format='JPEG', quality=95, optimize=True)
            cropped_files_info.append(combined_filename)
            
            return jsonify({
                'success': True,
                'download_file': combined_filename,
                'message': f'{card_name} both sides downloaded as JPG!'
            })
        
    except Exception as e:
        print(f"Combined image creation error: {str(e)}")
        return jsonify({'success': False, 'error': f'Download failed: {str(e)}'})

# ==================== PRINTING FUNCTIONS ====================

@app.route('/print-pvc-card', methods=['POST'])
def print_pvc_card():
    try:
        data = request.json
        print_type = data.get('type', 'both')  # front, back, both
        pvc_front_file = data.get('pvc_front_file')
        pvc_back_file = data.get('pvc_back_file')
        card_type = data.get('card_type', 'aadhaar')
        
        if not pvc_front_file or not pvc_back_file:
            return jsonify({'success': False, 'error': 'PVC files are required'})
        
        pvc_front_path = os.path.join(app.config['CROPPED_FOLDER'], pvc_front_file)
        pvc_back_path = os.path.join(app.config['CROPPED_FOLDER'], pvc_back_file)
        
        if not os.path.exists(pvc_front_path) or not os.path.exists(pvc_back_path):
            return jsonify({'success': False, 'error': 'PVC files not found'})
        
        card_names = {
            'aadhaar': 'Aadhaar Card',
            'pan': 'PAN Card',
            'voter': 'Voter ID Card',
            'jan-aadhaar': 'Jan-Aadhaar Card',
            'ayushman': 'Ayushman Card',
            'labour': 'Labour Card'
        }
        
        card_name = card_names.get(card_type, 'Card')
        
        # Create PDF based on print type
        file_id = str(uuid.uuid4())[:8]
        
        if print_type == 'front':
            pdf_filename = f"{file_id}_print_front.pdf"
            pdf_path = os.path.join(app.config['CROPPED_FOLDER'], pdf_filename)
            create_print_pdf(pvc_front_path, f"{card_name} - Front Side", pdf_path)
            
        elif print_type == 'back':
            pdf_filename = f"{file_id}_print_back.pdf"
            pdf_path = os.path.join(app.config['CROPPED_FOLDER'], pdf_filename)
            create_print_pdf(pvc_back_path, f"{card_name} - Back Side", pdf_path)
            
        else:  # both
            pdf_filename = f"{file_id}_print_both.pdf"
            pdf_path = os.path.join(app.config['CROPPED_FOLDER'], pdf_filename)
            create_print_pdf_both(pvc_front_path, pvc_back_path, card_name, pdf_path)
        
        cropped_files_info.append(pdf_filename)
        
        return jsonify({
            'success': True,
            'pdf_file': pdf_filename,
            'message': f'PDF created successfully for {print_type} side(s)!'
        })
        
    except Exception as e:
        print(f"PDF creation error: {str(e)}")
        return jsonify({'success': False, 'error': f'PDF creation failed: {str(e)}'})

# ==================== BACKWARD COMPATIBILITY PRINT ROUTES ====================

@app.route('/print-pvc-aadhaar', methods=['POST'])
def print_pvc_aadhaar():
    """Backward compatibility for Aadhaar printing"""
    return print_pvc_card()

@app.route('/print-pvc-voterid', methods=['POST'])
def print_pvc_voterid():
    """Voter ID ke liye printing"""
    try:
        data = request.json
        print_type = data.get('type', 'both')  # front, back, both
        pvc_front_file = data.get('pvc_front_file')
        pvc_back_file = data.get('pvc_back_file')
        
        if not pvc_front_file or not pvc_back_file:
            return jsonify({'success': False, 'error': 'PVC files are required'})
        
        pvc_front_path = os.path.join(app.config['CROPPED_FOLDER'], pvc_front_file)
        pvc_back_path = os.path.join(app.config['CROPPED_FOLDER'], pvc_back_file)
        
        if not os.path.exists(pvc_front_path) or not os.path.exists(pvc_back_path):
            return jsonify({'success': False, 'error': 'PVC files not found'})
        
        # Create PDF based on print type
        file_id = str(uuid.uuid4())[:8]
        
        if print_type == 'front':
            pdf_filename = f"{file_id}_print_front.pdf"
            pdf_path = os.path.join(app.config['CROPPED_FOLDER'], pdf_filename)
            create_print_pdf(pvc_front_path, "Voter ID Card - Front Side", pdf_path)
            
        elif print_type == 'back':
            pdf_filename = f"{file_id}_print_back.pdf"
            pdf_path = os.path.join(app.config['CROPPED_FOLDER'], pdf_filename)
            create_print_pdf(pvc_back_path, "Voter ID Card - Back Side", pdf_path)
            
        else:  # both
            pdf_filename = f"{file_id}_print_both.pdf"
            pdf_path = os.path.join(app.config['CROPPED_FOLDER'], pdf_filename)
            create_print_pdf_both(pvc_front_path, pvc_back_path, "Voter ID Card", pdf_path)
        
        cropped_files_info.append(pdf_filename)
        
        return jsonify({
            'success': True,
            'pdf_file': pdf_filename,
            'message': f'PDF created successfully for {print_type} side(s)!'
        })
        
    except Exception as e:
        print(f"Voter ID PDF creation error: {str(e)}")
        return jsonify({'success': False, 'error': f'PDF creation failed: {str(e)}'})

@app.route('/print-pvc-labour', methods=['POST'])
def print_pvc_labour():
    """Labour Card ke liye printing"""
    try:
        data = request.json
        print_type = data.get('type', 'both')  # front, back, both
        pvc_front_file = data.get('pvc_front_file')
        pvc_back_file = data.get('pvc_back_file')
        
        if not pvc_front_file or not pvc_back_file:
            return jsonify({'success': False, 'error': 'PVC files are required'})
        
        pvc_front_path = os.path.join(app.config['CROPPED_FOLDER'], pvc_front_file)
        pvc_back_path = os.path.join(app.config['CROPPED_FOLDER'], pvc_back_file)
        
        if not os.path.exists(pvc_front_path) or not os.path.exists(pvc_back_path):
            return jsonify({'success': False, 'error': 'PVC files not found'})
        
        # Create PDF based on print type
        file_id = str(uuid.uuid4())[:8]
        
        if print_type == 'front':
            pdf_filename = f"{file_id}_print_front.pdf"
            pdf_path = os.path.join(app.config['CROPPED_FOLDER'], pdf_filename)
            create_print_pdf(pvc_front_path, "Labour Card - Front Side", pdf_path)
            
        elif print_type == 'back':
            pdf_filename = f"{file_id}_print_back.pdf"
            pdf_path = os.path.join(app.config['CROPPED_FOLDER'], pdf_filename)
            create_print_pdf(pvc_back_path, "Labour Card - Back Side", pdf_path)
            
        else:  # both
            pdf_filename = f"{file_id}_print_both.pdf"
            pdf_path = os.path.join(app.config['CROPPED_FOLDER'], pdf_filename)
            create_print_pdf_both(pvc_front_path, pvc_back_path, "Labour Card", pdf_path)
        
        cropped_files_info.append(pdf_filename)
        
        return jsonify({
            'success': True,
            'pdf_file': pdf_filename,
            'message': f'PDF created successfully for {print_type} side(s)!'
        })
        
    except Exception as e:
        print(f"Labour Card PDF creation error: {str(e)}")
        return jsonify({'success': False, 'error': f'PDF creation failed: {str(e)}'})

def create_print_pdf(image_path, title, output_path):
    """Create PDF for direct printing"""
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4
    
    # Add image centered and larger for printing
    img = ImageReader(image_path)
    
    # Calculate size to fit page with margins
    img_width = 500
    img_height = 320
    
    x = (width - img_width) / 2
    y = (height - img_height) / 2
    
    c.drawImage(img, x, y, width=img_width, height=img_height, preserveAspectRatio=True)
    
    # Add title at bottom
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width/2, 50, title)
    
    c.showPage()
    c.save()

def create_print_pdf_both(front_path, back_path, card_name, output_path):
    """Create PDF with both sides for printing"""
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4
    
    # Front side
    front_img = ImageReader(front_path)
    front_width = 400
    front_height = 250
    
    front_x = (width - front_width) / 2
    front_y = height - front_height - 100
    
    c.drawImage(front_img, front_x, front_y, width=front_width, height=front_height, preserveAspectRatio=True)
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width/2, front_y - 30, f"Front Side - {card_name}")
    
    # Back side
    back_img = ImageReader(back_path)
    back_width = 400
    back_height = 250
    
    back_x = (width - back_width) / 2
    back_y = front_y - back_height - 80
    
    c.drawImage(back_img, back_x, back_y, width=back_width, height=back_height, preserveAspectRatio=True)
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width/2, back_y - 30, f"Back Side - {card_name}")
    
    c.showPage()
    c.save()

# ==================== IMAGE CONVERTER ROUTES ====================

@app.route('/convert-image', methods=['POST'])
def convert_image():
    """Image format conversion endpoint - ALL FORMATS SUPPORTED"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file selected'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'})
        
        # Get conversion parameters
        output_format = request.form.get('format', 'png').lower()
        quality = int(request.form.get('quality', 95))
        
        # SUPPORTED FORMATS - All formats that PIL supports
        supported_formats = {
            'jpg': 'JPEG', 'jpeg': 'JPEG', 'png': 'PNG', 'gif': 'GIF', 
            'bmp': 'BMP', 'tiff': 'TIFF', 'webp': 'WEBP', 'ico': 'ICO',
            'pdf': 'PDF'
        }
        
        # Validate format
        if output_format not in supported_formats:
            return jsonify({'success': False, 'error': f'Format {output_format.upper()} not supported. Use: {", ".join(supported_formats.keys())}'})
        
        # Generate unique filename
        file_id = secrets.token_hex(8)
        original_filename = file.filename
        file_extension = original_filename.rsplit('.', 1)[-1].lower()
        
        # Save uploaded file temporarily
        temp_filename = f"{file_id}_temp.{file_extension}"
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], temp_filename)
        file.save(temp_path)
        
        # Process image conversion
        with Image.open(temp_path) as img:
            # Convert to RGB if necessary (for JPG/PDF)
            if output_format in ['jpg', 'jpeg', 'pdf'] and img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            output_filename = f"{file_id}_converted.{output_format}"
            output_path = os.path.join(app.config['CONVERTED_FOLDER'], output_filename)
            
            # Save with format-specific options
            save_options = {
                'format': supported_formats[output_format],
                'optimize': True
            }
            
            # Add quality for lossy formats
            if output_format in ['jpg', 'jpeg', 'webp']:
                save_options['quality'] = quality
            elif output_format == 'png':
                save_options['compress_level'] = 9 - int((quality / 100) * 9)
            
            # Special handling for PDF
            if output_format == 'pdf':
                img.save(output_path, "PDF", resolution=100.0)
            else:
                img.save(output_path, **save_options)
            
            converted_files_info.append(output_filename)
            
            # Get file size for response
            file_size = os.path.getsize(output_path)
            
            return jsonify({
                'success': True,
                'message': f'Image converted to {output_format.upper()} successfully!',
                'converted_file': output_filename,
                'format': output_format,
                'file_id': file_id,
                'file_size': file_size
            })
            
    except Exception as e:
        print(f"Image conversion error: {str(e)}")
        return jsonify({'success': False, 'error': f'Conversion failed: {str(e)}'})

@app.route('/bulk-convert', methods=['POST'])
def bulk_convert():
    """Bulk image conversion"""
    try:
        if 'files' not in request.files:
            return jsonify({'success': False, 'error': 'No files selected'})
        
        files = request.files.getlist('files')
        output_format = request.form.get('format', 'png').lower()
        quality = int(request.form.get('quality', 95))
        
        if not files or files[0].filename == '':
            return jsonify({'success': False, 'error': 'No files selected'})
        
        # SUPPORTED FORMATS
        supported_formats = {
            'jpg': 'JPEG', 'jpeg': 'JPEG', 'png': 'PNG', 'gif': 'GIF', 
            'bmp': 'BMP', 'tiff': 'TIFF', 'webp': 'WEBP', 'ico': 'ICO',
            'pdf': 'PDF'
        }
        
        if output_format not in supported_formats:
            return jsonify({'success': False, 'error': f'Format {output_format.upper()} not supported'})
        
        converted_files = []
        
        for file in files:
            if file.filename:
                file_id = secrets.token_hex(8)
                original_filename = file.filename
                file_extension = original_filename.rsplit('.', 1)[-1].lower()
                
                # Save temporary file
                temp_filename = f"{file_id}_temp.{file_extension}"
                temp_path = os.path.join(app.config['UPLOAD_FOLDER'], temp_filename)
                file.save(temp_path)
                
                # Convert image
                with Image.open(temp_path) as img:
                    if output_format in ['jpg', 'jpeg', 'pdf'] and img.mode in ('RGBA', 'P'):
                        img = img.convert('RGB')
                    
                    output_filename = f"{file_id}_{original_filename.rsplit('.', 1)[0]}.{output_format}"
                    output_path = os.path.join(app.config['CONVERTED_FOLDER'], output_filename)
                    
                    # Save with format-specific options
                    save_options = {
                        'format': supported_formats[output_format],
                        'optimize': True
                    }
                    
                    if output_format in ['jpg', 'jpeg', 'webp']:
                        save_options['quality'] = quality
                    elif output_format == 'png':
                        save_options['compress_level'] = 9 - int((quality / 100) * 9)
                    
                    if output_format == 'pdf':
                        img.save(output_path, "PDF", resolution=100.0)
                    else:
                        img.save(output_path, **save_options)
                    
                    converted_files.append(output_filename)
                    converted_files_info.append(output_filename)
        
        # Create ZIP if multiple files
        if len(converted_files) > 1:
            zip_filename = f"bulk_converted_{secrets.token_hex(8)}.zip"
            zip_path = os.path.join(app.config['CONVERTED_FOLDER'], zip_filename)
            
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for converted_file in converted_files:
                    file_path = os.path.join(app.config['CONVERTED_FOLDER'], converted_file)
                    zipf.write(file_path, converted_file)
            
            converted_files_info.append(zip_filename)
            
            return jsonify({
                'success': True,
                'message': f'{len(converted_files)} files converted to {output_format.upper()} and zipped!',
                'zip_file': zip_filename,
                'converted_count': len(converted_files),
                'format': output_format
            })
        else:
            return jsonify({
                'success': True,
                'message': f'Image converted to {output_format.upper()} successfully!',
                'converted_file': converted_files[0],
                'format': output_format
            })
            
    except Exception as e:
        print(f"Bulk conversion error: {str(e)}")
        return jsonify({'success': False, 'error': f'Bulk conversion failed: {str(e)}'})

# ==================== FILE DOWNLOAD & PREVIEW ====================

@app.route('/download/<filename>')
def download_file(filename):
    try:
        # Check in all possible folders
        folders = [app.config['UPLOAD_FOLDER'], app.config['CROPPED_FOLDER'], app.config['CONVERTED_FOLDER']]
        
        for folder in folders:
            file_path = os.path.join(folder, filename)
            if os.path.exists(file_path):
                return send_file(file_path, as_attachment=True)
        
        return jsonify({'success': False, 'error': 'File not found'}), 404
        
    except Exception as e:
        print(f"Download error: {str(e)}")
        return jsonify({'success': False, 'error': f'Download failed: {str(e)}'}), 500

@app.route('/preview/<filename>')
def serve_image(filename):
    try:
        # Check in converted folder first for image converter files
        file_path = os.path.join(app.config['CONVERTED_FOLDER'], filename)
        
        if not os.path.exists(file_path):
            folders = [app.config['UPLOAD_FOLDER'], app.config['CROPPED_FOLDER']]
            for folder in folders:
                file_path = os.path.join(folder, filename)
                if os.path.exists(file_path):
                    break
        
        if os.path.exists(file_path):
            return send_file(file_path)
        else:
            return jsonify({'success': False, 'error': 'Image not found'}), 404
            
    except Exception as e:
        print(f"Preview error: {str(e)}")
        return jsonify({'success': False, 'error': f'Preview failed: {str(e)}'}), 500

# ==================== OTHER ROUTES ====================

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file selected'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'})
    
    file_id = secrets.token_hex(8)
    filename = f"{file_id}_{file.filename}"
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    
    return jsonify({
        'success': True,
        'message': 'File uploaded successfully',
        'file_id': file_id,
        'filename': filename
    })

@app.route('/clear-files', methods=['POST'])
def clear_files():
    try:
        folders = [app.config['UPLOAD_FOLDER'], app.config['CROPPED_FOLDER'], app.config['CONVERTED_FOLDER']]
        
        deleted_count = 0
        for folder in folders:
            if os.path.exists(folder):
                for filename in os.listdir(folder):
                    file_path = os.path.join(folder, filename)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        deleted_count += 1
        
        cropped_files_info.clear()
        converted_files_info.clear()
        
        return jsonify({
            'success': True,
            'message': f'Cleared {deleted_count} files',
            'deleted_count': deleted_count
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Clear failed: {str(e)}'})

@app.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'upload_folder': len(os.listdir(app.config['UPLOAD_FOLDER'])) if os.path.exists(app.config['UPLOAD_FOLDER']) else 0,
        'cropped_folder': len(os.listdir(app.config['CROPPED_FOLDER'])) if os.path.exists(app.config['CROPPED_FOLDER']) else 0,
        'converted_folder': len(os.listdir(app.config['CONVERTED_FOLDER'])) if os.path.exists(app.config['CONVERTED_FOLDER']) else 0
    })

if __name__ == '__main__':
    print("Starting Universal PVC Card Maker...")
    print(f"Upload folder: {UPLOAD_FOLDER}")
    print(f"Cropped folder: {CROPPED_FOLDER}")
    print(f"Converted folder: {CONVERTED_FOLDER}")
    
    print("\nFeatures:")
    print("   • Auto Front & Back cropping for ALL cards (Aadhaar, PAN, Voter ID, Jan-Aadhaar, Ayushman, Labour)")
    print("   • Consistent tight cropping pattern - no black borders")
    print("   • PVC Card conversion (8.6cm x 5.4cm) - NO BORDERS")
    print("   • Both sides download as combined PNG/JPG")
    print("   • Direct print functionality for all cards")
    print("   • Image Converter (JPG, PNG, GIF, BMP, TIFF, WEBP, ICO, PDF) with bulk conversion")
    print("   • Auto file cleanup (5 minutes)")
    print("   • Backward compatibility with old routes")
    
    # Start auto cleanup
    file_cleaner.start_auto_cleanup()
    print(f"Auto-delete enabled: Files will be deleted after 5 minutes")
    
    print("\nServer running on: http://localhost:5000")
    app.run(debug=True, port=5000, host='127.0.0.1')