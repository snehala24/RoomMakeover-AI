#!/usr/bin/env python3
"""
Document Section Parser for USB PD Specification Documents

This module provides comprehensive document parsing that maps ToC entries
to actual document content, extracts sections, and analyzes content types.
"""

import re
import logging
from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass
from collections import defaultdict
import math

from .toc_parser import TOCEntry
from ..utils.pdf_extractor import PageExtraction

logger = logging.getLogger(__name__)

@dataclass
class DocumentSection:
    """Container for a parsed document section with full content."""
    section_id: str
    title: str
    page_start: int
    page_end: Optional[int]
    level: int
    parent_id: Optional[str]
    full_path: str
    content: str
    content_type: str
    has_tables: bool
    has_figures: bool
    table_count: int
    figure_count: int
    word_count: int
    tags: List[str]
    confidence_score: float
    extraction_notes: List[str]

class DocumentParser:
    """
    Comprehensive document section parser for technical specifications.
    
    Maps Table of Contents entries to actual document content, extracts
    sections with proper boundaries, and analyzes content characteristics.
    """
    
    def __init__(self, doc_title: str = "USB PD Specification"):
        """
        Initialize the document parser.
        
        Args:
            doc_title: Document title for metadata
        """
        self.doc_title = doc_title
        self.document_sections: List[DocumentSection] = []
        self.toc_entries: List[TOCEntry] = []
        self.page_extractions: List[PageExtraction] = []
        self.parsing_stats = {
            "total_sections_attempted": 0,
            "sections_successfully_parsed": 0,
            "content_extraction_errors": 0,
            "boundary_detection_warnings": 0,
            "content_type_distribution": defaultdict(int),
            "warnings": []
        }
        
        # Compile patterns for content analysis
        self._compile_content_patterns()
    
    def _compile_content_patterns(self):
        """Compile regex patterns for content type detection and analysis."""
        
        # Table detection patterns
        self.table_patterns = [
            re.compile(r'Table\s+\d+[-.]?\d*:', re.IGNORECASE),
            re.compile(r'\|\s*[^|]+\s*\|', re.MULTILINE),  # Table rows with pipes
            re.compile(r'^\s*\+[-=]+\+', re.MULTILINE),    # ASCII table borders
            re.compile(r'^\s*[-]{3,}', re.MULTILINE),       # Table separators
        ]
        
        # Figure detection patterns
        self.figure_patterns = [
            re.compile(r'Figure\s+\d+[-.]?\d*:', re.IGNORECASE),
            re.compile(r'Diagram\s+\d+', re.IGNORECASE),
            re.compile(r'See\s+Figure\s+\d+', re.IGNORECASE),
            re.compile(r'shown\s+in\s+Figure', re.IGNORECASE),
        ]
        
        # Code/protocol patterns
        self.code_patterns = [
            re.compile(r'0x[0-9A-Fa-f]+', re.MULTILINE),   # Hex values
            re.compile(r'\b[01]{8,}\b', re.MULTILINE),      # Binary values
            re.compile(r'Byte\s+\d+:', re.IGNORECASE),
            re.compile(r'Bit\s+\d+:', re.IGNORECASE),
            re.compile(r'Field\s+Name\s*:\s*Value', re.IGNORECASE),
        ]
        
        # State machine patterns
        self.state_machine_patterns = [
            re.compile(r'State\s+\w+', re.IGNORECASE),
            re.compile(r'Transition\s+from', re.IGNORECASE),
            re.compile(r'when\s+.+\s+occurs', re.IGNORECASE),
            re.compile(r'go\s+to\s+state', re.IGNORECASE),
            re.compile(r'state\s+machine', re.IGNORECASE),
        ]
        
        # Section header patterns for boundary detection
        self.section_header_patterns = [
            re.compile(r'^\s*(\d+(?:\.\d+)*)\s+([A-Z][^.]*)', re.MULTILINE),
            re.compile(r'^(\d+(?:\.\d+)*)\s+([A-Z][A-Za-z\s]+)', re.MULTILINE),
            re.compile(r'^\s*(Chapter|CHAPTER)\s+\d+', re.MULTILINE | re.IGNORECASE),
            re.compile(r'^\s*(Appendix|APPENDIX)\s+[A-Z]', re.MULTILINE | re.IGNORECASE),
        ]
    
    def parse_document_sections(self, toc_entries: List[TOCEntry], 
                              page_extractions: List[PageExtraction]) -> List[DocumentSection]:
        """
        Parse full document sections based on ToC entries and page content.
        
        Args:
            toc_entries: List of ToC entries to map to content
            page_extractions: List of extracted page content
            
        Returns:
            List of DocumentSection objects with full content
        """
        logger.info(f"Starting document section parsing for {len(toc_entries)} ToC entries")
        
        self.toc_entries = toc_entries
        self.page_extractions = page_extractions
        self.document_sections = []
        
        # Create page number to content mapping
        page_content_map = {page.page_number: page for page in page_extractions}
        
        # Sort ToC entries by page number for sequential processing
        sorted_toc = sorted(toc_entries, key=lambda x: x.page)
        
        self.parsing_stats["total_sections_attempted"] = len(sorted_toc)
        
        for i, toc_entry in enumerate(sorted_toc):
            try:
                # Determine section boundaries
                start_page = toc_entry.page
                end_page = self._determine_section_end_page(toc_entry, sorted_toc, i)
                
                # Extract section content
                section_content = self._extract_section_content(
                    start_page, end_page, page_content_map, toc_entry
                )
                
                # Create document section
                doc_section = self._create_document_section(
                    toc_entry, start_page, end_page, section_content
                )
                
                if doc_section:
                    self.document_sections.append(doc_section)
                    self.parsing_stats["sections_successfully_parsed"] += 1
                
            except Exception as e:
                logger.error(f"Failed to parse section {toc_entry.section_id}: {e}")
                self.parsing_stats["content_extraction_errors"] += 1
                self.parsing_stats["warnings"].append(f"Section {toc_entry.section_id}: {str(e)}")
        
        logger.info(f"Document parsing completed. Successfully parsed {len(self.document_sections)} sections.")
        return self.document_sections
    
    def _determine_section_end_page(self, current_toc: TOCEntry, 
                                  sorted_toc: List[TOCEntry], 
                                  current_index: int) -> Optional[int]:
        """
        Determine the ending page for a section based on the next section's start.
        
        Args:
            current_toc: Current ToC entry
            sorted_toc: All ToC entries sorted by page
            current_index: Index of current entry in sorted list
            
        Returns:
            End page number or None if it's the last section
        """
        # Check if there's a next section at the same or higher level
        current_level = current_toc.level
        
        for j in range(current_index + 1, len(sorted_toc)):
            next_toc = sorted_toc[j]
            
            # If we find a section at same or higher level (lower number), that's our boundary
            if next_toc.level <= current_level:
                return next_toc.page - 1
            
            # For subsections, we continue until we find a peer or parent
            if next_toc.level > current_level:
                continue
        
        # If no next section found, this goes to the end
        return None
    
    def _extract_section_content(self, start_page: int, end_page: Optional[int],
                               page_content_map: Dict[int, PageExtraction],
                               toc_entry: TOCEntry) -> str:
        """
        Extract content for a section from the specified page range.
        
        Args:
            start_page: Starting page number
            end_page: Ending page number (None for last section)
            page_content_map: Mapping of page numbers to content
            toc_entry: ToC entry for context
            
        Returns:
            Extracted section content as text
        """
        content_parts = []
        actual_end = end_page or max(page_content_map.keys())
        
        for page_num in range(start_page, actual_end + 1):
            if page_num in page_content_map:
                page_content = page_content_map[page_num].text
                
                # For the first page, try to find the actual section start
                if page_num == start_page:
                    section_start = self._find_section_start_in_page(page_content, toc_entry)
                    if section_start:
                        page_content = section_start
                
                # For the last page, try to find where the section ends
                if page_num == actual_end and end_page is not None:
                    section_end = self._find_section_end_in_page(page_content, toc_entry)
                    if section_end:
                        page_content = section_end
                
                content_parts.append(page_content)
        
        return "\n\n".join(content_parts)
    
    def _find_section_start_in_page(self, page_content: str, toc_entry: TOCEntry) -> Optional[str]:
        """
        Find the actual start of a section within a page.
        
        Args:
            page_content: Full page content
            toc_entry: ToC entry to match
            
        Returns:
            Content from section start, or None if not found
        """
        # Look for section header patterns
        section_patterns = [
            rf'^\s*{re.escape(toc_entry.section_id)}\s+{re.escape(toc_entry.title[:20])}',
            rf'^\s*{re.escape(toc_entry.section_id)}\s+([A-Z][^.]*)',
            rf'^{re.escape(toc_entry.section_id)}\s'
        ]
        
        for pattern in section_patterns:
            match = re.search(pattern, page_content, re.MULTILINE | re.IGNORECASE)
            if match:
                return page_content[match.start():]
        
        # If no specific start found, return the full page
        return page_content
    
    def _find_section_end_in_page(self, page_content: str, toc_entry: TOCEntry) -> Optional[str]:
        """
        Find where a section ends within a page (before next section starts).
        
        Args:
            page_content: Full page content
            toc_entry: Current ToC entry
            
        Returns:
            Content up to section end, or None if not found
        """
        # Look for next section headers that would indicate this section ends
        for pattern in self.section_header_patterns:
            matches = list(pattern.finditer(page_content))
            if matches:
                # Return content up to the first match
                return page_content[:matches[0].start()]
        
        # If no clear end found, return the full page
        return page_content
    
    def _create_document_section(self, toc_entry: TOCEntry, start_page: int,
                               end_page: Optional[int], content: str) -> Optional[DocumentSection]:
        """
        Create a DocumentSection object from ToC entry and extracted content.
        
        Args:
            toc_entry: ToC entry information
            start_page: Starting page number
            end_page: Ending page number
            content: Extracted section content
            
        Returns:
            DocumentSection object or None if creation fails
        """
        try:
            # Analyze content characteristics
            content_analysis = self._analyze_content(content)
            
            # Calculate confidence score
            confidence = self._calculate_section_confidence(toc_entry, content, content_analysis)
            
            # Generate extraction notes
            notes = []
            if end_page is None:
                notes.append("Section continues to end of document")
            if content_analysis["low_quality_indicators"] > 0:
                notes.append("Content quality indicators suggest extraction issues")
            
            return DocumentSection(
                section_id=toc_entry.section_id,
                title=toc_entry.title,
                page_start=start_page,
                page_end=end_page,
                level=toc_entry.level,
                parent_id=toc_entry.parent_id,
                full_path=toc_entry.full_path,
                content=content,
                content_type=content_analysis["content_type"],
                has_tables=content_analysis["has_tables"],
                has_figures=content_analysis["has_figures"],
                table_count=content_analysis["table_count"],
                figure_count=content_analysis["figure_count"],
                word_count=content_analysis["word_count"],
                tags=toc_entry.tags.copy(),
                confidence_score=confidence,
                extraction_notes=notes
            )
            
        except Exception as e:
            logger.error(f"Failed to create document section for {toc_entry.section_id}: {e}")
            return None
    
    def _analyze_content(self, content: str) -> Dict:
        """
        Analyze content characteristics to determine type and features.
        
        Args:
            content: Section content text
            
        Returns:
            Dictionary with content analysis results
        """
        if not content or not content.strip():
            return {
                "content_type": "text",
                "has_tables": False,
                "has_figures": False,
                "table_count": 0,
                "figure_count": 0,
                "word_count": 0,
                "low_quality_indicators": 1
            }
        
        # Count tables
        table_count = 0
        for pattern in self.table_patterns:
            table_count += len(pattern.findall(content))
        has_tables = table_count > 0
        
        # Count figures
        figure_count = 0
        for pattern in self.figure_patterns:
            figure_count += len(pattern.findall(content))
        has_figures = figure_count > 0
        
        # Count code/protocol indicators
        code_indicators = 0
        for pattern in self.code_patterns:
            code_indicators += len(pattern.findall(content))
        
        # Count state machine indicators
        state_machine_indicators = 0
        for pattern in self.state_machine_patterns:
            state_machine_indicators += len(pattern.findall(content))
        
        # Calculate word count (approximate)
        words = re.findall(r'\b\w+\b', content)
        word_count = len(words)
        
        # Determine content type
        content_type = self._determine_content_type(
            has_tables, has_figures, code_indicators, 
            state_machine_indicators, word_count
        )
        
        # Quality indicators
        low_quality_indicators = 0
        if word_count < 10:
            low_quality_indicators += 1
        if len(content.strip()) < 50:
            low_quality_indicators += 1
        
        # Check for garbled text
        non_ascii_ratio = sum(1 for c in content if ord(c) > 127) / max(1, len(content))
        if non_ascii_ratio > 0.1:
            low_quality_indicators += 1
        
        return {
            "content_type": content_type,
            "has_tables": has_tables,
            "has_figures": has_figures,
            "table_count": table_count,
            "figure_count": figure_count,
            "word_count": word_count,
            "code_indicators": code_indicators,
            "state_machine_indicators": state_machine_indicators,
            "low_quality_indicators": low_quality_indicators
        }
    
    def _determine_content_type(self, has_tables: bool, has_figures: bool,
                              code_indicators: int, state_machine_indicators: int,
                              word_count: int) -> str:
        """
        Determine the primary content type of a section.
        
        Args:
            has_tables: Whether section contains tables
            has_figures: Whether section contains figures
            code_indicators: Number of code/protocol indicators
            state_machine_indicators: Number of state machine indicators
            word_count: Total word count
            
        Returns:
            Content type string
        """
        # Count different content indicators
        type_scores = {
            "table": 3 if has_tables else 0,
            "figure": 3 if has_figures else 0,
            "code": min(code_indicators, 5),
            "protocol": min(code_indicators, 5),
            "state_machine": min(state_machine_indicators * 2, 5),
            "text": min(word_count // 50, 5)  # Regular text baseline
        }
        
        # Special handling for mixed content
        active_types = [t for t, score in type_scores.items() if score > 2]
        if len(active_types) > 2:
            return "mixed"
        
        # Return the highest scoring type
        max_type = max(type_scores.items(), key=lambda x: x[1])
        return max_type[0]
    
    def _calculate_section_confidence(self, toc_entry: TOCEntry, content: str,
                                    content_analysis: Dict) -> float:
        """
        Calculate confidence score for a parsed section.
        
        Args:
            toc_entry: Original ToC entry
            content: Extracted content
            content_analysis: Content analysis results
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        score = 0.6  # Base score
        
        # Reward sections with substantial content
        word_count = content_analysis["word_count"]
        if word_count > 50:
            score += min(0.2, word_count / 500)
        else:
            score -= 0.3  # Penalize very short sections
        
        # Reward proper content structure
        if content_analysis["low_quality_indicators"] == 0:
            score += 0.2
        else:
            score -= content_analysis["low_quality_indicators"] * 0.1
        
        # Reward content that matches expected section type
        title_lower = toc_entry.title.lower()
        content_type = content_analysis["content_type"]
        
        type_title_matches = {
            "table": ["table", "format", "structure"],
            "figure": ["figure", "diagram", "illustration"],
            "protocol": ["protocol", "message", "communication"],
            "state_machine": ["state", "machine", "transition"],
            "code": ["format", "encoding", "field"]
        }
        
        if content_type in type_title_matches:
            for keyword in type_title_matches[content_type]:
                if keyword in title_lower:
                    score += 0.1
                    break
        
        # Use original ToC confidence as a factor
        score = (score + toc_entry.confidence_score) / 2
        
        return max(0.0, min(1.0, score))
    
    def get_parsing_statistics(self) -> Dict:
        """
        Get detailed statistics about the document parsing process.
        
        Returns:
            Dictionary containing parsing statistics
        """
        if not self.document_sections:
            return {"error": "No document sections parsed"}
        
        # Calculate statistics
        total_word_count = sum(section.word_count for section in self.document_sections)
        total_tables = sum(section.table_count for section in self.document_sections)
        total_figures = sum(section.figure_count for section in self.document_sections)
        
        confidence_scores = [section.confidence_score for section in self.document_sections]
        avg_confidence = sum(confidence_scores) / len(confidence_scores)
        
        # Content type distribution
        content_types = defaultdict(int)
        for section in self.document_sections:
            content_types[section.content_type] += 1
        
        # Level distribution
        level_distribution = defaultdict(int)
        for section in self.document_sections:
            level_distribution[section.level] += 1
        
        # Page coverage analysis
        pages_with_content = set()
        for section in self.document_sections:
            pages_with_content.add(section.page_start)
            if section.page_end:
                pages_with_content.update(range(section.page_start, section.page_end + 1))
        
        return {
            "total_sections_parsed": len(self.document_sections),
            "total_sections_attempted": self.parsing_stats["total_sections_attempted"],
            "success_rate": len(self.document_sections) / max(1, self.parsing_stats["total_sections_attempted"]),
            "average_confidence": avg_confidence,
            "total_word_count": total_word_count,
            "total_tables": total_tables,
            "total_figures": total_figures,
            "content_type_distribution": dict(content_types),
            "level_distribution": dict(level_distribution),
            "pages_with_content": len(pages_with_content),
            "extraction_errors": self.parsing_stats["content_extraction_errors"],
            "boundary_warnings": self.parsing_stats["boundary_detection_warnings"],
            "sections_with_notes": sum(1 for s in self.document_sections if s.extraction_notes)
        }
    
    def validate_section_mapping(self, toc_entries: List[TOCEntry]) -> List[str]:
        """
        Validate that document sections properly map to ToC entries.
        
        Args:
            toc_entries: Original ToC entries for comparison
            
        Returns:
            List of validation warnings
        """
        warnings = []
        
        # Create mapping for easy lookup
        toc_map = {entry.section_id: entry for entry in toc_entries}
        section_map = {section.section_id: section for section in self.document_sections}
        
        # Check for missing sections
        missing_sections = set(toc_map.keys()) - set(section_map.keys())
        if missing_sections:
            warnings.append(f"Missing document sections for ToC entries: {sorted(missing_sections)}")
        
        # Check for extra sections
        extra_sections = set(section_map.keys()) - set(toc_map.keys())
        if extra_sections:
            warnings.append(f"Found document sections not in ToC: {sorted(extra_sections)}")
        
        # Check for page number mismatches
        for section_id, section in section_map.items():
            if section_id in toc_map:
                toc_page = toc_map[section_id].page
                if section.page_start != toc_page:
                    warnings.append(f"Page mismatch for {section_id}: ToC={toc_page}, Section={section.page_start}")
        
        # Check for very low confidence scores
        low_confidence = [s for s in self.document_sections if s.confidence_score < 0.4]
        if low_confidence:
            warnings.append(f"{len(low_confidence)} sections have very low confidence scores")
        
        # Check for extremely short sections
        short_sections = [s for s in self.document_sections if s.word_count < 10]
        if short_sections:
            warnings.append(f"{len(short_sections)} sections have very little content")
        
        return warnings