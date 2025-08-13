#!/usr/bin/env python3
"""
PDF Text Extraction Utilities for USB PD Specification Parser

This module provides robust PDF text extraction using multiple libraries
for maximum reliability and accuracy in parsing technical specifications.
"""

import logging
import fitz  # PyMuPDF
import pdfplumber
import re
from typing import Dict, List, Tuple, Optional, Union
from dataclasses import dataclass
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PageExtraction:
    """Container for extracted page content and metadata."""
    page_number: int
    text: str
    tables: List[List[List[str]]]
    figures: List[Dict]
    confidence_score: float
    extraction_method: str
    warnings: List[str]

@dataclass
class DocumentInfo:
    """Container for document metadata."""
    title: str
    creator: Optional[str]
    producer: Optional[str]
    creation_date: Optional[str]
    modification_date: Optional[str]
    total_pages: int
    file_size: int
    pdf_version: Optional[str]

class PDFExtractor:
    """
    Robust PDF text extraction using multiple libraries and fallback mechanisms.
    
    This class uses both pdfplumber and PyMuPDF to extract text, tables, and metadata
    from PDF documents, with automatic fallback and quality scoring.
    """
    
    def __init__(self, pdf_path: Union[str, Path], use_ocr: bool = False):
        """
        Initialize the PDF extractor.
        
        Args:
            pdf_path: Path to the PDF file
            use_ocr: Whether to use OCR for image-based PDFs (not implemented yet)
        """
        self.pdf_path = Path(pdf_path)
        self.use_ocr = use_ocr
        self.doc_info: Optional[DocumentInfo] = None
        self.pages: List[PageExtraction] = []
        
        # Validate file exists
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {self.pdf_path}")
        
        logger.info(f"Initialized PDF extractor for: {self.pdf_path}")
    
    def extract_document_info(self) -> DocumentInfo:
        """Extract document metadata."""
        try:
            # Use PyMuPDF for metadata extraction
            with fitz.open(self.pdf_path) as doc:
                metadata = doc.metadata
                
                self.doc_info = DocumentInfo(
                    title=metadata.get('title', '').strip() or self.pdf_path.stem,
                    creator=metadata.get('creator'),
                    producer=metadata.get('producer'),
                    creation_date=metadata.get('creationDate'),
                    modification_date=metadata.get('modDate'),
                    total_pages=len(doc),
                    file_size=self.pdf_path.stat().st_size,
                    pdf_version=f"{doc.pdf_version()[0]}.{doc.pdf_version()[1]}"
                )
                
            logger.info(f"Extracted metadata: {self.doc_info.total_pages} pages")
            return self.doc_info
            
        except Exception as e:
            logger.error(f"Failed to extract document info: {e}")
            # Fallback with minimal info
            self.doc_info = DocumentInfo(
                title=self.pdf_path.stem,
                creator=None,
                producer=None,
                creation_date=None,
                modification_date=None,
                total_pages=0,
                file_size=self.pdf_path.stat().st_size,
                pdf_version=None
            )
            return self.doc_info
    
    def extract_page_with_pdfplumber(self, page_num: int) -> Optional[PageExtraction]:
        """
        Extract page content using pdfplumber.
        
        Args:
            page_num: Page number (0-indexed)
            
        Returns:
            PageExtraction object or None if extraction fails
        """
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                if page_num >= len(pdf.pages):
                    return None
                
                page = pdf.pages[page_num]
                text = page.extract_text() or ""
                
                # Extract tables
                tables = []
                try:
                    page_tables = page.extract_tables()
                    if page_tables:
                        tables = [table for table in page_tables if table]
                except Exception as e:
                    logger.warning(f"Table extraction failed for page {page_num + 1}: {e}")
                
                # Count figures (simple heuristic based on images)
                figures = []
                try:
                    images = page.images
                    figures = [{"type": "image", "bbox": img.get("bbox", [])} for img in images]
                except Exception as e:
                    logger.warning(f"Figure detection failed for page {page_num + 1}: {e}")
                
                # Calculate confidence based on text quality
                confidence = self._calculate_text_confidence(text)
                
                return PageExtraction(
                    page_number=page_num + 1,
                    text=text,
                    tables=tables,
                    figures=figures,
                    confidence_score=confidence,
                    extraction_method="pdfplumber",
                    warnings=[]
                )
                
        except Exception as e:
            logger.error(f"pdfplumber extraction failed for page {page_num + 1}: {e}")
            return None
    
    def extract_page_with_pymupdf(self, page_num: int) -> Optional[PageExtraction]:
        """
        Extract page content using PyMuPDF.
        
        Args:
            page_num: Page number (0-indexed)
            
        Returns:
            PageExtraction object or None if extraction fails
        """
        try:
            with fitz.open(self.pdf_path) as doc:
                if page_num >= len(doc):
                    return None
                
                page = doc[page_num]
                text = page.get_text()
                
                # Extract tables (basic detection)
                tables = []
                try:
                    # PyMuPDF table extraction is more complex, simplified here
                    table_data = page.find_tables()
                    if table_data:
                        for table in table_data:
                            try:
                                table_content = table.extract()
                                if table_content:
                                    tables.append(table_content)
                            except:
                                continue
                except Exception as e:
                    logger.warning(f"Table extraction failed for page {page_num + 1}: {e}")
                
                # Extract images/figures
                figures = []
                try:
                    image_list = page.get_images()
                    figures = [{"type": "image", "xref": img[0]} for img in image_list]
                except Exception as e:
                    logger.warning(f"Figure detection failed for page {page_num + 1}: {e}")
                
                # Calculate confidence
                confidence = self._calculate_text_confidence(text)
                
                return PageExtraction(
                    page_number=page_num + 1,
                    text=text,
                    tables=tables,
                    figures=figures,
                    confidence_score=confidence,
                    extraction_method="pymupdf",
                    warnings=[]
                )
                
        except Exception as e:
            logger.error(f"PyMuPDF extraction failed for page {page_num + 1}: {e}")
            return None
    
    def extract_page(self, page_num: int) -> PageExtraction:
        """
        Extract page content using the best available method.
        
        Args:
            page_num: Page number (0-indexed)
            
        Returns:
            PageExtraction object with the best quality extraction
        """
        extractions = []
        
        # Try pdfplumber first (generally better for text)
        pdfplumber_result = self.extract_page_with_pdfplumber(page_num)
        if pdfplumber_result:
            extractions.append(pdfplumber_result)
        
        # Try PyMuPDF as backup
        pymupdf_result = self.extract_page_with_pymupdf(page_num)
        if pymupdf_result:
            extractions.append(pymupdf_result)
        
        if not extractions:
            # Return empty extraction if all methods fail
            return PageExtraction(
                page_number=page_num + 1,
                text="",
                tables=[],
                figures=[],
                confidence_score=0.0,
                extraction_method="failed",
                warnings=["All extraction methods failed"]
            )
        
        # Select the best extraction based on confidence score and text length
        best_extraction = max(extractions, key=lambda x: (x.confidence_score, len(x.text)))
        
        # Merge table and figure data from all successful extractions
        all_tables = []
        all_figures = []
        for extraction in extractions:
            all_tables.extend(extraction.tables)
            all_figures.extend(extraction.figures)
        
        best_extraction.tables = all_tables
        best_extraction.figures = all_figures
        
        return best_extraction
    
    def extract_all_pages(self) -> List[PageExtraction]:
        """
        Extract content from all pages in the document.
        
        Returns:
            List of PageExtraction objects for all pages
        """
        if not self.doc_info:
            self.extract_document_info()
        
        self.pages = []
        total_pages = self.doc_info.total_pages if self.doc_info else 0
        
        logger.info(f"Starting extraction of {total_pages} pages...")
        
        for page_num in range(total_pages):
            page_extraction = self.extract_page(page_num)
            self.pages.append(page_extraction)
            
            if (page_num + 1) % 10 == 0:
                logger.info(f"Processed {page_num + 1}/{total_pages} pages")
        
        logger.info(f"Completed extraction of {len(self.pages)} pages")
        return self.pages
    
    def _calculate_text_confidence(self, text: str) -> float:
        """
        Calculate confidence score for extracted text quality.
        
        Args:
            text: Extracted text content
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        if not text or not text.strip():
            return 0.0
        
        score = 0.5  # Base score
        
        # Penalize for too many non-alphabetic characters
        alpha_ratio = sum(c.isalpha() for c in text) / len(text)
        score += min(alpha_ratio * 0.3, 0.3)
        
        # Reward proper spacing and punctuation
        word_count = len(text.split())
        if word_count > 0:
            avg_word_length = sum(len(word) for word in text.split()) / word_count
            if 3 <= avg_word_length <= 8:  # Reasonable word lengths
                score += 0.1
        
        # Penalize for excessive garbled characters
        garbled_chars = sum(1 for c in text if ord(c) > 127 and not c.isspace())
        if len(text) > 0:
            garbled_ratio = garbled_chars / len(text)
            score -= min(garbled_ratio * 0.5, 0.3)
        
        # Reward presence of common technical terms
        technical_terms = [
            'usb', 'power', 'delivery', 'specification', 'protocol',
            'voltage', 'current', 'cable', 'connector', 'message'
        ]
        text_lower = text.lower()
        term_matches = sum(1 for term in technical_terms if term in text_lower)
        score += min(term_matches * 0.02, 0.1)
        
        return max(0.0, min(1.0, score))
    
    def get_page_range_text(self, start_page: int, end_page: int) -> str:
        """
        Get concatenated text from a range of pages.
        
        Args:
            start_page: Starting page number (1-indexed)
            end_page: Ending page number (1-indexed, inclusive)
            
        Returns:
            Concatenated text from the specified page range
        """
        if not self.pages:
            self.extract_all_pages()
        
        # Convert to 0-indexed
        start_idx = start_page - 1
        end_idx = end_page - 1
        
        text_parts = []
        for i in range(start_idx, min(end_idx + 1, len(self.pages))):
            if i < len(self.pages):
                text_parts.append(self.pages[i].text)
        
        return "\n\n".join(text_parts)
    
    def find_table_of_contents_pages(self) -> List[int]:
        """
        Identify pages that likely contain the Table of Contents.
        
        Returns:
            List of page numbers (1-indexed) that likely contain ToC
        """
        if not self.pages:
            self.extract_all_pages()
        
        toc_pages = []
        toc_indicators = [
            r'\btable\s+of\s+contents\b',
            r'\bcontents\b',
            r'\btoc\b',
            r'^\s*\d+\.?\s+[A-Z]',  # Numbered sections
            r'^\s*\d+\.\d+\.?\s+',  # Subsections
        ]
        
        for page in self.pages:
            text_lower = page.text.lower()
            score = 0
            
            # Check for ToC indicators
            for pattern in toc_indicators:
                if re.search(pattern, text_lower, re.MULTILINE | re.IGNORECASE):
                    score += 1
            
            # Check for page number patterns at line ends
            page_num_pattern = r'\.\s*\d+\s*$'
            page_refs = len(re.findall(page_num_pattern, page.text, re.MULTILINE))
            if page_refs > 3:  # Multiple page references suggest ToC
                score += 2
            
            # ToC pages typically have shorter lines and less dense text
            lines = page.text.split('\n')
            short_lines = sum(1 for line in lines if 10 < len(line.strip()) < 80)
            if len(lines) > 0 and short_lines / len(lines) > 0.5:
                score += 1
            
            if score >= 2:
                toc_pages.append(page.page_number)
        
        logger.info(f"Identified potential ToC pages: {toc_pages}")
        return toc_pages
    
    def get_extraction_statistics(self) -> Dict:
        """
        Get statistics about the extraction process.
        
        Returns:
            Dictionary containing extraction statistics
        """
        if not self.pages:
            return {"error": "No pages extracted"}
        
        total_pages = len(self.pages)
        successful_extractions = sum(1 for p in self.pages if p.confidence_score > 0.3)
        total_text_length = sum(len(p.text) for p in self.pages)
        total_tables = sum(len(p.tables) for p in self.pages)
        total_figures = sum(len(p.figures) for p in self.pages)
        
        avg_confidence = sum(p.confidence_score for p in self.pages) / total_pages
        
        method_distribution = {}
        for page in self.pages:
            method = page.extraction_method
            method_distribution[method] = method_distribution.get(method, 0) + 1
        
        return {
            "total_pages": total_pages,
            "successful_extractions": successful_extractions,
            "success_rate": successful_extractions / total_pages if total_pages > 0 else 0,
            "average_confidence": avg_confidence,
            "total_text_length": total_text_length,
            "total_tables": total_tables,
            "total_figures": total_figures,
            "extraction_methods": method_distribution,
            "pages_with_warnings": sum(1 for p in self.pages if p.warnings)
        }