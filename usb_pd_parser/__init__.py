"""
USB Power Delivery Specification Parser

A comprehensive system for parsing USB PD specification PDFs and converting
them to structured JSONL format with validation and reporting.
"""

__version__ = "1.0.0"
__author__ = "USB PD Parser Team"

from .main import USBPDSpecificationParser

__all__ = ["USBPDSpecificationParser"]