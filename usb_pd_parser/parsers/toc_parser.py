#!/usr/bin/env python3
"""
Table of Contents Parser for USB PD Specification Documents

This module provides sophisticated ToC parsing with multiple regex patterns,
hierarchical structure detection, and robust error handling.
"""

import re
import logging
from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass
from collections import defaultdict

logger = logging.getLogger(__name__)

@dataclass
class TOCEntry:
    """Container for a Table of Contents entry."""
    section_id: str
    title: str
    page: int
    level: int
    parent_id: Optional[str]
    full_path: str
    tags: List[str]
    confidence_score: float
    raw_line: str

class TOCParser:
    """
    Advanced Table of Contents parser for technical specifications.
    
    Uses multiple regex patterns and heuristics to identify and parse
    ToC entries with high accuracy and robust error handling.
    """
    
    def __init__(self, doc_title: str = "USB PD Specification"):
        """
        Initialize the ToC parser.
        
        Args:
            doc_title: Document title for metadata
        """
        self.doc_title = doc_title
        self.toc_entries: List[TOCEntry] = []
        self.parsing_stats = {
            "total_lines_processed": 0,
            "entries_found": 0,
            "pattern_matches": defaultdict(int),
            "warnings": []
        }
        
        # Compile regex patterns for ToC entry detection
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile all regex patterns for ToC entry detection."""
        
        # Pattern 1: Standard numbered sections with page numbers
        # Examples: "2.1.2 Power Delivery Contract Negotiation ........... 53"
        #           "1 Introduction .................................... 10"
        self.pattern_standard = re.compile(
            r'^(\d+(?:\.\d+)*)\s+([^\.]+?)(?:\s*\.{2,}\s*|\s+)(\d+)\s*$',
            re.MULTILINE
        )
        
        # Pattern 2: Sections with varying spacing and separators
        # Examples: "2.1.2 Power Delivery Contract Negotiation   53"
        #           "2.1.2    Power Delivery Contract Negotiation 53"
        self.pattern_spaced = re.compile(
            r'^(\d+(?:\.\d+)*)\s+([^0-9]+?)\s+(\d+)\s*$',
            re.MULTILINE
        )
        
        # Pattern 3: Appendix and special sections
        # Examples: "Appendix A: Message Format ..................... 120"
        #           "Appendix B USB Type-C Cable and Connector ...... 150"
        self.pattern_appendix = re.compile(
            r'^(Appendix\s+[A-Z]+|APPENDIX\s+[A-Z]+):?\s+([^\.]+?)(?:\s*\.{2,}\s*|\s+)(\d+)\s*$',
            re.MULTILINE | re.IGNORECASE
        )
        
        # Pattern 4: Chapter-style entries
        # Examples: "Chapter 2: Power Delivery Overview ............ 25"
        self.pattern_chapter = re.compile(
            r'^(Chapter\s+\d+|CHAPTER\s+\d+):?\s+([^\.]+?)(?:\s*\.{2,}\s*|\s+)(\d+)\s*$',
            re.MULTILINE | re.IGNORECASE
        )
        
        # Pattern 5: Subsections with indentation
        # Examples: "    2.1.1 Introduction ........................ 54"
        self.pattern_indented = re.compile(
            r'^\s{2,}(\d+(?:\.\d+)+)\s+([^\.]+?)(?:\s*\.{2,}\s*|\s+)(\d+)\s*$',
            re.MULTILINE
        )
        
        # Pattern 6: Table and Figure lists
        # Examples: "Table 6-1: Message Header Format .............. 85"
        #           "Figure 2-1: USB PD Message Exchange ........... 30"
        self.pattern_table_figure = re.compile(
            r'^(Table|Figure)\s+(\d+(?:[-\.]\d+)*):?\s+([^\.]+?)(?:\s*\.{2,}\s*|\s+)(\d+)\s*$',
            re.MULTILINE | re.IGNORECASE
        )
        
        # Pattern 7: References and Bibliography
        # Examples: "References ..................................... 200"
        self.pattern_references = re.compile(
            r'^(References?|Bibliography|Index|Glossary)\s*(?:\s*\.{2,}\s*|\s+)(\d+)\s*$',
            re.MULTILINE | re.IGNORECASE
        )
        
        # All patterns for iteration
        self.all_patterns = [
            ("standard", self.pattern_standard),
            ("spaced", self.pattern_spaced),
            ("appendix", self.pattern_appendix),
            ("chapter", self.pattern_chapter),
            ("indented", self.pattern_indented),
            ("table_figure", self.pattern_table_figure),
            ("references", self.pattern_references)
        ]
    
    def parse_toc_text(self, text: str) -> List[TOCEntry]:
        """
        Parse Table of Contents from extracted text.
        
        Args:
            text: Raw text containing the ToC
            
        Returns:
            List of TOCEntry objects representing the parsed ToC
        """
        logger.info("Starting ToC parsing...")
        
        self.toc_entries = []
        self.parsing_stats["total_lines_processed"] = len(text.split('\n'))
        
        # Clean and preprocess text
        cleaned_text = self._preprocess_text(text)
        
        # Apply all patterns and collect matches
        all_matches = self._collect_pattern_matches(cleaned_text)
        
        # Filter and deduplicate matches
        filtered_matches = self._filter_matches(all_matches)
        
        # Create TOC entries from matches
        self.toc_entries = self._create_toc_entries(filtered_matches)
        
        # Post-process: assign levels and parent relationships
        self._assign_hierarchical_structure()
        
        # Calculate confidence scores
        self._calculate_confidence_scores()
        
        # Generate semantic tags
        self._generate_semantic_tags()
        
        self.parsing_stats["entries_found"] = len(self.toc_entries)
        logger.info(f"ToC parsing completed. Found {len(self.toc_entries)} entries.")
        
        return self.toc_entries
    
    def _preprocess_text(self, text: str) -> str:
        """
        Clean and preprocess ToC text for better parsing.
        
        Args:
            text: Raw ToC text
            
        Returns:
            Cleaned text
        """
        # Remove excessive whitespace but preserve structure
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Skip obviously non-ToC lines
            if self._is_noise_line(line):
                continue
            
            # Normalize whitespace but preserve indentation
            line = re.sub(r'\t', '    ', line)  # Convert tabs to spaces
            line = re.sub(r' {2,}', ' ', line.strip())  # Normalize multiple spaces
            
            if line.strip():
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def _is_noise_line(self, line: str) -> bool:
        """
        Check if a line is likely noise and not a ToC entry.
        
        Args:
            line: Text line to check
            
        Returns:
            True if the line should be ignored
        """
        line_stripped = line.strip().lower()
        
        # Skip empty lines
        if not line_stripped:
            return True
        
        # Skip obvious headers
        noise_patterns = [
            r'^table\s+of\s+contents\s*$',
            r'^contents\s*$',
            r'^page\s*$',
            r'^section\s*$',
            r'^\s*[-=_]{3,}\s*$',  # Separator lines
            r'^\s*\d+\s*$',        # Standalone page numbers
            r'^copyright',
            r'^all\s+rights\s+reserved',
            r'^usb\s+implementers\s+forum',
            r'^\s*revision\s+\d',
            r'^\s*version\s+\d',
        ]
        
        for pattern in noise_patterns:
            if re.match(pattern, line_stripped):
                return True
        
        return False
    
    def _collect_pattern_matches(self, text: str) -> List[Tuple[str, re.Match]]:
        """
        Apply all regex patterns and collect matches.
        
        Args:
            text: Preprocessed ToC text
            
        Returns:
            List of (pattern_name, match) tuples
        """
        all_matches = []
        
        for pattern_name, pattern in self.all_patterns:
            matches = pattern.finditer(text)
            for match in matches:
                all_matches.append((pattern_name, match))
                self.parsing_stats["pattern_matches"][pattern_name] += 1
        
        logger.info(f"Pattern matches: {dict(self.parsing_stats['pattern_matches'])}")
        return all_matches
    
    def _filter_matches(self, matches: List[Tuple[str, re.Match]]) -> List[Tuple[str, re.Match]]:
        """
        Filter and deduplicate pattern matches.
        
        Args:
            matches: List of (pattern_name, match) tuples
            
        Returns:
            Filtered list of matches
        """
        # Sort matches by position in text
        matches.sort(key=lambda x: x[1].start())
        
        filtered = []
        used_positions = set()
        
        for pattern_name, match in matches:
            # Check for overlapping matches
            start, end = match.span()
            if any(pos in range(start, end + 1) for pos in used_positions):
                continue
            
            # Validate the match makes sense
            if self._validate_match(pattern_name, match):
                filtered.append((pattern_name, match))
                used_positions.update(range(start, end + 1))
        
        logger.info(f"Filtered {len(filtered)} valid matches from {len(matches)} total")
        return filtered
    
    def _validate_match(self, pattern_name: str, match: re.Match) -> bool:
        """
        Validate that a regex match represents a valid ToC entry.
        
        Args:
            pattern_name: Name of the pattern that matched
            match: Regex match object
            
        Returns:
            True if the match is valid
        """
        try:
            groups = match.groups()
            
            # Check page number is reasonable
            if pattern_name in ["standard", "spaced", "appendix", "chapter", "indented"]:
                page_str = groups[-1]
                page_num = int(page_str)
                if page_num < 1 or page_num > 5000:  # Reasonable page range
                    return False
            
            # Check title is reasonable length
            if pattern_name in ["standard", "spaced", "appendix", "chapter", "indented"]:
                title = groups[-2].strip()
                if len(title) < 2 or len(title) > 200:
                    return False
                
                # Title shouldn't be mostly numbers or special characters
                alpha_chars = sum(1 for c in title if c.isalpha())
                if alpha_chars < len(title) * 0.3:
                    return False
            
            return True
            
        except (ValueError, IndexError) as e:
            logger.warning(f"Match validation failed: {e}")
            return False
    
    def _create_toc_entries(self, matches: List[Tuple[str, re.Match]]) -> List[TOCEntry]:
        """
        Create TOCEntry objects from validated matches.
        
        Args:
            matches: List of validated (pattern_name, match) tuples
            
        Returns:
            List of TOCEntry objects
        """
        entries = []
        
        for pattern_name, match in matches:
            entry = self._match_to_entry(pattern_name, match)
            if entry:
                entries.append(entry)
        
        # Sort by page number, then by section order
        entries.sort(key=lambda x: (x.page, self._section_sort_key(x.section_id)))
        
        return entries
    
    def _match_to_entry(self, pattern_name: str, match: re.Match) -> Optional[TOCEntry]:
        """
        Convert a regex match to a TOCEntry object.
        
        Args:
            pattern_name: Name of the pattern that matched
            match: Regex match object
            
        Returns:
            TOCEntry object or None if conversion fails
        """
        try:
            groups = match.groups()
            raw_line = match.group(0)
            
            if pattern_name in ["standard", "spaced", "indented"]:
                section_id = groups[0]
                title = groups[1].strip()
                page = int(groups[2])
                
            elif pattern_name in ["appendix", "chapter"]:
                section_id = groups[0].strip()
                title = groups[1].strip()
                page = int(groups[2])
                
            elif pattern_name == "table_figure":
                section_id = f"{groups[0]} {groups[1]}"
                title = groups[2].strip()
                page = int(groups[3])
                
            elif pattern_name == "references":
                section_id = "REF"
                title = groups[0].strip()
                page = int(groups[1])
                
            else:
                return None
            
            # Create full path
            full_path = f"{section_id} {title}" if section_id != "REF" else title
            
            return TOCEntry(
                section_id=section_id,
                title=title,
                page=page,
                level=0,  # Will be calculated later
                parent_id=None,  # Will be calculated later
                full_path=full_path,
                tags=[],  # Will be generated later
                confidence_score=0.0,  # Will be calculated later
                raw_line=raw_line
            )
            
        except (ValueError, IndexError) as e:
            logger.warning(f"Failed to create entry from match: {e}")
            return None
    
    def _assign_hierarchical_structure(self):
        """Assign hierarchical levels and parent relationships to ToC entries."""
        for entry in self.toc_entries:
            # Calculate level based on section ID structure
            entry.level = self._calculate_level(entry.section_id)
            
            # Find parent ID
            entry.parent_id = self._find_parent_id(entry.section_id)
    
    def _calculate_level(self, section_id: str) -> int:
        """
        Calculate the hierarchical level of a section.
        
        Args:
            section_id: Section identifier
            
        Returns:
            Hierarchical level (1-based)
        """
        # Handle special cases
        if section_id.startswith(("Appendix", "APPENDIX")):
            return 1
        if section_id.startswith(("Chapter", "CHAPTER")):
            return 1
        if section_id.startswith(("Table", "Figure")):
            return 3  # Usually subordinate to main sections
        if section_id == "REF":
            return 1
        
        # Count dots in numeric section IDs
        if re.match(r'^\d+(\.\d+)*$', section_id):
            return section_id.count('.') + 1
        
        # Default level
        return 1
    
    def _find_parent_id(self, section_id: str) -> Optional[str]:
        """
        Find the parent section ID for a given section.
        
        Args:
            section_id: Section identifier
            
        Returns:
            Parent section ID or None for top-level sections
        """
        # Handle special cases
        if section_id.startswith(("Appendix", "APPENDIX", "Chapter", "CHAPTER", "REF")):
            return None
        
        # For numeric section IDs, parent is the section with one less level
        if re.match(r'^\d+(\.\d+)+$', section_id):
            parts = section_id.split('.')
            if len(parts) > 1:
                return '.'.join(parts[:-1])
        
        # Top-level sections have no parent
        return None
    
    def _section_sort_key(self, section_id: str) -> Tuple:
        """
        Generate a sort key for section IDs to maintain proper order.
        
        Args:
            section_id: Section identifier
            
        Returns:
            Sort key tuple
        """
        # Handle special cases
        if section_id.startswith(("Appendix", "APPENDIX")):
            return (1000, section_id)
        if section_id == "REF":
            return (2000, section_id)
        if section_id.startswith(("Table", "Figure")):
            return (3000, section_id)
        
        # Handle numeric section IDs
        if re.match(r'^\d+(\.\d+)*$', section_id):
            parts = [int(x) for x in section_id.split('.')]
            # Pad to consistent length for sorting
            while len(parts) < 5:
                parts.append(0)
            return tuple(parts)
        
        # Default sorting
        return (5000, section_id)
    
    def _calculate_confidence_scores(self):
        """Calculate confidence scores for all ToC entries."""
        for entry in self.toc_entries:
            score = 0.7  # Base confidence
            
            # Reward proper section numbering
            if re.match(r'^\d+(\.\d+)*$', entry.section_id):
                score += 0.2
            
            # Reward reasonable page numbers in sequence
            score += min(0.1, max(0, 1 - abs(entry.page - 50) / 1000))  # Prefer mid-range pages
            
            # Reward proper title formatting
            if 5 <= len(entry.title) <= 100:
                score += 0.1
            
            # Penalty for very short or very long titles
            if len(entry.title) < 3 or len(entry.title) > 150:
                score -= 0.2
            
            entry.confidence_score = max(0.0, min(1.0, score))
    
    def _generate_semantic_tags(self):
        """Generate semantic tags for ToC entries based on title content."""
        # Common USB PD specification terms and their tags
        tag_mapping = {
            r'\b(power|delivery|pd)\b': ['power', 'delivery'],
            r'\b(message|communication|protocol)\b': ['communication', 'protocol'],
            r'\b(cable|connector|plug)\b': ['hardware', 'cable'],
            r'\b(voltage|current|electrical)\b': ['electrical'],
            r'\b(contract|negotiation|capability)\b': ['negotiation', 'contracts'],
            r'\b(source|sink|provider|consumer)\b': ['roles'],
            r'\b(state|machine|transition)\b': ['state_machine'],
            r'\b(table|format|structure)\b': ['data_structure'],
            r'\b(error|exception|fault)\b': ['error_handling'],
            r'\b(test|compliance|certification)\b': ['testing'],
            r'\b(security|authentication|encryption)\b': ['security'],
            r'\b(appendix|reference|index)\b': ['reference'],
        }
        
        for entry in self.toc_entries:
            title_lower = entry.title.lower()
            tags = set()
            
            for pattern, pattern_tags in tag_mapping.items():
                if re.search(pattern, title_lower):
                    tags.update(pattern_tags)
            
            # Add level-based tags
            if entry.level == 1:
                tags.add('chapter')
            elif entry.level >= 3:
                tags.add('subsection')
            
            entry.tags = sorted(list(tags))
    
    def get_parsing_statistics(self) -> Dict:
        """
        Get detailed statistics about the ToC parsing process.
        
        Returns:
            Dictionary containing parsing statistics
        """
        if not self.toc_entries:
            return {"error": "No ToC entries parsed"}
        
        level_distribution = defaultdict(int)
        confidence_scores = []
        
        for entry in self.toc_entries:
            level_distribution[entry.level] += 1
            confidence_scores.append(entry.confidence_score)
        
        avg_confidence = sum(confidence_scores) / len(confidence_scores)
        
        return {
            "total_entries": len(self.toc_entries),
            "level_distribution": dict(level_distribution),
            "max_level": max(level_distribution.keys()) if level_distribution else 0,
            "average_confidence": avg_confidence,
            "pattern_match_counts": dict(self.parsing_stats["pattern_matches"]),
            "lines_processed": self.parsing_stats["total_lines_processed"],
            "success_rate": len(self.toc_entries) / max(1, self.parsing_stats["total_lines_processed"]),
            "page_range": (
                min(entry.page for entry in self.toc_entries),
                max(entry.page for entry in self.toc_entries)
            ) if self.toc_entries else (0, 0)
        }
    
    def validate_toc_structure(self) -> List[str]:
        """
        Validate the parsed ToC structure for consistency and completeness.
        
        Returns:
            List of validation warnings
        """
        warnings = []
        
        # Check for missing parent sections
        section_ids = {entry.section_id for entry in self.toc_entries}
        for entry in self.toc_entries:
            if entry.parent_id and entry.parent_id not in section_ids:
                warnings.append(f"Missing parent section '{entry.parent_id}' for '{entry.section_id}'")
        
        # Check for page number sequence issues
        pages = [entry.page for entry in self.toc_entries]
        for i in range(1, len(pages)):
            if pages[i] < pages[i-1]:
                warnings.append(f"Page numbers out of sequence: {pages[i-1]} -> {pages[i]}")
        
        # Check for very low confidence scores
        low_confidence = [entry for entry in self.toc_entries if entry.confidence_score < 0.5]
        if low_confidence:
            warnings.append(f"{len(low_confidence)} entries have low confidence scores")
        
        # Check for duplicate section IDs
        section_id_counts = defaultdict(int)
        for entry in self.toc_entries:
            section_id_counts[entry.section_id] += 1
        
        duplicates = {sid: count for sid, count in section_id_counts.items() if count > 1}
        if duplicates:
            warnings.append(f"Duplicate section IDs found: {duplicates}")
        
        return warnings