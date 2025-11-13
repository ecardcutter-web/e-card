import fitz  # PyMuPDF
import os
from PIL import Image
import uuid
import io

def process_pdf_front_back(pdf_path, output_dir, card_type='aadhaar', pdf_password=None):
    """Extract Card Front & Back sides automatically with 300 DPI clarity - TIGHT CROPPING"""
    
    dpi = 300
    
    print(f"🔧 Processing PDF for Front & Back: {pdf_path}")
    print(f"📁 Output directory: {output_dir}")
    print(f"🎴 Card type: {card_type}")
    print(f"📊 DPI: {dpi} (Premium Quality)")
    
    # Output directory create करें अगर नहीं है
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    try:
        # PDF open करें
        doc = fitz.open(pdf_path)
        print(f"📄 PDF pages: {len(doc)}")
        
        # Password check अगर PDF protected है
        if doc.needs_pass:
            print("🔒 PDF is password protected")
            if pdf_password:
                if not doc.authenticate(pdf_password):
                    doc.close()
                    return {
                        'success': False,
                        'error': "Incorrect password or protected PDF could not be opened."
                    }
            else:
                doc.close()
                return {
                    'success': False,
                    'error': "PDF is password protected but no password provided."
                }

        # First page load करें
        page = doc.load_page(0)
        
        # ✅ ALWAYS 300 DPI - Premium quality
        matrix = fitz.Matrix(dpi/72, dpi/72)
        pix = page.get_pixmap(matrix=matrix, alpha=False)

        # Image dimensions
        w, h = pix.width, pix.height
        print(f"📐 Original Image dimensions: {w} x {h}")

        # ✅ CONSISTENT TIGHT CROP COORDINATES FOR ALL CARDS
        # Aadhaar card जैसा ही pattern सभी cards के लिए
        
        if card_type == "aadhaar":
            # Aadhaar - Tight cropping (no black border)
            card_width = int(w * 0.42)
            card_height = int(card_width / 1.59)
            
            total_cards_width = (card_width * 2) + (w * 0.008)
            start_x = (w - total_cards_width) / 2
            
            # Front Side (Left card)
            front_left = int(start_x + w * 0.005)
            front_top = int(h * 0.729)
            front_width = card_width - int(w * 0.01)
            front_height = card_height - int(h * 0.01)
            
            # Back Side (Right card)
            back_left = int(start_x + card_width + (w * 0.013))
            back_top = int(h * 0.729)
            back_width = card_width - int(w * 0.01)
            back_height = card_height - int(h * 0.01)
            
        elif card_type == "jan-aadhaar":
            # Jan-Aadhaar - Same pattern as Aadhaar
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
            
        elif card_type == "pan":
            # PAN Card - Same pattern as Aadhaar
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
            
        elif card_type == "voter":
            # Voter ID - Same pattern as Aadhaar
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
            
        elif card_type == "ayushman":
            # Ayushman Card - Same pattern as Aadhaar
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
            
        elif card_type == "labour":
            # ✅ NEW: Labour Card - Same pattern as Aadhaar
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
            
            print("🎴 Labour Card pattern applied - same as Aadhaar")
            
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

        print(f"📍 FRONT Coordinates: left={front_left}, top={front_top}, width={front_width}, height={front_height}")
        print(f"📍 BACK Coordinates: left={back_left}, top={back_top}, width={back_width}, height={back_height}")
        print(f"📏 Card Size: {card_width} x {card_height} pixels")
        print(f"🎯 Tight Crop: Only card content (no extra background)")

        # ✅ Safety limits for Front
        front_left = max(0, front_left)
        front_top = max(0, front_top)
        front_width = min(front_width, w - front_left)
        front_height = min(front_height, h - front_top)

        # ✅ Safety limits for Back
        back_left = max(0, back_left)
        back_top = max(0, back_top)
        back_width = min(back_width, w - back_left)
        back_height = min(back_height, h - back_top)

        print(f"🔒 Safe FRONT Crop: left={front_left}, top={front_top}, width={front_width}, height={front_height}")
        print(f"🔒 Safe BACK Crop: left={back_left}, top={back_top}, width={back_width}, height={back_height}")

        # ✅ Convert to PIL Image and crop both sides
        img_data = pix.tobytes("ppm")
        img = Image.open(io.BytesIO(img_data))
        print(f"🖼️ PIL Image size: {img.size}")
        
        # ACTUAL CROP OPERATION FOR BOTH SIDES
        front_cropped = img.crop((front_left, front_top, front_left + front_width, front_top + front_height))
        back_cropped = img.crop((back_left, back_top, back_left + back_width, back_top + back_height))
        
        print(f"✂️ After FRONT crop size: {front_cropped.size}")
        print(f"✂️ After BACK crop size: {back_cropped.size}")

        # ✅ Add slight white padding for better appearance
        padding = 2
        front_final = Image.new('RGB', (front_cropped.width + padding*2, front_cropped.height + padding*2), 'white')
        front_final.paste(front_cropped, (padding, padding))
        
        back_final = Image.new('RGB', (back_cropped.width + padding*2, back_cropped.height + padding*2), 'white')
        back_final.paste(back_cropped, (padding, padding))

        # ✅ Final output paths with unique name
        file_id = str(uuid.uuid4())[:8]
        front_out_path = os.path.join(output_dir, f"{file_id}_front.png")
        back_out_path = os.path.join(output_dir, f"{file_id}_back.png")
        
        # ✅ Always 300 DPI के साथ save करें
        front_final.save(front_out_path, dpi=(dpi, dpi), format='PNG', optimize=True)
        back_final.save(back_out_path, dpi=(dpi, dpi), format='PNG', optimize=True)
        
        print(f"✅ FRONT image saved: {front_out_path}")
        print(f"✅ BACK image saved: {back_out_path}")
        print(f"📏 FRONT dimensions: {front_final.size[0]} x {front_final.size[1]}")
        print(f"📏 BACK dimensions: {back_final.size[0]} x {back_final.size[1]}")
        print(f"🎯 Quality: 300 DPI (Premium)")
        print("🔄 Front & Back sides automatically extracted with TIGHT CROP!")

        doc.close()
        
        return {
            'success': True,
            'front_file': f"{file_id}_front.png",
            'back_file': f"{file_id}_back.png",
            'file_id': file_id,
            'message': 'Front & Back sides extracted successfully with tight cropping (no extra background)'
        }
        
    except Exception as e:
        print(f"❌ Error in process_pdf_front_back: {str(e)}")
        import traceback
        print(f"🔍 Traceback: {traceback.format_exc()}")
        return {
            'success': False,
            'error': str(e)
        }

# Legacy function for single card (backward compatibility)
def process_pdf(pdf_path, output_dir, card_type='aadhaar', pdf_password=None):
    """Legacy function - uses new front-back system but returns only front"""
    result = process_pdf_front_back(pdf_path, output_dir, card_type, pdf_password)
    
    if result['success']:
        # Return only front for backward compatibility
        return {
            'success': True,
            'output_file': os.path.join(output_dir, result['front_file']),
            'card_count': 1,
            'message': result['message']
        }
    else:
        return result