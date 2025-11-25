from flask import Flask, render_template, request, flash, redirect, url_for, send_file, jsonify
import os
import fitz
import secrets
from datetime import datetime, timedelta
import zipfile
import io
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import time
import uuid
import json
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, mm
from reportlab.lib.utils import ImageReader
import tempfile
import cv2
import numpy as np
from rembg import remove
import base64

# Static folder support
app = Flask(__name__, static_folder='static')
app.secret_key = 'your-secret-key-123'

# Directory setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
CROPPED_FOLDER = os.path.join(BASE_DIR, 'cropped')
CONVERTED_FOLDER = os.path.join(BASE_DIR, 'converted')
PASSPORT_FOLDER = os.path.join(BASE_DIR, 'passport_photos')
RESUME_FOLDER = os.path.join(BASE_DIR, 'resumes')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CROPPED_FOLDER, exist_ok=True)
os.makedirs(CONVERTED_FOLDER, exist_ok=True)
os.makedirs(PASSPORT_FOLDER, exist_ok=True)
os.makedirs(RESUME_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['CROPPED_FOLDER'] = CROPPED_FOLDER
app.config['CONVERTED_FOLDER'] = CONVERTED_FOLDER
app.config['PASSPORT_FOLDER'] = PASSPORT_FOLDER
app.config['RESUME_FOLDER'] = RESUME_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Store files info
cropped_files_info = []
converted_files_info = []
passport_files_info = []
resume_files_info = []

# File Cleaner Class
class FileCleaner:
    def __init__(self, upload_folder, cropped_folder, converted_folder, passport_folder, resume_folder, retention_minutes=5):
        self.upload_folder = upload_folder
        self.cropped_folder = cropped_folder
        self.converted_folder = converted_folder
        self.passport_folder = passport_folder
        self.resume_folder = resume_folder
        self.retention_minutes = retention_minutes
    
    def cleanup_old_files(self):
        try:
            current_time = time.time()
            folders = [self.upload_folder, self.cropped_folder, self.converted_folder, self.passport_folder, self.resume_folder]
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
    passport_folder=PASSPORT_FOLDER,
    resume_folder=RESUME_FOLDER,
    retention_minutes=5
)

# ==================== RESUME BUILDER ROUTES - COMPLETELY FIXED VERSION ====================

@app.route('/resume-builder')
def resume_builder():
    return render_template('resume_builder.html')

