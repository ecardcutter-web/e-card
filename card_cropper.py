import fitz  # PyMuPDF
import os
from PIL import Image
import uuid
import io

def process_pdf(pdf_path, output_dir, card_type='aadhaar', pdf_password=None):
    """Extract Aadhaar / Jan Aadhaar / Ayushman card region with 300 DPI clarity"""
    
    # ✅ Hardcode DPI to 300 - Always premium quality
    dpi = 300
    
    print(f"🔧 Processing PDF: {pdf_path}")
    print(f"📁 Output directory: {output_dir}")
    print(f"🎴 Card type: {card_type}")
    print(f"📊 DPI: {dpi} (Premium Quality)")
    print(f"🕒 File will auto-delete in 5 minutes (managed by file_cleaner)")
    
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

        # ✅ Crop region calculation
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
        elif card_type == "ayushman":
            left = int(w * 0.04)
            top = int(h * 0.22)
            card_width = int(w * 0.84)
            card_height = int(card_width / 2.55)
        else:
            left = int(w * 0.10)
            top = int(h * 0.20)
            card_width = int(w * 0.80)
            card_height = int(card_width / 1.62)

        print(f"✂️ Crop area: left={left}, top={top}, width={card_width}, height={card_height}")

        # ✅ Safety limits
        left = max(0, left)
        top = max(0, top)
        card_width = min(card_width, w - left)
        card_height = min(card_height, h - top)

        print(f"🔒 Safe Crop area: left={left}, top={top}, width={card_width}, height={card_height}")

        # ✅ Convert to PIL Image and crop directly (no temp files)
        img_data = pix.tobytes("ppm")
        img = Image.open(io.BytesIO(img_data))
        print(f"🖼️ PIL Image size: {img.size}")
        
        # ACTUAL CROP OPERATION
        cropped = img.crop((left, top, left + card_width, top + card_height))
        print(f"✂️ After crop size: {cropped.size}")

        # ✅ Final output path with unique name
        file_id = str(uuid.uuid4())[:8]
        out_path = os.path.join(output_dir, f"{file_id}_cropped.png")
        
        # ✅ Always 300 DPI के साथ save करें
        cropped.save(out_path, dpi=(dpi, dpi), format='PNG', optimize=True)
        print(f"✅ Final image saved: {out_path}")
        print(f"📏 Final dimensions: {cropped.size[0]} x {cropped.size[1]}")
        print(f"🎯 Quality: 300 DPI (Premium)")
        print(f"🕒 File will be auto-deleted in 5 minutes by file_cleaner")

        doc.close()
        
        return {
            'success': True,
            'output_file': out_path,
            'card_count': 1,
            'message': f'Card extracted successfully at 300 DPI Premium Quality - Auto-deletes in 5 minutes'
        }
        
    except Exception as e:
        print(f"❌ Error in process_pdf: {str(e)}")
        import traceback
        print(f"🔍 Traceback: {traceback.format_exc()}")
        return {
            'success': False,
            'error': str(e)
        }