"""
OCR Handler Module for Financial Due Diligence System
Handles extraction of text from scanned PDFs using OCR technology
"""

import os
import tempfile
from typing import List, Optional, Tuple
from pathlib import Path
import PyPDF2
from pdf2image import convert_from_path
import pytesseract
from PIL import Image
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OCRHandler:
    """
    Handles OCR operations for PDF documents including:
    - Converting PDF pages to images
    - Extracting text using OCR
    - Handling both regular and scanned PDFs
    """
    
    def __init__(self, dpi: int = 300, language: str = 'eng'):
        """
        Initialize OCR Handler
        
        Args:
            dpi: DPI for PDF to image conversion (higher = better quality but slower)
            language: OCR language (default: English)
        """
        self.dpi = dpi
        self.language = language
        self._check_tesseract_installation()
    
    def _check_tesseract_installation(self):
        """Check if Tesseract is installed"""
        try:
            pytesseract.get_tesseract_version()
            logger.info("Tesseract is installed and ready")
        except Exception as e:
            logger.error("Tesseract is not installed or not in PATH")
            logger.error("Please install Tesseract OCR:")
            logger.error("- macOS: brew install tesseract")
            logger.error("- Ubuntu: sudo apt-get install tesseract-ocr")
            logger.error("- Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki")
            raise RuntimeError("Tesseract OCR not found") from e
    
    def is_scanned_pdf(self, pdf_path: str) -> bool:
        """
        Check if a PDF is scanned (contains images) or has extractable text
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            True if PDF appears to be scanned, False if it has extractable text
        """
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Check first few pages for text
                pages_to_check = min(3, len(pdf_reader.pages))
                total_text_length = 0
                
                for i in range(pages_to_check):
                    page_text = pdf_reader.pages[i].extract_text()
                    total_text_length += len(page_text.strip())
                
                # If very little text is extracted, it's likely scanned
                # Threshold: less than 100 characters per page on average
                avg_text_per_page = total_text_length / pages_to_check
                is_scanned = avg_text_per_page < 100
                
                logger.info(f"PDF analysis: {'Scanned' if is_scanned else 'Text-based'} "
                          f"(avg {avg_text_per_page:.0f} chars/page)")
                
                return is_scanned
                
        except Exception as e:
            logger.error(f"Error checking PDF type: {e}")
            # If we can't determine, assume it might be scanned
            return True
    
    def pdf_to_images(self, pdf_path: str) -> List[Image.Image]:
        """
        Convert PDF pages to images
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of PIL Image objects
        """
        try:
            logger.info(f"Converting PDF to images at {self.dpi} DPI...")
            images = convert_from_path(pdf_path, dpi=self.dpi)
            logger.info(f"Converted {len(images)} pages to images")
            return images
        except Exception as e:
            logger.error(f"Error converting PDF to images: {e}")
            raise
    
    def extract_text_from_image(self, image: Image.Image, preprocess: bool = True) -> str:
        """
        Extract text from a single image using OCR
        
        Args:
            image: PIL Image object
            preprocess: Whether to preprocess image for better OCR
            
        Returns:
            Extracted text
        """
        try:
            if preprocess:
                # Basic image preprocessing for better OCR
                # Convert to grayscale if not already
                if image.mode != 'L':
                    image = image.convert('L')
            
            # Perform OCR
            text = pytesseract.image_to_string(image, lang=self.language)
            return text
            
        except Exception as e:
            logger.error(f"Error extracting text from image: {e}")
            return ""
    
    def extract_text_from_pdf(self, pdf_path: str, force_ocr: bool = False) -> Tuple[str, bool]:
        """
        Extract text from PDF, using OCR if necessary
        
        Args:
            pdf_path: Path to PDF file
            force_ocr: Force OCR even if PDF has extractable text
            
        Returns:
            Tuple of (extracted_text, used_ocr)
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        # First, try regular text extraction unless forced to use OCR
        if not force_ocr:
            try:
                with open(pdf_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    text = ""
                    
                    for page_num, page in enumerate(pdf_reader.pages):
                        page_text = page.extract_text()
                        if page_text:
                            text += f"\n--- Page {page_num + 1} ---\n"
                            text += page_text
                    
                    # Check if we got meaningful text
                    if len(text.strip()) > 100:
                        logger.info("Successfully extracted text using PyPDF2")
                        return text, False
                        
            except Exception as e:
                logger.warning(f"Regular text extraction failed: {e}")
        
        # If regular extraction failed or forced, use OCR
        logger.info("Using OCR to extract text from PDF...")
        return self._ocr_extract_pdf(pdf_path), True
    
    def _ocr_extract_pdf(self, pdf_path: str) -> str:
        """
        Extract text from PDF using OCR
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Extracted text
        """
        all_text = []
        
        try:
            # Convert PDF to images
            images = self.pdf_to_images(pdf_path)
            
            # Extract text from each page
            for page_num, image in enumerate(images, 1):
                logger.info(f"Processing page {page_num}/{len(images)}...")
                
                page_text = self.extract_text_from_image(image)
                
                if page_text.strip():
                    all_text.append(f"\n--- Page {page_num} (OCR) ---\n")
                    all_text.append(page_text)
                
                # Clear image from memory
                image.close()
            
            combined_text = "\n".join(all_text)
            logger.info(f"OCR extraction complete. Extracted {len(combined_text)} characters")
            
            return combined_text
            
        except Exception as e:
            logger.error(f"Error during OCR extraction: {e}")
            raise
    
    def extract_with_fallback(self, pdf_path: str) -> dict:
        """
        Extract text from PDF with automatic fallback to OCR if needed
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dictionary with extraction results
        """
        result = {
            "status": "success",
            "text": "",
            "method": "unknown",
            "page_count": 0,
            "character_count": 0,
            "used_ocr": False,
            "error": None
        }
        
        try:
            # Check if PDF is scanned
            is_scanned = self.is_scanned_pdf(pdf_path)
            
            # Extract text
            text, used_ocr = self.extract_text_from_pdf(pdf_path, force_ocr=is_scanned)
            
            # Get page count
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                page_count = len(pdf_reader.pages)
            
            result.update({
                "text": text,
                "method": "OCR" if used_ocr else "PyPDF2",
                "page_count": page_count,
                "character_count": len(text),
                "used_ocr": used_ocr
            })
            
        except Exception as e:
            result.update({
                "status": "error",
                "error": str(e)
            })
            logger.error(f"Extraction failed: {e}")
        
        return result


def test_ocr_handler():
    """Test function for OCR handler"""
    handler = OCRHandler()
    
    # Test with a sample PDF
    test_pdf = "Balance Sheet Crossways 15.pdf"
    
    if os.path.exists(test_pdf):
        print(f"Testing OCR handler with: {test_pdf}")
        
        # Check if it's scanned
        is_scanned = handler.is_scanned_pdf(test_pdf)
        print(f"Is scanned PDF: {is_scanned}")
        
        # Extract text
        result = handler.extract_with_fallback(test_pdf)
        
        print(f"\nExtraction Results:")
        print(f"Status: {result['status']}")
        print(f"Method: {result['method']}")
        print(f"Pages: {result['page_count']}")
        print(f"Characters extracted: {result['character_count']}")
        print(f"Used OCR: {result['used_ocr']}")
        
        if result['status'] == 'success':
            print(f"\nFirst 500 characters:")
            print(result['text'][:500])
        else:
            print(f"Error: {result['error']}")
    else:
        print(f"Test PDF not found: {test_pdf}")


if __name__ == "__main__":
    test_ocr_handler()