@app.route('/save-resume', methods=['POST'])
def save_resume():
    """Save resume data and generate PDF - COMPLETELY FIXED VERSION"""
    try:
        # Get form data from request
        resume_data = {
            'personal_info': {
                'name': request.form.get('fullName', 'Your Name'),
                'title': request.form.get('jobTitle', 'Job Title'),
                'email': request.form.get('email', ''),
                'phone': request.form.get('phone', ''),
                'address': request.form.get('address', '')
            },
            'summary': request.form.get('careerObjective', ''),
            'profile': request.form.get('personalProfile', ''),
            'education': request.form.get('education', ''),
            'experience': request.form.get('experience', ''),
            'skills': request.form.get('skills', ''),
            'signature_name': request.form.get('signatureName', ''),
            'date': request.form.get('date', ''),
            'place': request.form.get('place', '')
        }

        # Get template and photo settings
        template = request.form.get('template', '1')
        include_photo = request.form.get('include_photo', 'false') == 'true'
        
        # Handle photo data
        photo_data = None
        if 'photo' in request.files:
            photo_file = request.files['photo']
            if photo_file and photo_file.filename != '':
                photo_data = base64.b64encode(photo_file.read()).decode('utf-8')

        # Generate unique filename
        file_id = secrets.token_hex(8)
        pdf_filename = f"{file_id}_resume.pdf"
        pdf_path = os.path.join(app.config['RESUME_FOLDER'], pdf_filename)
        
        # Create PDF resume using the FIXED backend function
        create_resume_pdf_fixed(resume_data, template, include_photo, photo_data, pdf_path)
        
        resume_files_info.append(pdf_filename)
        
        return jsonify({
            'success': True,
            'message': 'Resume created successfully!',
            'pdf_file': pdf_filename,
            'download_url': f'/download-resume/{pdf_filename}'
        })
        
    except Exception as e:
        print(f"Resume creation error: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': f'Resume creation failed: {str(e)}'})

def create_resume_pdf_fixed(resume_data, template, include_photo, photo_data, output_path):
    """Fixed PDF creation function with PROPER CONTACT INFORMATION LINE BREAKS"""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from reportlab.lib.utils import ImageReader
        import base64
        from io import BytesIO
        
        # Create PDF with canvas
        c = canvas.Canvas(output_path, pagesize=A4)
        width, height = A4
        
        # Set margins based on template
        if template in ['4', '8']:  # Two-column templates
            left_margin = 0.5 * inch
        else:
            left_margin = 0.7 * inch
            
        top_margin = height - (0.7 * inch)
        current_y = top_margin
        line_height = 18
        
        # Personal Information
        personal_info = resume_data.get('personal_info', {})
        
        # TEMPLATE-SPECIFIC STYLING
        template_styles = {
            '1': {'primary_color': colors.HexColor('#2c3e50'), 'secondary_color': colors.HexColor('#3498db')},
            '2': {'primary_color': colors.HexColor('#2c3e50'), 'secondary_color': colors.HexColor('#e74c3c')},
            '3': {'primary_color': colors.HexColor('#3498db'), 'secondary_color': colors.HexColor('#2c3e50')},
            '4': {'primary_color': colors.HexColor('#27ae60'), 'secondary_color': colors.HexColor('#2c3e50')},
            '5': {'primary_color': colors.HexColor('#e67e22'), 'secondary_color': colors.HexColor('#2c3e50')},
            '6': {'primary_color': colors.HexColor('#9b59b6'), 'secondary_color': colors.HexColor('#3498db')},
            '7': {'primary_color': colors.HexColor('#e74c3c'), 'secondary_color': colors.HexColor('#2c3e50')},
            '8': {'primary_color': colors.HexColor('#34495e'), 'secondary_color': colors.HexColor('#e74c3c')},
            '9': {'primary_color': colors.HexColor('#d35400'), 'secondary_color': colors.HexColor('#27ae60')},
            '10': {'primary_color': colors.black, 'secondary_color': colors.HexColor('#666666')}
        }
        
        style = template_styles.get(template, template_styles['1'])
        primary_color = style['primary_color']
        secondary_color = style['secondary_color']
        
        # Add photo if included
        if include_photo and photo_data:
            try:
                if ',' in photo_data:
                    photo_data = photo_data.split(',')[1]
                
                photo_bytes = base64.b64decode(photo_data)
                photo_img = ImageReader(BytesIO(photo_bytes))
                
                # Photo positioning based on template
                if template in ['4', '8']:  # Two-column templates
                    photo_size = 1.0 * inch
                    photo_x = width - photo_size - left_margin
                    photo_y = top_margin - photo_size
                else:
                    photo_size = 1.2 * inch
                    photo_x = width - photo_size - left_margin
                    photo_y = top_margin - photo_size
                
                c.drawImage(photo_img, photo_x, photo_y, width=photo_size, height=photo_size, mask='auto')
                
                # Adjust current_y based on template
                if template in ['1', '3', '5']:
                    current_y -= photo_size + 10
                
            except Exception as e:
                print(f"Photo processing error: {e}")
        
        # HEADER SECTION
        if template in ['4', '8']:  # Two-column templates
            # Name and title on left, photo already placed on right
            name = personal_info.get('name', 'Your Name')
            c.setFont("Helvetica-Bold", 20)
            c.setFillColor(primary_color)
            c.drawString(left_margin, current_y, name)
            current_y -= 25
            
            title = personal_info.get('title', 'Job Title')
            c.setFont("Helvetica", 16)
            c.setFillColor(secondary_color)
            c.drawString(left_margin, current_y, title)
            current_y -= 35
            
        else:  # Centered header for other templates
            name = personal_info.get('name', 'Your Name')
            c.setFont("Helvetica-Bold", 24)
            c.setFillColor(primary_color)
            name_width = c.stringWidth(name, "Helvetica-Bold", 24)
            c.drawString((width - name_width) / 2, current_y, name)
            current_y -= 30
            
            title = personal_info.get('title', 'Job Title')
            c.setFont("Helvetica", 18)
            c.setFillColor(secondary_color)
            title_width = c.stringWidth(title, "Helvetica", 18)
            c.drawString((width - title_width) / 2, current_y, title)
            current_y -= 35
        
        # FIXED: Contact Information with PROPER LINE BREAKS
        contact_parts = []
        if personal_info.get('email'):
            contact_parts.append(f"Email: {personal_info['email']}")
        if personal_info.get('phone'):
            contact_parts.append(f"Phone: {personal_info['phone']}")
        if personal_info.get('address'):
            contact_parts.append(f"Address: {personal_info['address']}")
        
        # Display contact information with proper line breaks
        if contact_parts:
            c.setFont("Helvetica", 12)
            c.setFillColor(colors.black)
            
            contact_y = current_y
            
            # Display each contact item on separate lines
            for i, contact_item in enumerate(contact_parts):
                if template in ['4', '8']:
                    # Left aligned for two-column templates
                    c.drawString(left_margin, contact_y, contact_item)
                else:
                    # Centered for other templates
                    contact_width = c.stringWidth(contact_item, "Helvetica", 12)
                    c.drawString((width - contact_width) / 2, contact_y, contact_item)
                
                contact_y -= 20  # Move down for next line
            
            current_y = contact_y - 10  # Extra space after contact info
            
        else:
            # Default contact info if nothing provided
            default_contacts = [
                "Email: your.email@example.com",
                "Phone: (123) 456-7890", 
                "Address: Your Address"
            ]
            
            c.setFont("Helvetica", 12)
            c.setFillColor(colors.black)
            
            contact_y = current_y
            for contact_item in default_contacts:
                if template in ['4', '8']:
                    c.drawString(left_margin, contact_y, contact_item)
                else:
                    contact_width = c.stringWidth(contact_item, "Helvetica", 12)
                    c.drawString((width - contact_width) / 2, contact_y, contact_item)
                contact_y -= 20
            
            current_y = contact_y - 10
        
        # Draw a line separator
        c.setStrokeColor(primary_color)
        if template == '5':
            c.setLineWidth(2)
            c.line(left_margin, current_y, width - left_margin, current_y)
            current_y -= 30
        else:
            c.setLineWidth(1)
            c.line(left_margin, current_y, width - left_margin, current_y)
            current_y -= 25
        
        # TWO-COLUMN LAYOUT for templates 4 and 8
        if template in ['4', '8']:
            current_y = create_two_column_resume(c, resume_data, width, height, left_margin, current_y, 
                                               primary_color, secondary_color, line_height)
        else:
            # SINGLE COLUMN LAYOUT for other templates
            current_y = create_single_column_resume(c, resume_data, width, left_margin, current_y, 
                                                  primary_color, secondary_color, line_height, template)
        
        # Declaration Section
        if template in ['4', '8']:
            # Declaration in left column (already handled in two-column function)
            pass
        else:
            c.setFont("Helvetica-Bold", 16)
            c.setFillColor(primary_color)
            c.drawString(left_margin, current_y, "DECLARATION")
            current_y -= 20
            
            c.setFont("Helvetica", 14)
            c.setFillColor(colors.black)
            c.drawString(left_margin, current_y, "I hereby declare that all information provided is true to the best of my knowledge.")
            current_y -= 35
            
            # Signature area
            signature_name = resume_data.get('signature_name', '')
            date = resume_data.get('date', '')
            place = resume_data.get('place', '')
            
            signature_y = current_y
            c.line(left_margin, signature_y, left_margin + 200, signature_y)
            c.setFont("Helvetica", 14)
            c.drawString(left_margin, signature_y - 20, signature_name or "Your Name")
            c.drawString(left_margin, signature_y - 40, "Signature")
            
            date_text = f"Date: {date}" if date else "Date: ________"
            place_text = f"Place: {place}" if place else "Place: _______"
            
            c.drawString(width - 200, signature_y - 20, date_text)
            c.drawString(width - 200, signature_y - 40, place_text)
        
        # Save PDF
        c.save()
        print(f"Resume PDF created successfully with template {template}: {output_path}")
        
    except Exception as e:
        print(f"PDF creation error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise Exception(f"Failed to create PDF: {str(e)}")

def create_single_column_resume(c, resume_data, width, left_margin, current_y, primary_color, secondary_color, line_height, template):
    """Create single column resume layout with LARGER FONTS"""
    from reportlab.lib import colors
    
    sections = [
        ('summary', 'CAREER OBJECTIVE'),
        ('profile', 'PERSONAL PROFILE'), 
        ('education', 'EDUCATION'),
        ('experience', 'EXPERIENCE'),
        ('skills', 'SKILLS')
    ]
    
    for section_key, section_title in sections:
        content = resume_data.get(section_key, '')
        if content:
            # Section title with template-specific styling and LARGER FONTS
            if template == '3':
                c.setFillColor(colors.white)
                c.setStrokeColor(primary_color)
                c.setFont("Helvetica-Bold", 16)  # Increased from 12
                title_width = c.stringWidth(section_title, "Helvetica-Bold", 16)
                c.roundRect(left_margin, current_y - 5, title_width + 10, 25, 5, fill=1)  # Increased height
                c.setFillColor(primary_color)
                c.drawString(left_margin + 5, current_y, section_title)
                current_y -= 30  # Increased from 25
            elif template == '6':
                c.setFont("Helvetica-Bold", 16)  # Increased from 12
                c.setFillColor(primary_color)
                c.drawString(left_margin, current_y, section_title)
                c.setStrokeColor(primary_color)
                c.setLineWidth(2)
                c.line(left_margin, current_y - 2, left_margin + 100, current_y - 2)
                current_y -= 25  # Increased from 20
            else:
                c.setFont("Helvetica-Bold", 16)  # Increased from 12
                c.setFillColor(primary_color)
                c.drawString(left_margin, current_y, section_title)
                current_y -= 20  # Increased from 15
            
            # Content with LARGER FONT
            c.setFont("Helvetica", 14)  # Increased from 10
            c.setFillColor(colors.black)
            
            if section_key == 'profile':
                # Process as bullet points
                content_lines = content.split('\n')
                for line in content_lines:
                    if line.strip():
                        c.drawString(left_margin, current_y, "• " + line.strip())
                        current_y -= line_height
                        if current_y < 100:
                            c.showPage()
                            current_y = 750
            else:
                # Process as wrapped text
                words = content.split()
                line = ""
                for word in words:
                    test_line = line + word + " "
                    if c.stringWidth(test_line, "Helvetica", 14) < (width - 2 * left_margin):  # Increased font size
                        line = test_line
                    else:
                        c.drawString(left_margin, current_y, line.strip())
                        current_y -= line_height
                        line = word + " "
                        if current_y < 100:
                            c.showPage()
                            current_y = 750
                
                if line:
                    c.drawString(left_margin, current_y, line.strip())
                    current_y -= line_height
            
            current_y -= 15  # Increased from 10
    
    return current_y

def create_two_column_resume(c, resume_data, width, height, left_margin, start_y, primary_color, secondary_color, line_height):
    """Create two-column resume layout for templates 4 and 8 with LARGER FONTS"""
    from reportlab.lib import colors
    
    col_width = (width - 2 * left_margin - 20) / 2
    left_col_x = left_margin
    right_col_x = left_margin + col_width + 20
    current_y_left = start_y
    current_y_right = start_y
    
    # Left column sections
    left_sections = [
        ('summary', 'CAREER OBJECTIVE'),
        ('education', 'EDUCATION'),
        ('skills', 'SKILLS')
    ]
    
    # Right column sections  
    right_sections = [
        ('profile', 'PERSONAL PROFILE'),
        ('experience', 'EXPERIENCE')
    ]
    
    # Process left column with LARGER FONTS
    for section_key, section_title in left_sections:
        content = resume_data.get(section_key, '')
        if content:
            c.setFont("Helvetica-Bold", 14)  # Increased from 11
            c.setFillColor(primary_color)
            c.drawString(left_col_x, current_y_left, section_title)
            current_y_left -= 20  # Increased from 15
            
            c.setFont("Helvetica", 12)  # Increased from 9
            c.setFillColor(colors.black)
            
            if section_key == 'skills':
                content_lines = content.split('\n')
                for line in content_lines:
                    if line.strip():
                        c.drawString(left_col_x, current_y_left, "• " + line.strip())
                        current_y_left -= line_height - 2
            else:
                words = content.split()
                line = ""
                for word in words:
                    test_line = line + word + " "
                    if c.stringWidth(test_line, "Helvetica", 12) < col_width:  # Increased font size
                        line = test_line
                    else:
                        c.drawString(left_col_x, current_y_left, line.strip())
                        current_y_left -= line_height - 2
                        line = word + " "
                
                if line:
                    c.drawString(left_col_x, current_y_left, line.strip())
                    current_y_left -= line_height - 2
            
            current_y_left -= 15  # Increased from 10
    
    # Process right column with LARGER FONTS
    for section_key, section_title in right_sections:
        content = resume_data.get(section_key, '')
        if content:
            c.setFont("Helvetica-Bold", 14)  # Increased from 11
            c.setFillColor(primary_color)
            c.drawString(right_col_x, current_y_right, section_title)
            current_y_right -= 20  # Increased from 15
            
            c.setFont("Helvetica", 12)  # Increased from 9
            c.setFillColor(colors.black)
            
            content_lines = content.split('\n')
            for line in content_lines:
                if line.strip():
                    c.drawString(right_col_x, current_y_right, "• " + line.strip())
                    current_y_right -= line_height - 2
            
            current_y_right -= 15  # Increased from 10
    
    # Declaration at bottom with LARGER FONTS
    declaration_y = min(current_y_left, current_y_right) - 50  # Increased from 40
    c.setFont("Helvetica-Bold", 14)  # Increased from 11
    c.setFillColor(primary_color)
    c.drawString(left_col_x, declaration_y, "DECLARATION")
    declaration_y -= 15  # Increased from 12
    
    c.setFont("Helvetica", 12)  # Increased from 9
    c.setFillColor(colors.black)
    c.drawString(left_col_x, declaration_y, "I hereby declare that all information provided is true to the best of my knowledge.")
    declaration_y -= 35  # Increased from 30
    
    # Signature with LARGER FONTS
    signature_name = resume_data.get('signature_name', '')
    date = resume_data.get('date', '')
    place = resume_data.get('place', '')
    
    c.line(left_col_x, declaration_y, left_col_x + 150, declaration_y)
    c.setFont("Helvetica", 12)  # Increased from 9
    c.drawString(left_col_x, declaration_y - 15, signature_name or "Your Name")  # Increased spacing
    c.drawString(left_col_x, declaration_y - 30, "Signature")  # Increased spacing
    
    date_text = f"Date: {date}" if date else "Date: ________"
    place_text = f"Place: {place}" if place else "Place: _______"
    
    c.drawString(right_col_x, declaration_y - 15, date_text)  # Increased spacing
    c.drawString(right_col_x, declaration_y - 30, place_text)  # Increased spacing
    
    return declaration_y - 60  # Increased from 50

@app.route('/download-resume/<filename>')
def download_resume(filename):
    """Download resume PDF"""
    try:
        file_path = os.path.join(app.config['RESUME_FOLDER'], filename)
        
        if os.path.exists(file_path):
            return send_file(
                file_path, 
                as_attachment=True,
                download_name=f"resume_{filename}",
                mimetype='application/pdf'
            )
        else:
            return jsonify({'success': False, 'error': 'File not found'}), 404
            
    except Exception as e:
        print(f"Resume download error: {str(e)}")
        return jsonify({'success': False, 'error': f'Download failed: {str(e)}'}), 500

# ==================== SIMPLE RESUME DOWNLOAD (ALTERNATIVE) ====================

@app.route('/simple-download-resume', methods=['POST'])
def simple_download_resume():
    """Simple resume download - direct from frontend data"""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        
        # Get data from request
        data = request.json
        
        # Create PDF
        file_id = secrets.token_hex(8)
        pdf_filename = f"{file_id}_resume.pdf"
        pdf_path = os.path.join(app.config['RESUME_FOLDER'], pdf_filename)
        
        c = canvas.Canvas(pdf_path, pagesize=A4)
        width, height = A4
        
        # Set starting position
        y_position = height - 50
        
        # Name
        c.setFont("Helvetica-Bold", 20)
        c.setFillColor(colors.HexColor('#2c3e50'))
        c.drawString(50, y_position, data.get('name', 'Your Name'))
        y_position -= 30
        
        # Title
        c.setFont("Helvetica", 14)
        c.setFillColor(colors.HexColor('#3498db'))
        c.drawString(50, y_position, data.get('title', 'Job Title'))
        y_position -= 40
        
        # Contact Info
        c.setFont("Helvetica", 10)
        c.setFillColor(colors.black)
        
        contact_info = []
        if data.get('email'): contact_info.append(f"Email: {data['email']}")
        if data.get('phone'): contact_info.append(f"Phone: {data['phone']}")
        if data.get('address'): contact_info.append(f"Address: {data['address']}")
        
        if contact_info:
            contact_text = " | ".join(contact_info)
            c.drawString(50, y_position, contact_text)
            y_position -= 30
        
        # Draw separator line
        c.line(50, y_position, width-50, y_position)
        y_position -= 30
        
        # Career Objective
        if data.get('objective'):
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, y_position, "CAREER OBJECTIVE")
            y_position -= 20
            
            c.setFont("Helvetica", 10)
            objective = data.get('objective', '')
            # Simple text wrapping
            words = objective.split()
            line = ""
            for word in words:
                test_line = line + word + " "
                if c.stringWidth(test_line, "Helvetica", 10) < (width - 100):
                    line = test_line
                else:
                    c.drawString(50, y_position, line.strip())
                    y_position -= 15
                    line = word + " "
            if line:
                c.drawString(50, y_position, line.strip())
                y_position -= 20
        
        # Skills
        if data.get('skills'):
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, y_position, "SKILLS")
            y_position -= 20
            
            c.setFont("Helvetica", 10)
            skills = data.get('skills', '')
            skills_lines = skills.split('\n')
            for skill in skills_lines:
                if skill.strip():
                    c.drawString(50, y_position, "• " + skill.strip())
                    y_position -= 15
        
        # Save PDF
        c.save()
        
        return jsonify({
            'success': True,
            'pdf_file': pdf_filename,
            'download_url': f'/download-resume/{pdf_filename}'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# ==================== PASSPORT PHOTO AI ROUTES - IMPROVED ====================

@app.route('/process-image', methods=['POST'])
def process_image_ai():
    """ULTRA FAST AI background removal - MAX SPEED VERSION"""
    try:
        start_time = time.time()
        
        data = request.json
        image_data = data.get('image')
        
        if not image_data:
            return jsonify({'success': False, 'error': 'No image data provided'})
        
        # Fast processing
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        image_bytes = base64.b64decode(image_data)
        
        # Direct processing
        from io import BytesIO
        input_image = Image.open(BytesIO(image_bytes))
        
        # Speed optimization: Smaller size for faster processing
        original_size = input_image.size
        if max(original_size) > 600:
            input_image.thumbnail((600, 600), Image.Resampling.LANCZOS)
        
        # Fast background removal
        try:
            output_image = remove(input_image)
            if output_image.mode != 'RGBA':
                output_image = output_image.convert('RGBA')
            method = "rembg_fast"
        except:
            # Ultra fast fallback
            if input_image.mode != 'RGBA':
                input_image = input_image.convert('RGBA')
            output_image = input_image
            method = "direct_fallback"
        
        # Fast base64 conversion
        buffered = BytesIO()
        output_image.save(buffered, format="PNG", optimize=True)
        processed_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
        
        processing_time = time.time() - start_time
        
        return jsonify({
            'success': True,
            'image': f"data:image/png;base64,{processed_base64}",
            'processing_time': f"{processing_time:.2f}s",
            'message': f'Ultra fast processing in {processing_time:.2f} seconds!'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Processing failed: {str(e)}'})

# ==================== IMPROVED BACKGROUND REMOVAL ====================

def remove_background_improved(image_path):
    """Improved background removal with better quality preservation"""
    try:
        # Read image
        input_image = Image.open(image_path)
        
        # Convert to RGB if necessary
        if input_image.mode != 'RGB':
            input_image = input_image.convert('RGB')
        
        # Try to use rembg if available
        try:
            from rembg import remove
            print("Using rembg for background removal...")
            
            # Remove background
            output_image = remove(input_image)
            
            # Ensure the output is in RGBA mode for transparency
            if output_image.mode != 'RGBA':
                output_image = output_image.convert('RGBA')
            
            print("Background removal successful")
            return output_image, "rembg_success"
            
        except ImportError:
            print("Rembg not available, using fallback method")
            # Fallback: Simple background removal using edge detection
            return simple_background_removal(input_image), "fallback_no_rembg"
            
    except Exception as e:
        print(f"Background removal failed: {e}")
        # Ultimate fallback - return original image
        return Image.open(image_path).convert('RGBA'), "fallback_error"

def simple_background_removal(input_image):
    """Simple background removal using edge detection and masking"""
    try:
        # Convert to numpy array
        img_array = np.array(input_image)
        
        # Create a mask based on edge detection
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        edges = cv2.Canny(gray, 100, 200)
        
        # Dilate edges to create a better mask
        kernel = np.ones((5,5), np.uint8)
        dilated_edges = cv2.dilate(edges, kernel, iterations=2)
        
        # Create alpha channel based on edges
        alpha = np.ones(gray.shape, dtype=np.uint8) * 255
        alpha[dilated_edges == 0] = 0  # Set background to transparent
        
        # Convert back to PIL Image with alpha channel
        rgba_array = np.dstack((img_array, alpha))
        output_image = Image.fromarray(rgba_array, 'RGBA')
        
        return output_image
        
    except Exception as e:
        print(f"Simple background removal failed: {e}")
        # Return original image with white background removed
        img_array = np.array(input_image)
        white_threshold = 200
        mask = np.all(img_array > white_threshold, axis=2)
        
        # Create alpha channel
        alpha = np.ones(img_array.shape[:2], dtype=np.uint8) * 255
        alpha[mask] = 0
        
        rgba_array = np.dstack((img_array, alpha))
        return Image.fromarray(rgba_array, 'RGBA')

# ==================== PASSPORT PHOTO CREATION ====================

def create_passport_photo_improved(image, size_px=(600, 600), bg_color='#FFFFFF'):
    """Create passport photo with improved background handling"""
    try:
        width_px, height_px = size_px
        
        # Handle background color
        if bg_color == 'transparent':
            # Create transparent background
            result = Image.new('RGBA', (width_px, height_px), (255, 255, 255, 0))
        else:
            # Convert hex to RGB if needed
            if isinstance(bg_color, str) and bg_color.startswith('#'):
                bg_color_hex = bg_color.lstrip('#')
                bg_color_rgb = tuple(int(bg_color_hex[i:i+2], 16) for i in (0, 2, 4))
            else:
                bg_color_rgb = (255, 255, 255)  # Default white
            
            # Create solid background
            result = Image.new('RGB', (width_px, height_px), bg_color_rgb)
        
        # Calculate scaling to fit within passport photo while maintaining aspect ratio
        img_ratio = image.width / image.height
        passport_ratio = width_px / height_px
        
        if img_ratio > passport_ratio:
            # Image is wider, scale by width
            new_width = width_px
            new_height = int(width_px / img_ratio)
        else:
            # Image is taller, scale by height
            new_height = height_px
            new_width = int(height_px * img_ratio)
        
        # Resize image with high quality
        img_resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Calculate position to center the image
        x = (width_px - new_width) // 2
        y = (height_px - new_height) // 2
        
        # Paste onto result
        if img_resized.mode == 'RGBA' and result.mode == 'RGBA':
            result.paste(img_resized, (x, y), img_resized)
        elif img_resized.mode == 'RGBA' and result.mode == 'RGB':
            # Convert RGBA to RGB before pasting on RGB background
            rgb_img = Image.new('RGB', img_resized.size, bg_color_rgb)
            rgb_img.paste(img_resized, (0, 0), img_resized)
            result.paste(rgb_img, (x, y))
        else:
            result.paste(img_resized, (x, y))
        
        return result
        
    except Exception as e:
        print(f"Passport photo creation error: {e}")
        raise Exception(f"Passport photo creation failed: {str(e)}")

@app.route('/create-passport-photo', methods=['POST'])
def create_passport_photo_route():
    """Create final passport photo with custom settings - IMPROVED VERSION"""
    try:
        data = request.json
        image_data = data.get('image')
        size_type = data.get('size_type', '2x2')
        bg_color = data.get('bg_color', '#FFFFFF')
        crop_data = data.get('crop_data', {})
          
        if not image_data:
            return jsonify({'success': False, 'error': 'No image data provided'})
        
        # Remove data URL prefix
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        # Decode base64 image
        image_bytes = base64.b64decode(image_data)
        
        # Process image
        file_id = secrets.token_hex(8)
        temp_filename = f"{file_id}_temp.png"
        temp_path = os.path.join(app.config['PASSPORT_FOLDER'], temp_filename)
        
        with open(temp_path, 'wb') as f:
            f.write(image_bytes)
        
        # Define sizes in pixels (width, height)
        sizes_px = {
            '2x2': (600, 600),
            '3.5x4.5': (413, 531),
            '3x4': (354, 472),
            'custom_413x531': (413, 531),
            'custom_600x600': (600, 600),
            'custom_354x472': (354, 472)
        }
        
        size_px = sizes_px.get(size_type, (600, 600))
        
        # Load and process image
        with Image.open(temp_path) as img:
            # Apply cropping if crop data is provided
            if crop_data and all(k in crop_data for k in ['x', 'y', 'width', 'height', 'scale']):
                try:
                    scale = crop_data['scale']
                    x = crop_data['x']
                    y = crop_data['y']
                    width = crop_data['width']
                    height = crop_data['height']
                    
                    # Convert preview coordinates to original image coordinates
                    orig_x = int(x / scale)
                    orig_y = int(y / scale)
                    orig_width = int(width / scale)
                    orig_height = int(height / scale)
                    
                    # Ensure coordinates are within image bounds
                    orig_x = max(0, min(orig_x, img.width - 1))
                    orig_y = max(0, min(orig_y, img.height - 1))
                    orig_width = min(orig_width, img.width - orig_x)
                    orig_height = min(orig_height, img.height - orig_y)
                    
                    if orig_width > 0 and orig_height > 0:
                        # Crop the image
                        img = img.crop((orig_x, orig_y, orig_x + orig_width, orig_y + orig_height))
                        
                except Exception as crop_error:
                    print(f"Crop processing error: {crop_error}")
                    # Continue without cropping
            
            # Create passport photo with improved function
            passport_photo = create_passport_photo_improved(
                img, 
                size_px=size_px,
                bg_color=bg_color
            )
        
        # Save passport photo
        passport_filename = f"{file_id}_passport_{size_type}.png"
        passport_path = os.path.join(app.config['PASSPORT_FOLDER'], passport_filename)
        
        # Save based on background type
        if bg_color == 'transparent':
            passport_photo.save(passport_path, format='PNG', optimize=True)
        else:
            if passport_photo.mode == 'RGBA':
                passport_photo = passport_photo.convert('RGB')
            passport_photo.save(passport_path, format='PNG', optimize=True)
        
        passport_files_info.append(passport_filename)
        
        # Convert to base64 for response
        with open(passport_path, 'rb') as f:
            passport_base64 = base64.b64encode(f.read()).decode('utf-8')
        
        return jsonify({
            'success': True,
            'image': f"data:image/png;base64,{passport_base64}",
            'filename': passport_filename,
            'message': f'Passport photo ({size_type}) created successfully!',
            'size': size_type,
            'dimensions': f"{size_px[0]}x{size_px[1]}px",
            'background': bg_color
        })
        
    except Exception as e:
        print(f"Passport photo creation error: {str(e)}")
        return jsonify({'success': False, 'error': f'Passport photo creation failed: {str(e)}'})

# ==================== EXISTING PASSPORT PHOTO ROUTES ====================

@app.route('/passport-photo')
def passport_photo():
    return render_template('passport_photo.html')

@app.route('/upload-passport-photo', methods=['POST'])
def upload_passport_photo():
    """Handle passport photo upload and processing"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file selected'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'})
        
        # Validate file type
        allowed_extensions = {'jpg', 'jpeg', 'png', 'webp'}
        if not '.' in file.filename or file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
            return jsonify({'success': False, 'error': 'Invalid file type. Please upload JPG, PNG, or WEBP.'})
        
        # Validate file size (10MB max)
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to beginning
        
        if file_size > 10 * 1024 * 1024:
            return jsonify({'success': False, 'error': 'File size must be less than 10MB'})
        
        # Save uploaded file
        file_id = secrets.token_hex(8)
        original_filename = f"{file_id}_original.{file.filename.rsplit('.', 1)[1].lower()}"
        original_path = os.path.join(app.config['PASSPORT_FOLDER'], original_filename)
        file.save(original_path)
        
        # Process image (background removal)
        processed_image, method = remove_background_improved(original_path)
        
        # Save processed image
        processed_filename = f"{file_id}_processed.png"
        processed_path = os.path.join(app.config['PASSPORT_FOLDER'], processed_filename)
        
        processed_image.save(processed_path, 'PNG', optimize=True)
        
        passport_files_info.extend([original_filename, processed_filename])
        
        return jsonify({
            'success': True,
            'message': 'Photo processed successfully with background removal!',
            'file_id': file_id,
            'processed_file': processed_filename,
            'method': method
        })
        
    except Exception as e:
        print(f"Passport photo upload error: {str(e)}")
        return jsonify({'success': False, 'error': f'Photo processing failed: {str(e)}'})

@app.route('/create-passport-size', methods=['POST'])
def create_passport_size():
    """Create passport photo with specific size"""
    try:
        data = request.json
        processed_file = data.get('processed_file')
        size_type = data.get('size_type', '2x2')
        bg_color = data.get('bg_color', '#FFFFFF')
        
        if not processed_file:
            return jsonify({'success': False, 'error': 'Processed file is required'})
        
        processed_path = os.path.join(app.config['PASSPORT_FOLDER'], processed_file)
        
        if not os.path.exists(processed_path):
            return jsonify({'success': False, 'error': 'Processed file not found'})
        
        # Define sizes in pixels
        sizes_px = {
            '2x2': (600, 600),
            '3.5x4.5': (413, 531),
            '3x4': (354, 472)
        }
        
        size_px = sizes_px.get(size_type, (600, 600))
        
        # Load processed image
        processed_image = Image.open(processed_path)
        
        # Create passport photo
        passport_photo = create_passport_photo_improved(
            processed_image, 
            size_px=size_px,
            bg_color=bg_color
        )
        
        # Save passport photo
        file_id = secrets.token_hex(8)
        passport_filename = f"{file_id}_passport_{size_type.replace('x', 'x')}.png"
        passport_path = os.path.join(app.config['PASSPORT_FOLDER'], passport_filename)
        
        if passport_photo.mode == 'RGBA' and bg_color != 'transparent':
            passport_photo = passport_photo.convert('RGB')
        
        passport_photo.save(passport_path, format='PNG', optimize=True)
        passport_files_info.append(passport_filename)
        
        return jsonify({
            'success': True,
            'passport_file': passport_filename,
            'message': f'Passport photo ({size_type}) created successfully!',
            'size': size_type
        })
        
    except Exception as e:
        print(f"Passport size creation error: {str(e)}")
        return jsonify({'success': False, 'error': f'Passport photo creation failed: {str(e)}'})

@app.route('/create-photo-sheet', methods=['POST'])
def create_photo_sheet_route():
    """Create sheet with multiple passport photos"""
    try:
        data = request.json
        passport_file = data.get('passport_file')
        photos_per_sheet = int(data.get('photos_per_sheet', 4))
        size_type = data.get('size_type', '2x2')
        
        if not passport_file:
            return jsonify({'success': False, 'error': 'Passport file is required'})
        
        passport_path = os.path.join(app.config['PASSPORT_FOLDER'], passport_file)
        
        if not os.path.exists(passport_path):
            return jsonify({'success': False, 'error': 'Passport file not found'})
        
        # Define sizes in pixels
        sizes_px = {
            '2x2': (600, 600),
            '3.5x4.5': (413, 531),
            '3x4': (354, 472)
        }
        
        photo_size_px = sizes_px.get(size_type, (600, 600))
        
        # Load passport photo and resize to exact size
        passport_photo = Image.open(passport_path)
        if passport_photo.size != photo_size_px:
            passport_photo = passport_photo.resize(photo_size_px, Image.Resampling.LANCZOS)
        
        # Create photo sheet
        photo_sheet = create_photo_sheet_advanced(passport_photo, photos_per_sheet, photo_size_px)
        
        # Save photo sheet
        file_id = secrets.token_hex(8)
        sheet_filename = f"{file_id}_sheet_{photos_per_sheet}.png"
        sheet_path = os.path.join(app.config['PASSPORT_FOLDER'], sheet_filename)
        
        photo_sheet.save(sheet_path, dpi=(300, 300), format='PNG', optimize=True)
        passport_files_info.append(sheet_filename)
        
        return jsonify({
            'success': True,
            'sheet_file': sheet_filename,
            'message': f'Photo sheet with {photos_per_sheet} photos created successfully!',
            'photos_count': photos_per_sheet
        })
        
    except Exception as e:
        print(f"Photo sheet creation error: {str(e)}")
        return jsonify({'success': False, 'error': f'Photo sheet creation failed: {str(e)}'})

def create_photo_sheet_advanced(passport_photo, photos_per_sheet, photo_size_px):
    """Create photo sheet with multiple photos"""
    try:
        # Calculate grid layout
        if photos_per_sheet <= 4:
            cols = 2
            rows = 2
        elif photos_per_sheet <= 6:
            cols = 3
            rows = 2
        elif photos_per_sheet <= 8:
            cols = 4
            rows = 2
        elif photos_per_sheet <= 12:
            cols = 4
            rows = 3
        else:
            cols = 4
            rows = 4
        
        # Calculate sheet dimensions with margins
        margin = 50
        gap = 20
        sheet_width = (photo_size_px[0] * cols) + (gap * (cols - 1)) + (margin * 2)
        sheet_height = (photo_size_px[1] * rows) + (gap * (rows - 1)) + (margin * 2)
        
        # Create sheet with white background
        sheet = Image.new('RGB', (sheet_width, sheet_height), 'white')
        
        # Paste photos in grid
        for i in range(photos_per_sheet):
            if i >= cols * rows:
                break
                
            row = i // cols
            col = i % cols
            
            x = margin + (col * (photo_size_px[0] + gap))
            y = margin + (row * (photo_size_px[1] + gap))
            
            sheet.paste(passport_photo, (x, y))
        
        return sheet
        
    except Exception as e:
        print(f"Photo sheet creation error: {e}")
        raise Exception(f"Photo sheet creation failed: {str(e)}")

@app.route('/download-passport-file/<filename>')
def download_passport_file(filename):
    """Download passport photo files"""
    try:
        file_path = os.path.join(app.config['PASSPORT_FOLDER'], filename)
        
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        else:
            return jsonify({'success': False, 'error': 'File not found'}), 404
            
    except Exception as e:
        print(f"Passport file download error: {str(e)}")
        return jsonify({'success': False, 'error': f'Download failed: {str(e)}'}), 500

@app.route('/preview-passport-file/<filename>')
def preview_passport_file(filename):
    """Preview passport photo files"""
    try:
        file_path = os.path.join(app.config['PASSPORT_FOLDER'], filename)
        
        if os.path.exists(file_path):
            return send_file(file_path)
        else:
            return jsonify({'success': False, 'error': 'File not found'}), 404
            
    except Exception as e:
        print(f"Passport file preview error: {str(e)}")
        return jsonify({'success': False, 'error': f'Preview failed: {str(e)}'}), 500

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
            front_left = int(start_x + w * 0.007)
            front_top = int(h * 0.729)
            front_width = card_width - int(w * 0.01)
            front_height = card_height - int(h * 0.01)
            
            # Back Side (Right side - Address and QR Code)
            back_left = int(start_x + card_width + (w * 0.0162))
            back_top = int(h * 0.729)
            back_width = card_width - int(w * 0.01)
            back_height = card_height - int(h * 0.01)

        elif card_type == "jan-aadhaar":
            # Jan-Aadhaar - Same pattern as Aadhaar
            card_width = int(w * 0.42)
            card_height = int(card_width / 1.62)
            
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

# ==================== IMAGE CONVERTER ROUTES - UPDATED ====================

@app.route('/convert-image', methods=['POST'])
def convert_image():
    """Image format conversion endpoint - UPDATED VERSION"""
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
            
            # Return JSON response with file info for frontend
            return jsonify({
                'success': True,
                'message': f'Image converted to {output_format.upper()} successfully!',
                'converted_file': output_filename,
                'format': output_format,
                'file_id': file_id,
                'file_size': file_size,
                'file_size_kb': round(file_size / 1024, 2),
                'file_size_mb': round(file_size / (1024 * 1024), 2)
            })
            
    except Exception as e:
        print(f"Image conversion error: {str(e)}")
        return jsonify({'success': False, 'error': f'Conversion failed: {str(e)}'})

@app.route('/download-converted/<filename>')
def download_converted(filename):
    """Download converted image files"""
    try:
        file_path = os.path.join(app.config['CONVERTED_FOLDER'], filename)
        
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        else:
            return jsonify({'success': False, 'error': 'File not found'}), 404
            
    except Exception as e:
        print(f"Download error: {str(e)}")
        return jsonify({'success': False, 'error': f'Download failed: {str(e)}'}), 500

@app.route('/preview-converted/<filename>')
def preview_converted(filename):
    """Preview converted image files"""
    try:
        file_path = os.path.join(app.config['CONVERTED_FOLDER'], filename)
        
        if os.path.exists(file_path):
            return send_file(file_path)
        else:
            return jsonify({'success': False, 'error': 'File not found'}), 404
            
    except Exception as e:
        print(f"Preview error: {str(e)}")
        return jsonify({'success': False, 'error': f'Preview failed: {str(e)}'}), 500

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
        total_size = 0
        
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
                    
                    file_size = os.path.getsize(output_path)
                    total_size += file_size
                    
                    converted_files.append({
                        'filename': output_filename,
                        'original_name': original_filename,
                        'size': file_size,
                        'size_kb': round(file_size / 1024, 2),
                        'size_mb': round(file_size / (1024 * 1024), 2)
                    })
                    converted_files_info.append(output_filename)
        
        # Create ZIP if multiple files
        if len(converted_files) > 1:
            zip_filename = f"bulk_converted_{secrets.token_hex(8)}.zip"
            zip_path = os.path.join(app.config['CONVERTED_FOLDER'], zip_filename)
            
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for converted_file in converted_files:
                    file_path = os.path.join(app.config['CONVERTED_FOLDER'], converted_file['filename'])
                    zipf.write(file_path, converted_file['filename'])
            
            converted_files_info.append(zip_filename)
            
            return jsonify({
                'success': True,
                'message': f'{len(converted_files)} files converted to {output_format.upper()} and zipped!',
                'zip_file': zip_filename,
                'converted_count': len(converted_files),
                'total_size_kb': round(total_size / 1024, 2),
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'format': output_format
            })
        else:
            return jsonify({
                'success': True,
                'message': f'Image converted to {output_format.upper()} successfully!',
                'converted_file': converted_files[0]['filename'],
                'file_size_kb': converted_files[0]['size_kb'],
                'file_size_mb': converted_files[0]['size_mb'],
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
        folders = [app.config['UPLOAD_FOLDER'], app.config['CROPPED_FOLDER'], app.config['CONVERTED_FOLDER'], app.config['PASSPORT_FOLDER'], app.config['RESUME_FOLDER']]
        
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
        # Check in all folders
        folders = [app.config['UPLOAD_FOLDER'], app.config['CROPPED_FOLDER'], app.config['CONVERTED_FOLDER'], app.config['PASSPORT_FOLDER'], app.config['RESUME_FOLDER']]
        
        for folder in folders:
            file_path = os.path.join(folder, filename)
            if os.path.exists(file_path):
                return send_file(file_path)
        
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
        folders = [app.config['UPLOAD_FOLDER'], app.config['CROPPED_FOLDER'], app.config['CONVERTED_FOLDER'], app.config['PASSPORT_FOLDER'], app.config['RESUME_FOLDER']]
        
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
        passport_files_info.clear()
        resume_files_info.clear()
        
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
        'converted_folder': len(os.listdir(app.config['CONVERTED_FOLDER'])) if os.path.exists(app.config['CONVERTED_FOLDER']) else 0,
        'passport_folder': len(os.listdir(app.config['PASSPORT_FOLDER'])) if os.path.exists(app.config['PASSPORT_FOLDER']) else 0,
        'resume_folder': len(os.listdir(app.config['RESUME_FOLDER'])) if os.path.exists(app.config['RESUME_FOLDER']) else 0
    })

if __name__ == '__main__':
    print("Starting Universal PVC Card Maker & AI Passport Photo Tool & Resume Builder...")
    print(f"Upload folder: {UPLOAD_FOLDER}")
    print(f"Cropped folder: {CROPPED_FOLDER}")
    print(f"Converted folder: {CONVERTED_FOLDER}")
    print(f"Passport folder: {PASSPORT_FOLDER}")
    print(f"Resume folder: {RESUME_FOLDER}")
    
    print("\nFeatures:")
    print("   • FIXED Professional Resume Builder with PDF download")
    print("   • IMPROVED Background Removal with better quality")
    print("   • Auto Front & Back cropping for ALL cards (Aadhaar, PAN, Voter ID, Jan-Aadhaar, Ayushman, Labour)")
    print("   • Consistent tight cropping pattern - no black borders")
    print("   • PVC Card conversion (8.6cm x 5.4cm) - NO BORDERS")
    print("   • Both sides download as combined PNG/JPG")
    print("   • Direct print functionality for all cards")
    print("   • ADVANCED AI Passport Photo Maker with background removal")
    print("   • Multiple passport sizes with exact pixel dimensions")
    print("   • Photo sheets with FIXED photo sizes (all images same size)")
    print("   • Transparent background support")
    print("   • Real-time background color change")
    print("   • Image Converter (JPG, PNG, GIF, BMP, TIFF, WEBP, ICO, PDF) with bulk conversion")
    print("   • Auto file cleanup (5 minutes)")
    print("   • Backward compatibility with old routes")
    
    # Start auto cleanup
    file_cleaner.start_auto_cleanup()
    print(f"Auto-delete enabled: Files will be deleted after 5 minutes")
    
    print("\nServer running on: http://localhost:5000")
    app.run(debug=True, port=5000, host='localhost')