E-Card Cutter - Universal Document & Photo Tool (Local Setup)

1) SYSTEM REQUIREMENTS:
   - Python 3.8+ installed (64-bit recommended)
   - Poppler (Windows) installed and PATH set to C:\poppler\Library\bin
     (Download: https://github.com/oschwartz10612/poppler-windows/releases/)
   - 4GB+ RAM recommended for AI processing
   - 500MB+ free disk space for temporary files

2) PROJECT STRUCTURE:
   E-Card-Cutter/
   ├── app.py                 # Main Flask application
   ├── requirements.txt       # Python dependencies
   ├── README.txt            # This file
   ├── static/               # CSS, JS, images
   ├── templates/            # HTML templates
   │   ├── index.html
   │   ├── aadhaar_crop.html
   │   ├── pan_crop.html
   │   ├── voterid_crop.html
   │   ├── janaadhaar_crop.html
   │   ├── ayushman_crop.html
   │   ├── labour_crop.html
   │   ├── image_converter.html
   │   ├── passport_photo.html
   │   ├── resume_builder.html
   │   └── other template files...
   ├── uploads/              # Temporary upload storage
   ├── cropped/              # Cropped card images
   ├── converted/            # Converted images
   ├── passport_photos/      # Passport photo outputs
   └── resumes/              # Generated resume PDFs

3) SETUP INSTRUCTIONS:

   Step 1: Create project folder and extract all files

   Step 2: (Recommended) Create virtual environment:
      python -m venv .venv
      .venv\Scripts\activate  (Windows)
      source .venv/bin/activate  (Linux/Mac)

   Step 3: Install dependencies:
      pip install -r requirements.txt

   Step 4: Run the application:
      python app.py

   Step 5: Open your browser and navigate to:
       http://localhost:5000

4) COMPREHENSIVE FEATURES:

   A) UNIVERSAL CARD CROPPER:
      - Supports Aadhaar, PAN, Voter ID, Jan-Aadhaar, Ayushman, Labour cards
      - Auto front & back extraction from PDF
      - Password-protected PDF support
      - Tight cropping (no black borders)
      - 300 DPI high-quality output
      - PVC card conversion (8.6cm × 5.4cm)

   B) PROFESSIONAL RESUME BUILDER:
      - 10+ professional templates
      - Real-time preview
      - Photo integration
      - PDF export with proper formatting
      - Contact information with line breaks
      - Single & two-column layouts
      - Declaration section with signature

   C) AI PASSPORT PHOTO MAKER:
      - Ultra-fast background removal
      - Multiple standard sizes (2x2, 3.5x4.5, 3x4 inches)
      - Custom background colors (white, blue, transparent)
      - Real-time editing and cropping
      - Photo sheet creation (multiple photos per sheet)
      - High-quality 300 DPI output

   D) ADVANCED IMAGE CONVERTER:
      - Support for JPG, PNG, GIF, BMP, TIFF, WEBP, ICO, PDF
      - Bulk conversion with ZIP download
      - Quality adjustment
      - Format-specific optimization
      - Batch processing

5) SECURITY FEATURES:
   - Auto file cleanup (files deleted after 5 minutes)
   - Secure file handling
   - No permanent storage of sensitive documents
   - Local processing only (no external API calls for card processing)

6) USAGE INSTRUCTIONS:

   For Card Cropping:
     1. Select card type (Aadhaar, PAN, Voter ID, etc.)
     2. Upload PDF file (password if required)
     3. System auto-detects and crops front & back
     4. Download individual sides or combined image
     5. Optional: Convert to PVC size for printing

   For Resume Building:
     1. Fill in personal details, education, experience, skills
     2. Choose from 10 professional templates
     3. Upload photo (optional)
     4. Preview and download as PDF

   For Passport Photos:
     1. Upload any photo
     2. Remove background automatically
     3. Crop and adjust as needed
     4. Choose size and background color
     5. Download single photo or photo sheet

   For Image Conversion:
     1. Upload single or multiple images
     2. Select target format and quality
     3. Convert and download individually or as ZIP

7) TROUBLESHOOTING:

   Common Issues:
   - "pdftoppm not found": Ensure C:\poppler\Library\bin is in PATH and restart terminal
   - "PDF password error": Enter correct password for protected PDFs
   - "Memory error": Close other applications and try smaller files
   - "Background removal failed": Try with different image or use manual crop

   Performance Tips:
   - Use images under 10MB for faster processing
   - For bulk operations, process files in smaller batches
   - Ensure adequate free disk space

8) LEGAL & PRIVACY NOTES:
   - Process identity documents only for legitimate purposes
   - Delete processed files after use
   - Do not share sensitive documents publicly
   - Comply with local data protection laws
   - This tool is for personal use only

9) TECHNICAL SUPPORT:
   - Check console for detailed error messages
   - Ensure all dependencies are properly installed
   - Verify file permissions in project folders
   - Restart application if unexpected behavior occurs

10) AUTO-CLEANUP FEATURE:
    - Files automatically deleted after 5 minutes
    - Manual cleanup available via interface
    - Temporary folders monitored continuously

The application is now running with ALL features enabled!
Visit  http://localhost:5000 to start using the Universal Document & Photo Tool.