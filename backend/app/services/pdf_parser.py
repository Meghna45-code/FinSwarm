import io
import logging
from typing import BinaryIO

logger = logging.getLogger("finswarm.pdf_parser")

def extract_pdf_layout_text(file_bytes: bytes) -> str:
    """
    Extracts text from PDF bytes while attempting to preserve
    column alignments and tabular grids using layout mode.
    """
    try:
        from pypdf import PdfReader
        
        # Load stream
        stream = io.BytesIO(file_bytes)
        reader = PdfReader(stream)
        
        full_text = []
        for idx, page in enumerate(reader.pages):
            # extraction_mode="layout" preserves column layout, grids, and spaces
            try:
                page_text = page.extract_text(extraction_mode="layout")
            except Exception:
                # Fallback to standard extraction
                page_text = page.extract_text()
                
            full_text.append(f"--- PAGE {idx+1} ---\n{page_text}")
            
        logger.info(f"Successfully parsed PDF. Pages extracted: {len(reader.pages)}")
        return "\n\n".join(full_text)
    except ImportError:
        logger.error("pypdf is not installed. PDF extraction failed.")
        return "Error: pypdf library is not installed on the server."
    except Exception as e:
        logger.exception(f"Failed to parse PDF: {e}")
        return f"Error extracting PDF: {str(e)}"
