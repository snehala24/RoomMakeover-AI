#!/usr/bin/env python3
"""
USB Power Delivery Specification Parser - Main Orchestrator

This is the main entry point for the USB PD specification parsing system.
It coordinates all components to extract, parse, and validate PDF documents.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime

# Import our parsing modules
from .utils.pdf_extractor import PDFExtractor
from .parsers.toc_parser import TOCParser
from .parsers.document_parser import DocumentParser
from .utils.jsonl_generator import JSONLGenerator
from .validators.validation_report import ValidationReport

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('usb_pd_parser.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class USBPDSpecificationParser:
    """
    Main orchestrator class for USB PD specification parsing.
    
    Coordinates PDF extraction, ToC parsing, document section parsing,
    JSONL generation, and validation reporting.
    """
    
    def __init__(self, parser_version: str = "1.0.0"):
        """
        Initialize the USB PD specification parser.
        
        Args:
            parser_version: Version of the parsing system
        """
        self.parser_version = parser_version
        self.session_timestamp = datetime.now().isoformat()
        
        # Initialize components
        self.pdf_extractor: Optional[PDFExtractor] = None
        self.toc_parser: Optional[TOCParser] = None
        self.document_parser: Optional[DocumentParser] = None
        self.jsonl_generator: Optional[JSONLGenerator] = None
        self.validation_report: Optional[ValidationReport] = None
        
        # Parsing results
        self.parsing_results = {
            "document_info": None,
            "page_extractions": [],
            "toc_entries": [],
            "document_sections": [],
            "toc_stats": {},
            "document_stats": {},
            "validation_results": {},
            "generation_stats": {}
        }
        
        logger.info(f"USB PD Parser v{parser_version} initialized")
    
    def parse_pdf(self, pdf_path: str, output_dir: str = "output", 
                  doc_title: Optional[str] = None) -> dict:
        """
        Parse a USB PD specification PDF file completely.
        
        Args:
            pdf_path: Path to the PDF file
            output_dir: Directory for output files
            doc_title: Custom document title (auto-detected if None)
            
        Returns:
            Comprehensive parsing results dictionary
        """
        logger.info(f"Starting complete parsing of: {pdf_path}")
        
        try:
            # Step 1: Extract PDF content
            self._extract_pdf_content(pdf_path, doc_title)
            
            # Step 2: Parse Table of Contents
            self._parse_table_of_contents()
            
            # Step 3: Parse document sections
            self._parse_document_sections()
            
            # Step 4: Generate JSONL files
            self._generate_jsonl_files(output_dir)
            
            # Step 5: Validate and generate report
            self._validate_and_report(output_dir)
            
            # Step 6: Generate final summary
            summary = self._generate_parsing_summary()
            
            logger.info("Complete parsing finished successfully")
            return summary
            
        except Exception as e:
            logger.error(f"Parsing failed: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    def _extract_pdf_content(self, pdf_path: str, doc_title: Optional[str]):
        """Extract content from PDF file."""
        logger.info("Step 1: Extracting PDF content...")
        
        self.pdf_extractor = PDFExtractor(pdf_path)
        
        # Extract document metadata
        self.parsing_results["document_info"] = self.pdf_extractor.extract_document_info()
        
        # Use provided title or extracted title
        if doc_title:
            self.parsing_results["document_info"].title = doc_title
        
        # Extract all pages
        self.parsing_results["page_extractions"] = self.pdf_extractor.extract_all_pages()
        
        # Get extraction statistics
        extraction_stats = self.pdf_extractor.get_extraction_statistics()
        logger.info(f"PDF extraction completed: {extraction_stats['success_rate']:.1%} success rate")
    
    def _parse_table_of_contents(self):
        """Parse the Table of Contents from extracted pages."""
        logger.info("Step 2: Parsing Table of Contents...")
        
        doc_title = self.parsing_results["document_info"].title
        self.toc_parser = TOCParser(doc_title)
        
        # Find ToC pages
        toc_pages = self.pdf_extractor.find_table_of_contents_pages()
        
        if not toc_pages:
            logger.warning("No ToC pages automatically detected, using first 10 pages")
            toc_pages = list(range(1, min(11, len(self.parsing_results["page_extractions"]) + 1)))
        
        # Extract ToC text
        toc_text = self.pdf_extractor.get_page_range_text(toc_pages[0], toc_pages[-1])
        
        # Parse ToC entries
        self.parsing_results["toc_entries"] = self.toc_parser.parse_toc_text(toc_text)
        
        # Get ToC statistics
        self.parsing_results["toc_stats"] = self.toc_parser.get_parsing_statistics()
        
        # Validate ToC structure
        toc_warnings = self.toc_parser.validate_toc_structure()
        if toc_warnings:
            logger.warning(f"ToC validation warnings: {toc_warnings}")
        
        logger.info(f"ToC parsing completed: {len(self.parsing_results['toc_entries'])} entries found")
    
    def _parse_document_sections(self):
        """Parse full document sections based on ToC entries."""
        logger.info("Step 3: Parsing document sections...")
        
        doc_title = self.parsing_results["document_info"].title
        self.document_parser = DocumentParser(doc_title)
        
        # Parse document sections
        self.parsing_results["document_sections"] = self.document_parser.parse_document_sections(
            self.parsing_results["toc_entries"],
            self.parsing_results["page_extractions"]
        )
        
        # Get parsing statistics
        self.parsing_results["document_stats"] = self.document_parser.get_parsing_statistics()
        
        # Validate section mapping
        mapping_warnings = self.document_parser.validate_section_mapping(
            self.parsing_results["toc_entries"]
        )
        if mapping_warnings:
            logger.warning(f"Section mapping warnings: {mapping_warnings}")
        
        logger.info(f"Document parsing completed: {len(self.parsing_results['document_sections'])} sections parsed")
    
    def _generate_jsonl_files(self, output_dir: str):
        """Generate JSONL output files."""
        logger.info("Step 4: Generating JSONL files...")
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        doc_title = self.parsing_results["document_info"].title
        self.jsonl_generator = JSONLGenerator(doc_title, self.parser_version)
        
        generation_stats = {}
        
        # Generate ToC JSONL
        toc_stats = self.jsonl_generator.generate_toc_jsonl(
            self.parsing_results["toc_entries"],
            output_path / "usb_pd_toc.jsonl"
        )
        generation_stats["toc"] = toc_stats
        
        # Generate document sections JSONL
        doc_stats = self.jsonl_generator.generate_document_jsonl(
            self.parsing_results["document_sections"],
            output_path / "usb_pd_spec.jsonl"
        )
        generation_stats["document"] = doc_stats
        
        # Generate metadata JSONL
        parsing_quality = {
            "overall_confidence": self.parsing_results["document_stats"].get("average_confidence", 0.0),
            "toc_match_rate": self.parsing_results["toc_stats"].get("success_rate", 0.0),
            "extraction_errors": (
                self.parsing_results["document_stats"].get("extraction_errors", 0) +
                self.parsing_results["toc_stats"].get("pattern_match_counts", {}).get("failed", 0)
            ),
            "warnings": []
        }
        
        metadata_stats = self.jsonl_generator.generate_metadata_jsonl(
            self.parsing_results["document_info"],
            self.parsing_results["toc_stats"],
            self.parsing_results["document_stats"],
            parsing_quality,
            output_path / "usb_pd_metadata.jsonl"
        )
        generation_stats["metadata"] = metadata_stats
        
        self.parsing_results["generation_stats"] = generation_stats
        logger.info("JSONL generation completed")
    
    def _validate_and_report(self, output_dir: str):
        """Validate parsing results and generate Excel report."""
        logger.info("Step 5: Validating results and generating report...")
        
        doc_title = self.parsing_results["document_info"].title
        self.validation_report = ValidationReport(doc_title)
        
        # Perform validation
        self.parsing_results["validation_results"] = self.validation_report.validate_parsing_results(
            self.parsing_results["toc_entries"],
            self.parsing_results["document_sections"]
        )
        
        # Generate Excel report
        output_path = Path(output_dir)
        excel_path = output_path / "validation_report.xlsx"
        
        report_stats = self.validation_report.generate_excel_report(str(excel_path))
        self.parsing_results["validation_results"]["report_stats"] = report_stats
        
        # Log validation summary
        summary = self.validation_report.get_validation_summary()
        logger.info(f"Validation completed: {summary['status']} ({summary['overall_match_rate']:.1%} match rate)")
    
    def _generate_parsing_summary(self) -> dict:
        """Generate a comprehensive parsing summary."""
        logger.info("Step 6: Generating final summary...")
        
        # Calculate overall success metrics
        toc_success = len(self.parsing_results["toc_entries"]) > 0
        doc_success = len(self.parsing_results["document_sections"]) > 0
        jsonl_success = all(
            stats.get("successfully_written", 0) > 0 
            for stats in self.parsing_results["generation_stats"].values()
        )
        validation_success = self.parsing_results["validation_results"].get("summary", {}).get("status", "Unknown") != "Poor"
        
        overall_success = toc_success and doc_success and jsonl_success and validation_success
        
        # Calculate overall accuracy
        match_rate = self.parsing_results["validation_results"].get("summary", {}).get("overall_match_rate", 0.0)
        confidence = self.parsing_results["document_stats"].get("average_confidence", 0.0)
        overall_accuracy = (match_rate + confidence) / 2
        
        summary = {
            "success": overall_success,
            "accuracy": overall_accuracy,
            "parser_version": self.parser_version,
            "session_timestamp": self.session_timestamp,
            "document_info": {
                "title": self.parsing_results["document_info"].title,
                "total_pages": self.parsing_results["document_info"].total_pages,
                "file_size": self.parsing_results["document_info"].file_size
            },
            "parsing_results": {
                "toc_entries_found": len(self.parsing_results["toc_entries"]),
                "document_sections_parsed": len(self.parsing_results["document_sections"]),
                "total_word_count": self.parsing_results["document_stats"].get("total_word_count", 0),
                "total_tables": self.parsing_results["document_stats"].get("total_tables", 0),
                "total_figures": self.parsing_results["document_stats"].get("total_figures", 0)
            },
            "quality_metrics": {
                "overall_match_rate": match_rate,
                "average_confidence": confidence,
                "validation_status": self.parsing_results["validation_results"].get("summary", {}).get("status", "Unknown"),
                "missing_sections": self.parsing_results["validation_results"].get("statistics", {}).get("missing_sections_count", 0),
                "quality_issues": self.parsing_results["validation_results"].get("statistics", {}).get("quality_issues_count", 0)
            },
            "output_files": {
                "toc_jsonl": "usb_pd_toc.jsonl",
                "document_jsonl": "usb_pd_spec.jsonl", 
                "metadata_jsonl": "usb_pd_metadata.jsonl",
                "validation_report": "validation_report.xlsx"
            }
        }
        
        logger.info(f"Parsing summary: {overall_accuracy:.1%} overall accuracy, {match_rate:.1%} match rate")
        return summary
    
    def generate_sample_files(self, output_dir: str = "sample_output") -> dict:
        """
        Generate sample JSONL files for demonstration purposes.
        
        Args:
            output_dir: Directory to write sample files
            
        Returns:
            Sample generation statistics
        """
        logger.info("Generating sample JSONL files...")
        
        self.jsonl_generator = JSONLGenerator("USB Power Delivery Specification Rev 3.1", self.parser_version)
        
        try:
            sample_stats = self.jsonl_generator.generate_sample_files(output_dir)
            logger.info(f"Sample files generated in: {sample_stats['output_directory']}")
            return sample_stats
        except Exception as e:
            logger.error(f"Failed to generate sample files: {e}")
            return {"success": False, "error": str(e)}

def create_argument_parser():
    """Create command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="USB Power Delivery Specification Parser",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Parse a PDF file
  python -m usb_pd_parser.main parse document.pdf
  
  # Parse with custom output directory
  python -m usb_pd_parser.main parse document.pdf --output ./results
  
  # Generate sample files
  python -m usb_pd_parser.main sample --output ./samples
  
  # Parse with custom document title
  python -m usb_pd_parser.main parse document.pdf --title "USB PD Spec v3.1"
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Parse command
    parse_parser = subparsers.add_parser('parse', help='Parse a USB PD specification PDF')
    parse_parser.add_argument('pdf_file', help='Path to the PDF file to parse')
    parse_parser.add_argument('--output', '-o', default='output', 
                             help='Output directory for results (default: output)')
    parse_parser.add_argument('--title', '-t', 
                             help='Custom document title (auto-detected if not provided)')
    parse_parser.add_argument('--verbose', '-v', action='store_true',
                             help='Enable verbose logging')
    
    # Sample command
    sample_parser = subparsers.add_parser('sample', help='Generate sample JSONL files')
    sample_parser.add_argument('--output', '-o', default='sample_output',
                              help='Output directory for sample files (default: sample_output)')
    sample_parser.add_argument('--verbose', '-v', action='store_true',
                              help='Enable verbose logging')
    
    return parser

