"""
Main pipeline orchestrator for Excel validation and cleaning
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import json
from datetime import datetime
import traceback

from .excel_reader import ExcelReader
from .structure_detector import StructureDetector
from .data_cleaner import DataCleaner
from .unstructured_parser import UnstructuredParser
from .output_formatter import OutputFormatter
from .config import PipelineConfig
from .exceptions import ValidationError, ProcessingError
from .metadata_extractor import MetadataExtractor
from .irl_parser import IRLParser
from .llm_validator import LLMValidator


class ExcelValidationPipeline:
    """Main pipeline for processing Excel files"""
    
    def __init__(self, config: Optional[PipelineConfig] = None):
        """Initialize the pipeline with configuration"""
        self.config = config or PipelineConfig()
        self.setup_logging()
        
        self.reader = ExcelReader(self.config)
        self.detector = StructureDetector(self.config)
        self.cleaner = DataCleaner(self.config)
        self.unstructured_parser = UnstructuredParser(self.config)
        self.formatter = OutputFormatter(self.config)
        self.metadata_extractor = MetadataExtractor()
        self.irl_parser = IRLParser()
        self.llm_validator = LLMValidator()
        
        self.results = []
        self.errors = []
        
    def setup_logging(self):
        """Setup logging configuration"""
        log_dir = Path(self.config.output_dir) / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"pipeline_{timestamp}.log"
        
        logging.basicConfig(
            level=self.config.log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def process_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Process a single Excel file"""
        file_path = Path(file_path)
        self.logger.info(f"Processing file: {file_path}")
        
        result = {
            "file_path": str(file_path),
            "file_name": file_path.name,
            "status": "pending",
            "sheets": {},
            "metadata": {},
            "errors": []
        }
        
        try:
            # Read Excel file
            excel_data = self.reader.read_file(file_path)
            result["metadata"] = excel_data.get("metadata", {})
            
            # Process each sheet
            for sheet_name, sheet_data in excel_data.get("sheets", {}).items():
                self.logger.info(f"Processing sheet: {sheet_name}")
                sheet_result = self.process_sheet(sheet_name, sheet_data)
                result["sheets"][sheet_name] = sheet_result
                
            result["status"] = "success"
            
        except Exception as e:
            self.logger.error(f"Error processing file {file_path}: {str(e)}")
            result["status"] = "error"
            result["errors"].append({
                "type": type(e).__name__,
                "message": str(e),
                "traceback": traceback.format_exc()
            })
            
        return result
    
    def process_sheet(self, sheet_name: str, sheet_data: Any) -> Dict[str, Any]:
        """Process a single sheet from Excel file"""
        sheet_result = {
            "name": sheet_name,
            "structure_type": None,
            "data": None,
            "cleaned_data": None,
            "metadata": {},
            "errors": []
        }
        
        try:
            # Detect structure
            structure_info = self.detector.detect_structure(sheet_data)
            sheet_result["structure_type"] = structure_info["type"]
            sheet_result["metadata"]["structure_info"] = structure_info
            
            if structure_info["type"] == "structured":
                # Process structured data
                cleaned_data = self.process_structured_data(
                    sheet_data, 
                    structure_info
                )
                sheet_result["cleaned_data"] = cleaned_data
                
            elif structure_info["type"] == "unstructured":
                # Process unstructured data
                parsed_data = self.unstructured_parser.parse(
                    sheet_data,
                    structure_info
                )
                sheet_result["cleaned_data"] = parsed_data
                
            else:  # semi-structured or unknown
                # Try both approaches
                try:
                    cleaned_data = self.process_structured_data(
                        sheet_data, 
                        structure_info
                    )
                    sheet_result["cleaned_data"] = cleaned_data
                except:
                    parsed_data = self.unstructured_parser.parse(
                        sheet_data,
                        structure_info
                    )
                    sheet_result["cleaned_data"] = parsed_data
                    
        except Exception as e:
            self.logger.error(f"Error processing sheet {sheet_name}: {str(e)}")
            sheet_result["errors"].append({
                "type": type(e).__name__,
                "message": str(e)
            })
            
        return sheet_result
    
    def process_structured_data(self, data: Any, structure_info: Dict) -> Dict[str, Any]:
        """Process structured tabular data"""
        # Extract table from detected boundaries
        table_data = self.detector.extract_table(data, structure_info)
        
        # Clean the data
        cleaned = self.cleaner.clean_structured_data(table_data)
        
        # Extract metadata
        metadata = {
            "columns": cleaned.get("columns", []),
            "data_types": cleaned.get("data_types", {}),
            "row_count": cleaned.get("row_count", 0),
            "column_count": len(cleaned.get("columns", [])),
            "missing_values": cleaned.get("missing_values", {}),
            "column_descriptions": cleaned.get("descriptions", {})
        }
        
        return {
            "type": "structured",
            "data": cleaned.get("data", []),
            "metadata": metadata
        }
    
    def process_files(self, file_paths: List[Union[str, Path]], 
                     parallel: bool = True) -> Dict[str, Any]:
        """Process multiple Excel files"""
        self.logger.info(f"Processing {len(file_paths)} files")
        
        if parallel and len(file_paths) > 1:
            results = self.process_files_parallel(file_paths)
        else:
            results = self.process_files_sequential(file_paths)
            
        # Generate summary
        summary = self.generate_summary(results)
        
        # Save results
        self.save_results(results, summary)
        
        return {
            "results": results,
            "summary": summary
        }
    
    def process_files_sequential(self, file_paths: List[Union[str, Path]]) -> List[Dict]:
        """Process files sequentially"""
        results = []
        for file_path in file_paths:
            result = self.process_file(file_path)
            results.append(result)
        return results
    
    def process_files_parallel(self, file_paths: List[Union[str, Path]]) -> List[Dict]:
        """Process files in parallel"""
        results = []
        
        max_workers = min(self.config.max_workers, len(file_paths))
        
        if self.config.use_multiprocessing:
            executor_class = ProcessPoolExecutor
        else:
            executor_class = ThreadPoolExecutor
            
        with executor_class(max_workers=max_workers) as executor:
            future_to_file = {
                executor.submit(self.process_file, fp): fp 
                for fp in file_paths
            }
            
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    result = future.result(timeout=self.config.file_timeout)
                    results.append(result)
                except Exception as e:
                    self.logger.error(f"Failed to process {file_path}: {str(e)}")
                    results.append({
                        "file_path": str(file_path),
                        "status": "error",
                        "error": str(e)
                    })
                    
        return results
    
    def generate_summary(self, results: List[Dict]) -> Dict[str, Any]:
        """Generate summary of processing results"""
        summary = {
            "total_files": len(results),
            "successful": 0,
            "failed": 0,
            "sheets_processed": 0,
            "structure_types": {
                "structured": 0,
                "unstructured": 0,
                "semi_structured": 0,
                "unknown": 0
            },
            "processing_time": None,
            "timestamp": datetime.now().isoformat()
        }
        
        for result in results:
            if result.get("status") == "success":
                summary["successful"] += 1
                summary["sheets_processed"] += len(result.get("sheets", {}))
                
                for sheet in result.get("sheets", {}).values():
                    struct_type = sheet.get("structure_type", "unknown")
                    if struct_type in summary["structure_types"]:
                        summary["structure_types"][struct_type] += 1
            else:
                summary["failed"] += 1
                
        return summary
    
    def save_results(self, results: List[Dict], summary: Dict):
        """Save processing results to files"""
        output_dir = Path(self.config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save detailed results
        results_file = output_dir / f"validation_results_{timestamp}.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, default=str)
            
        # Save summary
        summary_file = output_dir / f"validation_summary_{timestamp}.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, default=str)
            
        # Generate formatted report
        report = self.formatter.generate_report(results, summary)
        report_file = output_dir / f"validation_report_{timestamp}.html"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
            
        self.logger.info(f"Results saved to {output_dir}")
    
    def validate_directory(self, directory: Union[str, Path], 
                          pattern: str = "*.xlsx") -> Dict[str, Any]:
        """Validate all Excel files in a directory"""
        directory = Path(directory)
        
        # Find all Excel files
        file_paths = list(directory.glob(pattern))
        file_paths.extend(list(directory.glob("*.xls")))
        
        if not file_paths:
            self.logger.warning(f"No Excel files found in {directory}")
            return {"results": [], "summary": {"total_files": 0}}
            
        self.logger.info(f"Found {len(file_paths)} Excel files in {directory}")
        
        return self.process_files(file_paths, parallel=True)
    
    def validate_against_irl(self, file_paths: List[Union[str, Path]], 
                            irl_requirements: Dict[str, str],
                            parallel: bool = True) -> Dict[str, Any]:
        """Validate files against IRL requirements using LLM"""
        
        # First, process all files normally
        processing_results = self.process_files(file_paths, parallel)
        
        # Parse IRL requirements
        parsed_irl = self.irl_parser.parse_irl_requirements(irl_requirements)
        irl_template = self.irl_parser.create_requirement_template(parsed_irl)
        
        # Extract safe metadata from processing results
        safe_metadata = {}
        for result in processing_results["results"]:
            file_name = result.get("file_name", "unknown")
            safe_metadata[file_name] = self.metadata_extractor.extract_safe_metadata(result)
        
        # Combine all metadata for analysis
        combined_metadata = self.combine_file_metadata(safe_metadata)
        
        # Validate against requirements using LLM
        validation_result = self.llm_validator.validate_against_requirements(
            combined_metadata, irl_template
        )
        
        # Add processing results to validation
        validation_result["file_processing_results"] = processing_results
        validation_result["irl_requirements"] = parsed_irl
        validation_result["safe_metadata"] = safe_metadata
        
        # Generate comprehensive report
        validation_summary = self.llm_validator.generate_validation_summary(validation_result)
        validation_result["validation_summary"] = validation_summary
        
        # Save validation results
        self.save_irl_validation_results(validation_result)
        
        return validation_result
    
    def combine_file_metadata(self, file_metadata: Dict[str, Dict]) -> Dict[str, Any]:
        """Combine metadata from multiple files for analysis"""
        combined = {
            "total_files": len(file_metadata),
            "files": {},
            "aggregate_entities": set(),
            "aggregate_periods": {},
            "structure_summary": {},
            "data_quality_summary": {}
        }
        
        for file_name, metadata in file_metadata.items():
            combined["files"][file_name] = metadata
            
            # Aggregate entities
            for sheet_meta in metadata.get("sheets_metadata", {}).values():
                for entity_info in sheet_meta.get("entities", {}).values():
                    if isinstance(entity_info, dict) and "primary_entity" in entity_info:
                        combined["aggregate_entities"].add(entity_info["primary_entity"])
                        
            # Aggregate periods
            for sheet_meta in metadata.get("sheets_metadata", {}).values():
                for period_info in sheet_meta.get("date_info", {}).values():
                    if isinstance(period_info, dict):
                        start_year = period_info.get("start_year")
                        end_year = period_info.get("end_year")
                        if start_year and end_year:
                            combined["aggregate_periods"][f"{start_year}-{end_year}"] = period_info
        
        # Convert sets to lists for JSON serialization
        combined["aggregate_entities"] = list(combined["aggregate_entities"])
        
        return combined
    
    def save_irl_validation_results(self, validation_result: Dict[str, Any]):
        """Save IRL validation results to files"""
        output_dir = Path(self.config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save detailed validation results
        validation_file = output_dir / f"irl_validation_{timestamp}.json"
        with open(validation_file, 'w', encoding='utf-8') as f:
            json.dump(validation_result, f, indent=2, default=str)
            
        # Save validation summary
        summary_file = output_dir / f"irl_validation_summary_{timestamp}.txt"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(validation_result.get("validation_summary", "No summary available"))
            
        # Generate HTML report for IRL validation
        html_report = self.generate_irl_html_report(validation_result)
        html_file = output_dir / f"irl_validation_report_{timestamp}.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_report)
            
        self.logger.info(f"IRL validation results saved to {output_dir}")
    
    def generate_irl_html_report(self, validation_result: Dict[str, Any]) -> str:
        """Generate HTML report for IRL validation"""
        overall_status = validation_result.get("overall_compliance", {}).get("status", "UNKNOWN")
        confidence = validation_result.get("overall_compliance", {}).get("confidence_score", 0)
        
        html_template = f"""
<!DOCTYPE html>
<html>
<head>
    <title>IRL Validation Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .status-compliant {{ color: green; font-weight: bold; }}
        .status-partial {{ color: orange; font-weight: bold; }}
        .status-non-compliant {{ color: red; font-weight: bold; }}
        .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
        .requirement {{ background: #f9f9f9; margin: 10px 0; padding: 10px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .recommendations {{ background: #fff3cd; padding: 15px; border-radius: 5px; }}
        pre {{ background: #f8f8f8; padding: 10px; overflow-x: auto; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>IRL Validation Report</h1>
        <p><strong>Overall Status:</strong> 
        <span class="status-{overall_status.lower().replace('_', '-')}">{overall_status}</span></p>
        <p><strong>Confidence Score:</strong> {confidence:.2f}</p>
        <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="section">
        <h2>File Analysis</h2>
        <table>
            <tr><th>Metric</th><th>Value</th></tr>
            <tr><td>Files Submitted</td><td>{validation_result.get("file_analysis", {}).get("total_files_submitted", 0)}</td></tr>
            <tr><td>Files Expected</td><td>{validation_result.get("file_analysis", {}).get("expected_files", 0)}</td></tr>
            <tr><td>Missing Files</td><td>{len(validation_result.get("file_analysis", {}).get("missing_files", []))}</td></tr>
            <tr><td>Extra Files</td><td>{len(validation_result.get("file_analysis", {}).get("extra_files", []))}</td></tr>
        </table>
    </div>
    
    <div class="section">
        <h2>Entity Analysis</h2>
        <table>
            <tr><th>Metric</th><th>Value</th></tr>
            <tr><td>Required Entities</td><td>{len(validation_result.get("entity_analysis", {}).get("required_entities", []))}</td></tr>
            <tr><td>Found Entities</td><td>{len(validation_result.get("entity_analysis", {}).get("found_entities", []))}</td></tr>
            <tr><td>Missing Entities</td><td>{len(validation_result.get("entity_analysis", {}).get("missing_entities", []))}</td></tr>
        </table>
    </div>
    
    <div class="section">
        <h2>Period Analysis</h2>
        <table>
            <tr><th>Metric</th><th>Value</th></tr>
            <tr><td>Required Periods</td><td>{len(validation_result.get("period_analysis", {}).get("required_periods", []))}</td></tr>
            <tr><td>Fully Covered</td><td>{len(validation_result.get("period_analysis", {}).get("period_coverage", {}).get("fully_covered", []))}</td></tr>
            <tr><td>Partially Covered</td><td>{len(validation_result.get("period_analysis", {}).get("period_coverage", {}).get("partially_covered", []))}</td></tr>
            <tr><td>Missing</td><td>{len(validation_result.get("period_analysis", {}).get("period_coverage", {}).get("missing", []))}</td></tr>
        </table>
    </div>
    
    <div class="section recommendations">
        <h2>Recommendations</h2>
        <ul>
"""
        
        for rec in validation_result.get("recommendations", []):
            html_template += f"<li>{rec}</li>"
            
        html_template += """
        </ul>
    </div>
    
    <div class="section">
        <h2>Detailed Findings</h2>
        <pre>
"""
        
        html_template += json.dumps(validation_result.get("detailed_findings", {}), indent=2)
        
        html_template += """
        </pre>
    </div>
    
</body>
</html>
"""
        
        return html_template