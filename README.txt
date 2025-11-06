E-Card Cutter - local setup

1) System requirements:
   - Python 3.8+ installed (64-bit recommended)
   - Poppler (Windows) installed and PATH set to C:\poppler\Library\bin
     (download: https://github.com/oschwartz10612/poppler-windows/releases)

2) Create project folder and paste files as per structure.

3) (Recommended) Create virtual environment:
   python -m venv .venv
   .venv\Scripts\activate

4) Install dependencies:
   pip install -r requirements.txt

5) Run the app:
   python app.py

6) Open browser:
   http://127.0.0.1:5000

7) Usage:
   - Upload Aadhaar or Jan-Aadhaar PDF (password-protected allowed: enter password)
   - Optional: upload one sample image to improve matching
   - Optional: upload logo to overlay
   - Click "Process & Preview" -> see cropped preview -> Download PNG

Security notes:
 - Delete uploaded PDFs after processing if not needed.
 - Avoid running on public server without proper security.
 - Follow legal rules for storing/processing identity documents.

Troubleshooting:
 - If pdftoppm not found -> ensure C:\poppler\Library\bin in PATH & restart terminal.
 - If pdf2image errors -> check poppler install & permissions.
 - If OpenCV errors -> reinstall opencv-python.
