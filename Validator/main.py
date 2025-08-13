"""
Main entry point for the Excel Validator pipeline
"""

import argparse
import sys
from pathlib import Path
import json
import logging
from typing import Optional

from .pipeline import ExcelValidationPipeline
from .config import PipelineConfig, ProfiledConfig


def main():
    """Main entry point for CLI usage"""
    parser = argparse.ArgumentParser(
        description="Excel Validator - Robust pipeline for validating and cleaning Excel files"
    )
    
    # Input arguments
    parser.add_argument(
        "input",
        help="Input file or directory containing Excel files"
    )
    
    # Output arguments
    parser.add_argument(
        "-o", "--output",
        default="validation_output",
        help="Output directory for results (default: validation_output)"
    )
    
    # Processing options
    parser.add_argument(
        "--profile",
        choices=["fast", "thorough", "large", "unstructured"],
        help="Use a pre-configured profile"
    )
    
    # IRL validation options
    parser.add_argument(
        "--irl-file",
        help="JSON file containing IRL requirements for validation"
    )
    
    parser.add_argument(
        "--irl-json",
        help="JSON string containing IRL requirements"
    )
    
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Enable parallel processing"
    )
    
    parser.add_argument(
        "--workers",
        type=int,
        help="Number of parallel workers"
    )
    
    # Structure detection options
    parser.add_argument(
        "--max-scan-rows",
        type=int,
        default=20,
        help="Maximum rows to scan for structure detection"
    )
    
    parser.add_argument(
        "--max-scan-cols",
        type=int,
        default=20,
        help="Maximum columns to scan for structure detection"
    )
    
    # Cleaning options
    parser.add_argument(
        "--no-clean",
        action="store_true",
        help="Skip data cleaning"
    )
    
    parser.add_argument(
        "--remove-duplicates",
        action="store_true",
        help="Remove duplicate rows"
    )
    
    parser.add_argument(
        "--no-infer-types",
        action="store_true",
        help="Don't infer data types"
    )
    
    # Output options
    parser.add_argument(
        "--no-html",
        action="store_true",
        help="Don't generate HTML report"
    )
    
    parser.add_argument(
        "--no-json",
        action="store_true",
        help="Don't generate JSON output"
    )
    
    # Logging options
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress all output except errors"
    )
    
    args = parser.parse_args()
    
    # Create configuration
    config = create_config(args)
    
    # Create pipeline
    pipeline = ExcelValidationPipeline(config)
    
    # Load IRL requirements if provided
    irl_requirements = None
    if args.irl_file:
        try:
            with open(args.irl_file, 'r') as f:
                irl_requirements = json.load(f)
        except Exception as e:
            print(f"Error loading IRL file {args.irl_file}: {str(e)}")
            sys.exit(1)
    elif args.irl_json:
        try:
            irl_requirements = json.loads(args.irl_json)
        except Exception as e:
            print(f"Error parsing IRL JSON: {str(e)}")
            sys.exit(1)
    
    # Process input
    input_path = Path(args.input)
    
    try:
        if input_path.is_file():
            file_paths = [input_path]
        elif input_path.is_dir():
            # Find all Excel files
            file_paths = list(input_path.glob("*.xlsx"))
            file_paths.extend(list(input_path.glob("*.xls")))
        else:
            print(f"Error: {input_path} is not a valid file or directory")
            sys.exit(1)
            
        if not file_paths:
            print("No Excel files found!")
            sys.exit(1)
            
        if irl_requirements:
            # IRL validation mode
            print(f"Running IRL validation on {len(file_paths)} files...")
            results = pipeline.validate_against_irl(file_paths, irl_requirements, args.parallel)
            print("\nIRL Validation completed!")
            print(f"Overall Status: {results.get('overall_compliance', {}).get('status', 'UNKNOWN')}")
            
        else:
            # Standard processing mode
            if len(file_paths) == 1:
                print(f"Processing file: {file_paths[0]}")
                result = pipeline.process_file(file_paths[0])
                pipeline.save_results([result], pipeline.generate_summary([result]))
            else:
                print(f"Processing {len(file_paths)} files...")
                results = pipeline.process_files(file_paths, args.parallel)
            
        print(f"\nValidation complete! Results saved to: {config.output_dir}")
        
    except Exception as e:
        print(f"Error during processing: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def create_config(args) -> PipelineConfig:
    """Create configuration from command line arguments"""
    
    # Start with profile if specified
    if args.profile:
        if args.profile == "fast":
            config = ProfiledConfig.fast_scan()
        elif args.profile == "thorough":
            config = ProfiledConfig.thorough_analysis()
        elif args.profile == "large":
            config = ProfiledConfig.large_files()
        elif args.profile == "unstructured":
            config = ProfiledConfig.unstructured_focus()
    else:
        config = PipelineConfig()
        
    # Override with command line arguments
    config.output_dir = Path(args.output)
    
    if args.parallel:
        config.use_multiprocessing = True
        
    if args.workers:
        config.max_workers = args.workers
        
    config.max_scan_rows = args.max_scan_rows
    config.max_scan_cols = args.max_scan_cols
    
    if args.no_clean:
        config.trim_whitespace = False
        config.standardize_dates = False
        
    config.remove_duplicates = args.remove_duplicates
    config.infer_data_types = not args.no_infer_types
    
    config.generate_html_report = not args.no_html
    config.generate_json_output = not args.no_json
    
    # Set logging level
    if args.quiet:
        config.log_level = logging.ERROR
    elif args.verbose:
        config.log_level = logging.DEBUG
    else:
        config.log_level = logging.INFO
        
    return config


def validate_file(file_path: str, config: Optional[dict] = None) -> dict:
    """
    Convenience function for validating a single file
    
    Args:
        file_path: Path to Excel file
        config: Optional configuration dictionary
        
    Returns:
        Validation results dictionary
    """
    if config:
        pipeline_config = PipelineConfig.from_dict(config)
    else:
        pipeline_config = PipelineConfig()
        
    pipeline = ExcelValidationPipeline(pipeline_config)
    return pipeline.process_file(Path(file_path))


def validate_directory(directory_path: str, config: Optional[dict] = None) -> dict:
    """
    Convenience function for validating all Excel files in a directory
    
    Args:
        directory_path: Path to directory containing Excel files
        config: Optional configuration dictionary
        
    Returns:
        Validation results dictionary
    """
    if config:
        pipeline_config = PipelineConfig.from_dict(config)
    else:
        pipeline_config = PipelineConfig()
        
    pipeline = ExcelValidationPipeline(pipeline_config)
    return pipeline.validate_directory(Path(directory_path))


def validate_against_irl_requirements(file_paths: List[str], irl_requirements: Dict[str, str],
                                     config: Optional[dict] = None) -> dict:
    """
    Convenience function for validating files against IRL requirements
    
    Args:
        file_paths: List of paths to Excel files
        irl_requirements: Dictionary of IRL requirements
        config: Optional configuration dictionary
        
    Returns:
        IRL validation results dictionary
        
    Example:
        irl_dict = {
            "Revenue Analysis": "a) Monthly revenue report, b) Quarterly breakdown",
            "Balance Sheet": "a) Current assets, b) Liabilities summary"
        }
        result = validate_against_irl_requirements(
            ["file1.xlsx", "file2.xlsx"], 
            irl_dict
        )
    """
    if config:
        pipeline_config = PipelineConfig.from_dict(config)
    else:
        pipeline_config = PipelineConfig()
        
    pipeline = ExcelValidationPipeline(pipeline_config)
    return pipeline.validate_against_irl(
        [Path(fp) for fp in file_paths], 
        irl_requirements, 
        parallel=True
    )


if __name__ == "__main__":
    main()