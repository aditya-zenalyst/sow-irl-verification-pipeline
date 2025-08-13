"""
Excel Validator Pipeline
A robust pipeline for validating, cleaning, and extracting data from Excel files
"""

from .pipeline import ExcelValidationPipeline
from .config import PipelineConfig

__version__ = "1.0.0"
__all__ = ["ExcelValidationPipeline", "PipelineConfig"]