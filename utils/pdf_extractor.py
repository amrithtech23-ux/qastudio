import PyMuPDF as fitz
import pdfplumber
import os

def extract_text_from_pdf(pdf_path):
    """
    Extract text from PDF file using multiple methods for better accuracy
    """
    text = ""
    
    try:
        # Method 1: PyMuPDF (faster, good for most PDFs)
        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            page = doc[page_num]
            text += page.get_text()
        doc.close()
        
        # If text is too short, try pdfplumber as backup
        if len(text.strip()) < 100:
            text = extract_with_pdfplumber(pdf_path)
            
    except Exception as e:
        print(f"PyMuPDF extraction failed: {e}")
        # Fallback to pdfplumber
        text = extract_with_pdfplumber(pdf_path)
    
    return text.strip()

def extract_with_pdfplumber(pdf_path):
    """
    Alternative extraction using pdfplumber (better for tables)
    """
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"pdfplumber extraction failed: {e}")
    
    return text.strip()

def extract_text_with_formatting(pdf_path):
    """
    Extract text with basic formatting information
    """
    text_blocks = []
    
    try:
        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            page = doc[page_num]
            blocks = page.get_text("blocks")
            for block in blocks:
                text_blocks.append({
                    'text': block[4],
                    'page': page_num + 1,
                    'bbox': block[:4]
                })
        doc.close()
    except Exception as e:
        print(f"Formatted extraction failed: {e}")
    
    return text_blocks
