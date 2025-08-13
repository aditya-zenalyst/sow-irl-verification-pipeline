"""
Configuration for the Excel validation pipeline
"""

import os
from pathlib import Path
from typing import Optional, Any
import logging


class PipelineConfig:
    """Configuration settings for the validation pipeline"""
    
    def __init__(self, **kwargs):
        """Initialize configuration with defaults and overrides"""
        
        # Output settings
        self.output_dir = kwargs.get('output_dir', Path('validation_output'))
        
        # Logging settings
        self.log_level = kwargs.get('log_level', logging.INFO)
        self.log_to_file = kwargs.get('log_to_file', True)
        
        # Processing settings
        self.max_workers = kwargs.get('max_workers', os.cpu_count() or 4)
        self.use_multiprocessing = kwargs.get('use_multiprocessing', False)
        self.file_timeout = kwargs.get('file_timeout', 300)  # 5 minutes per file
        
        # Structure detection settings
        self.max_scan_rows = kwargs.get('max_scan_rows', 20)
        self.max_scan_cols = kwargs.get('max_scan_cols', 20)
        self.min_data_density = kwargs.get('min_data_density', 0.3)
        self.header_confidence_threshold = kwargs.get('header_confidence_threshold', 0.7)
        
        # Data cleaning settings
        self.replace_missing_with = kwargs.get('replace_missing_with', None)
        self.trim_whitespace = kwargs.get('trim_whitespace', True)
        self.standardize_dates = kwargs.get('standardize_dates', True)
        self.remove_duplicates = kwargs.get('remove_duplicates', False)
        self.infer_data_types = kwargs.get('infer_data_types', True)
        
        # Excel reading settings
        self.read_formulas = kwargs.get('read_formulas', False)
        self.preserve_formatting = kwargs.get('preserve_formatting', False)
        self.max_file_size = kwargs.get('max_file_size', 100 * 1024 * 1024)  # 100MB
        
        # Validation settings
        self.strict_mode = kwargs.get('strict_mode', False)
        self.validate_data_types = kwargs.get('validate_data_types', True)
        self.check_referential_integrity = kwargs.get('check_referential_integrity', False)
        
        # Output format settings
        self.generate_html_report = kwargs.get('generate_html_report', True)
        self.generate_json_output = kwargs.get('generate_json_output', True)
        self.generate_csv_summary = kwargs.get('generate_csv_summary', True)
        
        # Performance settings
        self.chunk_size = kwargs.get('chunk_size', 1000)
        self.memory_limit = kwargs.get('memory_limit', 1024 * 1024 * 1024)  # 1GB
        
    def to_dict(self) -> dict:
        """Convert configuration to dictionary"""
        return {
            key: value for key, value in self.__dict__.items()
            if not key.startswith('_')
        }
    
    @classmethod
    def from_dict(cls, config_dict: dict) -> 'PipelineConfig':
        """Create configuration from dictionary"""
        return cls(**config_dict)
    
    def validate(self) -> bool:
        """Validate configuration settings"""
        errors = []
        
        # Check output directory
        if not isinstance(self.output_dir, (str, Path)):
            errors.append("output_dir must be a string or Path object")
            
        # Check numeric settings
        if self.max_workers < 1:
            errors.append("max_workers must be at least 1")
            
        if self.file_timeout < 1:
            errors.append("file_timeout must be at least 1 second")
            
        if self.max_scan_rows < 1:
            errors.append("max_scan_rows must be at least 1")
            
        if self.max_scan_cols < 1:
            errors.append("max_scan_cols must be at least 1")
            
        if not 0 <= self.min_data_density <= 1:
            errors.append("min_data_density must be between 0 and 1")
            
        if not 0 <= self.header_confidence_threshold <= 1:
            errors.append("header_confidence_threshold must be between 0 and 1")
            
        if errors:
            raise ValueError(f"Configuration validation failed: {'; '.join(errors)}")
            
        return True
    
    def update(self, **kwargs):
        """Update configuration settings"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise AttributeError(f"Configuration has no attribute '{key}'")
                
        self.validate()


class ProfiledConfig:
    """Pre-configured profiles for different use cases"""
    
    @staticmethod
    def fast_scan() -> PipelineConfig:
        """Configuration for fast scanning with minimal processing"""
        return PipelineConfig(
            max_scan_rows=10,
            max_scan_cols=10,
            infer_data_types=False,
            standardize_dates=False,
            remove_duplicates=False,
            use_multiprocessing=True,
            generate_html_report=False
        )
    
    @staticmethod
    def thorough_analysis() -> PipelineConfig:
        """Configuration for thorough analysis"""
        return PipelineConfig(
            max_scan_rows=50,
            max_scan_cols=50,
            infer_data_types=True,
            standardize_dates=True,
            remove_duplicates=True,
            validate_data_types=True,
            check_referential_integrity=True,
            strict_mode=True
        )
    
    @staticmethod
    def large_files() -> PipelineConfig:
        """Configuration optimized for large files"""
        return PipelineConfig(
            use_multiprocessing=True,
            max_workers=os.cpu_count() or 4,
            chunk_size=5000,
            max_file_size=500 * 1024 * 1024,  # 500MB
            memory_limit=2 * 1024 * 1024 * 1024,  # 2GB
            file_timeout=600  # 10 minutes
        )
    
    @staticmethod
    def unstructured_focus() -> PipelineConfig:
        """Configuration optimized for unstructured data"""
        return PipelineConfig(
            max_scan_rows=100,
            max_scan_cols=20,
            min_data_density=0.1,
            header_confidence_threshold=0.5,
            infer_data_types=False,
            trim_whitespace=True
        )