def main():
    """Main entry point for the command-line interface."""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Configure logging level
    if getattr(args, 'verbose', False):
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Initialize parser
        usb_pd_parser = USBPDSpecificationParser()
        
        if args.command == 'parse':
            # Validate PDF file exists
            pdf_path = Path(args.pdf_file)
            if not pdf_path.exists():
                logger.error(f"PDF file not found: {pdf_path}")
                return 1
            
            # Parse the PDF
            result = usb_pd_parser.parse_pdf(
                str(pdf_path),
                args.output,
                args.title
            )
            
            if result.get('success', False):
                print(f"\n✅ Parsing completed successfully!")
                print(f"📊 Overall accuracy: {result['accuracy']:.1%}")
                print(f"📄 ToC entries: {result['parsing_results']['toc_entries_found']}")
                print(f"📑 Document sections: {result['parsing_results']['document_sections_parsed']}")
                print(f"📁 Output directory: {args.output}")
                return 0
            else:
                print(f"\n❌ Parsing failed: {result.get('error', 'Unknown error')}")
                return 1
        
        elif args.command == 'sample':
            # Generate sample files
            result = usb_pd_parser.generate_sample_files(args.output)
            
            if result.get('toc_file_stats', {}).get('successfully_written', 0) > 0:
                print(f"\n✅ Sample files generated successfully!")
                print(f"📁 Output directory: {result['output_directory']}")
                print(f"📄 Files created: usb_pd_toc.jsonl, usb_pd_spec.jsonl, usb_pd_metadata.jsonl")
                return 0
            else:
                print(f"\n❌ Sample generation failed: {result.get('error', 'Unknown error')}")
                return 1
        
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())