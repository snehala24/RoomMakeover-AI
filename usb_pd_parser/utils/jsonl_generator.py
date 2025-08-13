#!/usr/bin/env python3
"""
JSONL Generator for USB PD Specification Parser

This module provides utilities to convert parsed ToC entries, document sections,
and metadata into structured JSONL format with schema validation.
"""

import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import jsonschema

from ..parsers.toc_parser import TOCEntry
from ..parsers.document_parser import DocumentSection
from ..utils.pdf_extractor import DocumentInfo, PageExtraction

logger = logging.getLogger(__name__)

class JSONLGenerator:
    """
    Comprehensive JSONL generator for USB PD specification parsing results.
    
    Converts parsed data structures to JSONL format with schema validation
    and generates multiple output files for different data types.
    """
    
    def __init__(self, doc_title: str = "USB PD Specification", 
                 parser_version: str = "1.0.0"):
        """
        Initialize the JSONL generator.
        
        Args:
            doc_title: Document title for metadata
            parser_version: Version of the parsing system
        """
        self.doc_title = doc_title
        self.parser_version = parser_version
        self.generation_timestamp = datetime.now().isoformat()
        
        # Load JSON schemas for validation
        self._load_schemas()
    
    def _load_schemas(self):
        """Load JSON schemas for validation."""
        try:
            schema_dir = Path(__file__).parent.parent / "schemas"
            
            with open(schema_dir / "toc_schema.json", 'r') as f:
                self.toc_schema = json.load(f)
            
            with open(schema_dir / "document_schema.json", 'r') as f:
                self.document_schema = json.load(f)
            
            with open(schema_dir / "metadata_schema.json", 'r') as f:
                self.metadata_schema = json.load(f)
                
            logger.info("Successfully loaded JSON schemas for validation")
            
        except Exception as e:
            logger.error(f"Failed to load JSON schemas: {e}")
            # Set empty schemas to avoid validation
            self.toc_schema = {}
            self.document_schema = {}
            self.metadata_schema = {}
    
    def generate_toc_jsonl(self, toc_entries: List[TOCEntry], 
                          output_path: str) -> Dict[str, Any]:
        """
        Generate JSONL file for Table of Contents entries.
        
        Args:
            toc_entries: List of parsed ToC entries
            output_path: Path to output JSONL file
            
        Returns:
            Generation statistics and validation results
        """
        logger.info(f"Generating ToC JSONL for {len(toc_entries)} entries")
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        stats = {
            "total_entries": len(toc_entries),
            "successfully_written": 0,
            "validation_errors": 0,
            "validation_warnings": []
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for entry in toc_entries:
                try:
                    # Convert to dictionary
                    entry_dict = self._toc_entry_to_dict(entry)
                    
                    # Validate against schema
                    if self.toc_schema:
                        validation_result = self._validate_entry(entry_dict, self.toc_schema)
                        if not validation_result["valid"]:
                            stats["validation_errors"] += 1
                            stats["validation_warnings"].extend(validation_result["errors"])
                            logger.warning(f"Validation failed for ToC entry {entry.section_id}: {validation_result['errors']}")
                    
                    # Write to file
                    f.write(json.dumps(entry_dict, ensure_ascii=False) + '\n')
                    stats["successfully_written"] += 1
                    
                except Exception as e:
                    logger.error(f"Failed to write ToC entry {entry.section_id}: {e}")
                    stats["validation_errors"] += 1
                    stats["validation_warnings"].append(f"Entry {entry.section_id}: {str(e)}")
        
        logger.info(f"ToC JSONL generation completed: {stats['successfully_written']}/{stats['total_entries']} entries written")
        return stats
    
    def generate_document_jsonl(self, document_sections: List[DocumentSection], 
                              output_path: str) -> Dict[str, Any]:
        """
        Generate JSONL file for document sections.
        
        Args:
            document_sections: List of parsed document sections
            output_path: Path to output JSONL file
            
        Returns:
            Generation statistics and validation results
        """
        logger.info(f"Generating document JSONL for {len(document_sections)} sections")
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        stats = {
            "total_sections": len(document_sections),
            "successfully_written": 0,
            "validation_errors": 0,
            "validation_warnings": [],
            "content_size_stats": {
                "total_chars": 0,
                "total_words": 0,
                "avg_section_size": 0
            }
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for section in document_sections:
                try:
                    # Convert to dictionary
                    section_dict = self._document_section_to_dict(section)
                    
                    # Update content statistics
                    stats["content_size_stats"]["total_chars"] += len(section.content)
                    stats["content_size_stats"]["total_words"] += section.word_count
                    
                    # Validate against schema
                    if self.document_schema:
                        validation_result = self._validate_entry(section_dict, self.document_schema)
                        if not validation_result["valid"]:
                            stats["validation_errors"] += 1
                            stats["validation_warnings"].extend(validation_result["errors"])
                            logger.warning(f"Validation failed for section {section.section_id}: {validation_result['errors']}")
                    
                    # Write to file
                    f.write(json.dumps(section_dict, ensure_ascii=False) + '\n')
                    stats["successfully_written"] += 1
                    
                except Exception as e:
                    logger.error(f"Failed to write document section {section.section_id}: {e}")
                    stats["validation_errors"] += 1
                    stats["validation_warnings"].append(f"Section {section.section_id}: {str(e)}")
        
        # Calculate average section size
        if stats["successfully_written"] > 0:
            stats["content_size_stats"]["avg_section_size"] = (
                stats["content_size_stats"]["total_chars"] / stats["successfully_written"]
            )
        
        logger.info(f"Document JSONL generation completed: {stats['successfully_written']}/{stats['total_sections']} sections written")
        return stats
    
    def generate_metadata_jsonl(self, doc_info: DocumentInfo,
                               toc_stats: Dict, document_stats: Dict,
                               parsing_quality: Dict, output_path: str) -> Dict[str, Any]:
        """
        Generate JSONL file for document metadata and parsing statistics.
        
        Args:
            doc_info: Document information from PDF extraction
            toc_stats: Statistics from ToC parsing
            document_stats: Statistics from document parsing
            parsing_quality: Quality metrics and warnings
            output_path: Path to output JSONL file
            
        Returns:
            Generation statistics and validation results
        """
        logger.info("Generating metadata JSONL")
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        stats = {
            "metadata_entries": 1,
            "successfully_written": 0,
            "validation_errors": 0,
            "validation_warnings": []
        }
        
        try:
            # Create metadata entry
            metadata_dict = self._create_metadata_dict(doc_info, toc_stats, document_stats, parsing_quality)
            
            # Validate against schema
            if self.metadata_schema:
                validation_result = self._validate_entry(metadata_dict, self.metadata_schema)
                if not validation_result["valid"]:
                    stats["validation_errors"] += 1
                    stats["validation_warnings"].extend(validation_result["errors"])
                    logger.warning(f"Metadata validation failed: {validation_result['errors']}")
            
            # Write to file
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(json.dumps(metadata_dict, ensure_ascii=False) + '\n')
            
            stats["successfully_written"] = 1
            logger.info("Metadata JSONL generation completed successfully")
            
        except Exception as e:
            logger.error(f"Failed to write metadata: {e}")
            stats["validation_errors"] += 1
            stats["validation_warnings"].append(f"Metadata generation failed: {str(e)}")
        
        return stats
    
    def _toc_entry_to_dict(self, entry: TOCEntry) -> Dict[str, Any]:
        """
        Convert a TOCEntry to dictionary format for JSONL.
        
        Args:
            entry: TOCEntry object
            
        Returns:
            Dictionary representation
        """
        return {
            "doc_title": self.doc_title,
            "section_id": entry.section_id,
            "title": entry.title,
            "page": entry.page,
            "level": entry.level,
            "parent_id": entry.parent_id,
            "full_path": entry.full_path,
            "tags": entry.tags
        }
    
    def _document_section_to_dict(self, section: DocumentSection) -> Dict[str, Any]:
        """
        Convert a DocumentSection to dictionary format for JSONL.
        
        Args:
            section: DocumentSection object
            
        Returns:
            Dictionary representation
        """
        return {
            "doc_title": self.doc_title,
            "section_id": section.section_id,
            "title": section.title,
            "page_start": section.page_start,
            "page_end": section.page_end,
            "level": section.level,
            "parent_id": section.parent_id,
            "full_path": section.full_path,
            "content": section.content,
            "content_type": section.content_type,
            "has_tables": section.has_tables,
            "has_figures": section.has_figures,
            "table_count": section.table_count,
            "figure_count": section.figure_count,
            "word_count": section.word_count,
            "tags": section.tags,
            "confidence_score": section.confidence_score,
            "extraction_notes": section.extraction_notes
        }
    
    def _create_metadata_dict(self, doc_info: DocumentInfo, toc_stats: Dict,
                            document_stats: Dict, parsing_quality: Dict) -> Dict[str, Any]:
        """
        Create metadata dictionary for JSONL output.
        
        Args:
            doc_info: Document information
            toc_stats: ToC parsing statistics
            document_stats: Document parsing statistics
            parsing_quality: Quality metrics
            
        Returns:
            Metadata dictionary
        """
        return {
            "doc_title": doc_info.title if doc_info else self.doc_title,
            "doc_version": getattr(doc_info, 'doc_version', None),
            "doc_date": getattr(doc_info, 'doc_date', None),
            "total_pages": doc_info.total_pages if doc_info else 0,
            "parsing_timestamp": self.generation_timestamp,
            "parser_version": self.parser_version,
            "toc_statistics": {
                "total_sections": toc_stats.get("total_entries", 0),
                "max_level": toc_stats.get("max_level", 0),
                "level_distribution": self._convert_level_distribution(
                    toc_stats.get("level_distribution", {})
                )
            },
            "content_statistics": {
                "total_sections_parsed": document_stats.get("total_sections_parsed", 0),
                "total_tables": document_stats.get("total_tables", 0),
                "total_figures": document_stats.get("total_figures", 0),
                "total_word_count": document_stats.get("total_word_count", 0),
                "content_type_distribution": {
                    "text": document_stats.get("content_type_distribution", {}).get("text", 0),
                    "table": document_stats.get("content_type_distribution", {}).get("table", 0),
                    "figure": document_stats.get("content_type_distribution", {}).get("figure", 0),
                    "code": document_stats.get("content_type_distribution", {}).get("code", 0),
                    "protocol": document_stats.get("content_type_distribution", {}).get("protocol", 0),
                    "state_machine": document_stats.get("content_type_distribution", {}).get("state_machine", 0),
                    "mixed": document_stats.get("content_type_distribution", {}).get("mixed", 0)
                }
            },
            "parsing_quality": {
                "overall_confidence": parsing_quality.get("overall_confidence", 0.0),
                "toc_match_rate": parsing_quality.get("toc_match_rate", 0.0),
                "extraction_errors": parsing_quality.get("extraction_errors", 0),
                "warnings": parsing_quality.get("warnings", [])
            },
            "file_info": {
                "filename": doc_info.pdf_path.name if hasattr(doc_info, 'pdf_path') else "unknown.pdf",
                "file_size": doc_info.file_size if doc_info else 0,
                "pdf_creator": doc_info.creator if doc_info else None,
                "pdf_version": doc_info.pdf_version if doc_info else None
            }
        }
    
    def _convert_level_distribution(self, level_dist: Dict) -> Dict[str, int]:
        """
        Convert level distribution to string keys for JSON schema compliance.
        
        Args:
            level_dist: Level distribution with integer keys
            
        Returns:
            Level distribution with string keys
        """
        return {str(k): v for k, v in level_dist.items()}
    
    def _validate_entry(self, entry_dict: Dict, schema: Dict) -> Dict[str, Any]:
        """
        Validate a dictionary entry against a JSON schema.
        
        Args:
            entry_dict: Dictionary to validate
            schema: JSON schema for validation
            
        Returns:
            Validation result with success status and error messages
        """
        try:
            jsonschema.validate(instance=entry_dict, schema=schema)
            return {"valid": True, "errors": []}
        except jsonschema.ValidationError as e:
            return {"valid": False, "errors": [str(e)]}
        except Exception as e:
            return {"valid": False, "errors": [f"Validation error: {str(e)}"]}
    
    def generate_sample_files(self, output_dir: str) -> Dict[str, Any]:
        """
        Generate sample JSONL files with example USB PD specification data.
        
        Args:
            output_dir: Directory to write sample files
            
        Returns:
            Generation statistics
        """
        logger.info("Generating sample JSONL files")
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Sample ToC entries
        sample_toc = self._create_sample_toc_data()
        toc_stats = self.generate_toc_jsonl(sample_toc, output_path / "usb_pd_toc.jsonl")
        
        # Sample document sections
        sample_sections = self._create_sample_document_data()
        doc_stats = self.generate_document_jsonl(sample_sections, output_path / "usb_pd_spec.jsonl")
        
        # Sample metadata
        sample_metadata_stats = {
            "total_entries": len(sample_toc),
            "max_level": 3,
            "level_distribution": {1: 5, 2: 8, 3: 12}
        }
        sample_doc_stats = {
            "total_sections_parsed": len(sample_sections),
            "total_tables": 15,
            "total_figures": 8,
            "total_word_count": 25000,
            "content_type_distribution": {"text": 10, "table": 3, "mixed": 2}
        }
        sample_quality = {
            "overall_confidence": 0.92,
            "toc_match_rate": 0.95,
            "extraction_errors": 2,
            "warnings": ["Minor formatting inconsistencies detected"]
        }
        
        # Create sample document info
        sample_doc_info = type('DocInfo', (), {
            'title': 'USB Power Delivery Specification Rev 3.1',
            'total_pages': 200,
            'file_size': 2500000,
            'creator': 'USB Implementers Forum',
            'pdf_version': '1.7'
        })()
        
        metadata_stats = self.generate_metadata_jsonl(
            sample_doc_info, sample_metadata_stats, sample_doc_stats,
            sample_quality, output_path / "usb_pd_metadata.jsonl"
        )
        
        return {
            "toc_file_stats": toc_stats,
            "document_file_stats": doc_stats,
            "metadata_file_stats": metadata_stats,
            "output_directory": str(output_path)
        }
    
    def _create_sample_toc_data(self) -> List[TOCEntry]:
        """Create sample ToC entries for demonstration."""
        sample_data = [
            ("1", "Introduction", 10, 1, None),
            ("1.1", "Scope", 10, 2, "1"),
            ("1.2", "References", 11, 2, "1"),
            ("2", "Overview", 15, 1, None),
            ("2.1", "USB Power Delivery Basics", 15, 2, "2"),
            ("2.1.1", "Power Delivery Source Operational Contracts", 16, 3, "2.1"),
            ("2.1.2", "Power Delivery Contract Negotiation", 18, 3, "2.1"),
            ("2.1.3", "Other Uses for Power Delivery", 20, 3, "2.1"),
            ("2.2", "Compatibility with Revision 2.0", 22, 2, "2"),
            ("2.3", "USB Power Delivery Capable Devices", 25, 2, "2"),
            ("3", "Architecture", 30, 1, None),
            ("3.1", "Protocol Layer", 30, 2, "3"),
            ("3.2", "Physical Layer", 35, 2, "3"),
            ("4", "Message Format", 40, 1, None),
            ("4.1", "Message Header", 40, 2, "4"),
            ("4.1.1", "Message Type", 41, 3, "4.1"),
            ("4.1.2", "Data Role", 42, 3, "4.1"),
            ("5", "Protocol State Machine", 50, 1, None),
            ("5.1", "Source States", 50, 2, "5"),
            ("5.2", "Sink States", 55, 2, "5"),
        ]
        
        entries = []
        for section_id, title, page, level, parent_id in sample_data:
            entry = TOCEntry(
                section_id=section_id,
                title=title,
                page=page,
                level=level,
                parent_id=parent_id,
                full_path=f"{section_id} {title}",
                tags=self._generate_sample_tags(title),
                confidence_score=0.9,
                raw_line=f"{section_id} {title} {'.' * 30} {page}"
            )
            entries.append(entry)
        
        return entries
    
    def _create_sample_document_data(self) -> List[DocumentSection]:
        """Create sample document sections for demonstration."""
        sections = []
        
        # Use the sample ToC data as a base
        toc_entries = self._create_sample_toc_data()
        
        for i, toc_entry in enumerate(toc_entries[:10]):  # Create sections for first 10 ToC entries
            content = self._generate_sample_content(toc_entry.title, toc_entry.level)
            
            section = DocumentSection(
                section_id=toc_entry.section_id,
                title=toc_entry.title,
                page_start=toc_entry.page,
                page_end=toc_entry.page + 1 if i < 9 else None,
                level=toc_entry.level,
                parent_id=toc_entry.parent_id,
                full_path=toc_entry.full_path,
                content=content,
                content_type=self._determine_sample_content_type(toc_entry.title),
                has_tables="table" in toc_entry.title.lower() or "format" in toc_entry.title.lower(),
                has_figures="architecture" in toc_entry.title.lower() or "state" in toc_entry.title.lower(),
                table_count=1 if "format" in toc_entry.title.lower() else 0,
                figure_count=1 if "architecture" in toc_entry.title.lower() else 0,
                word_count=len(content.split()),
                tags=toc_entry.tags,
                confidence_score=0.88,
                extraction_notes=[]
            )
            sections.append(section)
        
        return sections
    
    def _generate_sample_tags(self, title: str) -> List[str]:
        """Generate sample tags based on title content."""
        title_lower = title.lower()
        tags = []
        
        if "power" in title_lower or "delivery" in title_lower:
            tags.extend(["power", "delivery"])
        if "message" in title_lower or "format" in title_lower:
            tags.extend(["communication", "protocol"])
        if "state" in title_lower or "machine" in title_lower:
            tags.append("state_machine")
        if "architecture" in title_lower:
            tags.append("architecture")
        if "contract" in title_lower or "negotiation" in title_lower:
            tags.extend(["contracts", "negotiation"])
        
        return tags
    
    def _generate_sample_content(self, title: str, level: int) -> str:
        """Generate sample content based on section title and level."""
        base_content = f"This section covers {title.lower()}. "
        
        if level == 1:
            # Chapter-level content
            content = base_content + """This chapter provides a comprehensive overview of the concepts and mechanisms involved. 
            
            The USB Power Delivery specification defines a standard for power delivery over USB connections, 
            enabling higher power levels and more intelligent power management. This specification builds upon 
            previous USB standards while introducing new capabilities for modern devices.
            
            Key aspects covered in this chapter include fundamental concepts, operational principles, and 
            architectural considerations that form the foundation for understanding the detailed specifications 
            that follow."""
            
        elif level == 2:
            # Section-level content
            content = base_content + """This section provides detailed information about the specific mechanisms and requirements.
            
            The implementation of these features requires careful consideration of compatibility, performance, 
            and safety requirements. Various protocols and state machines work together to ensure reliable 
            power delivery while maintaining system integrity.
            
            Reference implementations and compliance requirements are specified to ensure interoperability 
            across different device types and manufacturers."""
            
        else:
            # Subsection-level content
            content = base_content + """This subsection details the specific implementation requirements and procedures.
            
            Detailed specifications include message formats, timing requirements, and error handling procedures. 
            These specifications ensure that implementations will be compatible and provide the expected functionality 
            across different system configurations."""
        
        return content
    
    def _determine_sample_content_type(self, title: str) -> str:
        """Determine content type for sample data based on title."""
        title_lower = title.lower()
        
        if "format" in title_lower or "header" in title_lower:
            return "table"
        elif "state" in title_lower and "machine" in title_lower:
            return "state_machine"
        elif "protocol" in title_lower:
            return "protocol"
        elif "architecture" in title_lower:
            return "mixed"
        else:
            return "text"