"""
Metadata extraction for privacy-safe data analysis
"""

from typing import Dict, Any, List, Optional
import logging
from .date_time_detector import DateTimeDetector
from .entity_detector import EntityDetector


class MetadataExtractor:
    """Extract metadata without exposing sensitive data"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.date_detector = DateTimeDetector()
        self.entity_detector = EntityDetector()
        
    def extract_safe_metadata(self, validation_results: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata safe for LLM analysis without sensitive data"""
        safe_metadata = {
            "file_info": {},
            "sheets_metadata": {},
            "entities_detected": {},
            "date_periods": {},
            "data_structure": {}
        }
        
        # Extract file-level metadata
        safe_metadata["file_info"] = {
            "file_name": validation_results.get("file_name", ""),
            "status": validation_results.get("status", ""),
            "sheet_count": len(validation_results.get("sheets", {}))
        }
        
        # Process each sheet
        for sheet_name, sheet_data in validation_results.get("sheets", {}).items():
            sheet_meta = self.extract_sheet_metadata(sheet_name, sheet_data)
            safe_metadata["sheets_metadata"][sheet_name] = sheet_meta
            
            # Aggregate entities and dates
            if sheet_meta.get("entities"):
                safe_metadata["entities_detected"][sheet_name] = sheet_meta["entities"]
                
            if sheet_meta.get("date_info"):
                safe_metadata["date_periods"][sheet_name] = sheet_meta["date_info"]
                
        # Add structure summary
        safe_metadata["data_structure"]["summary"] = self.summarize_structure(validation_results)
        
        return safe_metadata
    
    def extract_sheet_metadata(self, sheet_name: str, sheet_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata from a single sheet"""
        metadata = {
            "structure_type": sheet_data.get("structure_type", "unknown"),
            "has_data": False,
            "columns": {},
            "entities": {},
            "date_info": {},
            "data_quality": {}
        }
        
        cleaned_data = sheet_data.get("cleaned_data", {})
        
        if sheet_data.get("structure_type") == "structured":
            metadata.update(self.extract_structured_metadata(cleaned_data))
        elif sheet_data.get("structure_type") == "unstructured":
            metadata.update(self.extract_unstructured_metadata(cleaned_data))
        else:
            # Semi-structured or unknown
            metadata.update(self.extract_mixed_metadata(cleaned_data))
            
        return metadata
    
    def extract_structured_metadata(self, cleaned_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata from structured (tabular) data"""
        metadata = {
            "has_data": True,
            "columns": {},
            "entities": {},
            "date_info": {},
            "data_quality": {}
        }
        
        if not cleaned_data:
            return metadata
            
        # Get column information
        columns = cleaned_data.get("columns", [])
        data_types = cleaned_data.get("data_types", {})
        descriptions = cleaned_data.get("descriptions", {})
        missing_values = cleaned_data.get("missing_values", {})
        data_rows = cleaned_data.get("data", [])
        
        # Process each column
        for col in columns:
            col_meta = {
                "name": col,
                "data_type": data_types.get(col, "unknown"),
                "non_null_count": descriptions.get(col, {}).get("non_null_count", 0),
                "unique_count": descriptions.get(col, {}).get("unique_count", 0),
                "missing_percentage": missing_values.get(col, {}).get("percentage", 0)
            }
            
            # Add type-specific metadata
            if col_meta["data_type"] == "text":
                col_meta.update({
                    "min_length": descriptions.get(col, {}).get("min_length"),
                    "max_length": descriptions.get(col, {}).get("max_length"),
                    "avg_length": descriptions.get(col, {}).get("avg_length")
                })
                
                # Check for entities
                if self.entity_detector.is_entity_column(col):
                    col_data = [row[columns.index(col)] if columns.index(col) < len(row) else None 
                               for row in data_rows]
                    entity_analysis = self.entity_detector.analyze_entity_column(col_data)
                    
                    if entity_analysis.get("has_entities"):
                        metadata["entities"][col] = {
                            "unique_entities": entity_analysis["unique_entities"],
                            "primary_entity": entity_analysis.get("likely_primary_entity"),
                            "entity_types": entity_analysis.get("entity_types", {})
                        }
                        
            elif col_meta["data_type"] in ["integer", "float"]:
                col_meta.update({
                    "min": descriptions.get(col, {}).get("min"),
                    "max": descriptions.get(col, {}).get("max"),
                    "mean": descriptions.get(col, {}).get("mean"),
                    "std": descriptions.get(col, {}).get("std")
                })
                
            elif col_meta["data_type"] == "date":
                col_meta.update({
                    "min_date": descriptions.get(col, {}).get("min_date"),
                    "max_date": descriptions.get(col, {}).get("max_date")
                })
                
                # Analyze date column for periods
                if self.date_detector.is_date_column(col):
                    col_data = [row[columns.index(col)] if columns.index(col) < len(row) else None 
                               for row in data_rows]
                    date_analysis = self.date_detector.analyze_date_column(col_data)
                    
                    if date_analysis.get("is_date"):
                        parsed_dates = []
                        for val in col_data:
                            parsed = self.date_detector.parse_date(val)
                            if parsed:
                                parsed_dates.append(parsed)
                                
                        if parsed_dates:
                            period_info = self.date_detector.extract_period_info(parsed_dates)
                            metadata["date_info"][col] = period_info
                            
            elif col_meta["data_type"] == "categorical":
                col_meta.update({
                    "category_count": descriptions.get(col, {}).get("category_count"),
                    "top_categories": list(descriptions.get(col, {}).get("top_values", {}).keys())[:5] if descriptions.get(col, {}).get("top_values") else []
                })
                
            metadata["columns"][col] = col_meta
            
        # Calculate data quality metrics
        metadata["data_quality"] = {
            "total_rows": cleaned_data.get("row_count", 0),
            "total_columns": len(columns),
            "completeness": self.calculate_completeness(missing_values),
            "has_duplicates": False  # This would need to be determined during cleaning
        }
        
        return metadata
    
    def extract_unstructured_metadata(self, cleaned_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata from unstructured data"""
        metadata = {
            "has_data": True,
            "key_hierarchy": {},
            "entities": {},
            "date_info": {},
            "data_quality": {}
        }
        
        content = cleaned_data.get("content", {})
        
        if not content:
            return metadata
            
        # Extract key hierarchy (without values)
        metadata["key_hierarchy"] = self.extract_key_hierarchy(content)
        
        # Look for entities in keys
        all_keys = self.get_all_keys(content)
        for key in all_keys:
            entities = self.entity_detector.extract_entities(key)
            if entities:
                metadata["entities"][key] = entities
                
        # Data quality for unstructured
        metadata["data_quality"] = {
            "total_keys": len(all_keys),
            "max_depth": cleaned_data.get("metadata", {}).get("max_depth", 0),
            "has_nested_structure": cleaned_data.get("metadata", {}).get("max_depth", 0) > 1
        }
        
        return metadata
    
    def extract_mixed_metadata(self, cleaned_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata from mixed/semi-structured data"""
        # Combine both structured and unstructured approaches
        metadata = {
            "has_data": True,
            "columns": {},
            "key_hierarchy": {},
            "entities": {},
            "date_info": {},
            "data_quality": {}
        }
        
        # Try to extract both types of metadata
        if cleaned_data.get("data"):
            struct_meta = self.extract_structured_metadata(cleaned_data)
            metadata.update(struct_meta)
            
        if cleaned_data.get("content"):
            unstruct_meta = self.extract_unstructured_metadata(cleaned_data)
            metadata["key_hierarchy"] = unstruct_meta.get("key_hierarchy", {})
            
        return metadata
    
    def extract_key_hierarchy(self, content: Dict, prefix: str = "") -> Dict[str, Any]:
        """Extract key hierarchy without exposing values"""
        hierarchy = {}
        
        for key, value in content.items():
            if key.startswith("_"):  # Skip internal keys
                continue
                
            full_key = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, dict):
                hierarchy[key] = {
                    "type": "nested",
                    "keys": list(value.keys())
                }
                # Recursively extract nested keys
                nested = self.extract_key_hierarchy(value, full_key)
                if nested:
                    hierarchy[key]["nested"] = nested
            elif isinstance(value, list):
                hierarchy[key] = {
                    "type": "list",
                    "count": len(value)
                }
            else:
                hierarchy[key] = {
                    "type": "value"
                }
                
        return hierarchy
    
    def get_all_keys(self, content: Dict, prefix: str = "") -> List[str]:
        """Get all keys from nested dictionary"""
        keys = []
        
        for key, value in content.items():
            if key.startswith("_"):
                continue
                
            full_key = f"{prefix}.{key}" if prefix else key
            keys.append(full_key)
            
            if isinstance(value, dict):
                keys.extend(self.get_all_keys(value, full_key))
                
        return keys
    
    def calculate_completeness(self, missing_values: Dict[str, Dict]) -> float:
        """Calculate data completeness percentage"""
        if not missing_values:
            return 100.0
            
        total_missing_pct = sum(col.get("percentage", 0) for col in missing_values.values())
        avg_missing = total_missing_pct / len(missing_values) if missing_values else 0
        
        return round(100 - avg_missing, 2)
    
    def summarize_structure(self, validation_results: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize overall data structure"""
        summary = {
            "total_sheets": len(validation_results.get("sheets", {})),
            "structure_types": {},
            "has_entities": False,
            "has_dates": False,
            "primary_entities": [],
            "date_ranges": []
        }
        
        for sheet_name, sheet_data in validation_results.get("sheets", {}).items():
            struct_type = sheet_data.get("structure_type", "unknown")
            summary["structure_types"][struct_type] = summary["structure_types"].get(struct_type, 0) + 1
            
            # Check for entities and dates
            cleaned = sheet_data.get("cleaned_data", {})
            if cleaned:
                # Look for entities
                if isinstance(cleaned, dict):
                    for key in ["entities", "entity_columns"]:
                        if cleaned.get(key):
                            summary["has_entities"] = True
                            break
                            
                # Look for dates
                for key in ["date_columns", "date_info", "periods"]:
                    if cleaned.get(key):
                        summary["has_dates"] = True
                        break
                        
        return summary