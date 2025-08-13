"""
Custom exceptions for the Excel validation pipeline
"""


class ValidationError(Exception):
    """Base exception for validation errors"""
    pass


class FileReadError(ValidationError):
    """Exception raised when file cannot be read"""
    pass


class ProcessingError(ValidationError):
    """Exception raised during data processing"""
    pass


class StructureDetectionError(ValidationError):
    """Exception raised during structure detection"""
    pass


class CleaningError(ValidationError):
    """Exception raised during data cleaning"""
    pass


class ParsingError(ValidationError):
    """Exception raised during data parsing"""
    pass


class ConfigurationError(ValidationError):
    """Exception raised for configuration issues"""
    pass


class TimeoutError(ValidationError):
    """Exception raised when processing exceeds timeout"""
    pass