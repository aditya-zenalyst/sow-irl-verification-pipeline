"""
Data cleaning utilities for structured and unstructured Excel data
"""

import re
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Union
import logging
from datetime import datetime
import statistics
from .date_time_detector import DateTimeDetector
from .entity_detector import EntityDetector


class DataCleaner:
    """Clean and standardize Excel data"""
    
    def __init__(self, config: Any):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize enhanced detectors
        self.date_detector = DateTimeDetector()
        self.entity_detector = EntityDetector()
        
        # Cleaning parameters
        self.replace_missing_with = getattr(config, 'replace_missing_with', None)
        self.trim_whitespace = getattr(config, 'trim_whitespace', True)
        self.standardize_dates = getattr(config, 'standardize_dates', True)
        self.remove_duplicates = getattr(config, 'remove_duplicates', False)
        self.infer_data_types = getattr(config, 'infer_data_types', True)
        
        # Date formats to try
        self.date_formats = [
            '%Y-%m-%d',
            '%d/%m/%Y',
            '%m/%d/%Y',
            '%Y/%m/%d',
            '%d-%m-%Y',
            '%m-%d-%Y',
            '%d.%m.%Y',
            '%Y.%m.%d',
            '%d %B %Y',
            '%B %d, %Y',
            '%d %b %Y',
            '%b %d, %Y'
        ]
        
    def clean_structured_data(self, table_data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean structured tabular data"""
        columns = table_data.get("columns", [])
        data = table_data.get("data", [])
        
        if not columns or not data:
            return {
                "columns": [],
                "data": [],
                "data_types": {},
                "row_count": 0,
                "missing_values": {},
                "descriptions": {}
            }
            
        # Clean column names
        cleaned_columns = self.clean_column_names(columns)
        
        # Convert to DataFrame for easier processing
        df = pd.DataFrame(data, columns=cleaned_columns)
        
        # Clean the data
        df = self.clean_dataframe(df)
        
        # Infer data types
        data_types = self.infer_column_types(df) if self.infer_data_types else {}
        
        # Apply data type conversions
        df = self.apply_data_types(df, data_types)
        
        # Calculate statistics and metadata
        missing_values = self.calculate_missing_values(df)
        descriptions = self.generate_column_descriptions(df, data_types)
        
        # Enhanced analysis with new detectors
        enhanced_metadata = self.generate_enhanced_metadata(df, data_types)
        
        # Remove duplicates if requested
        if self.remove_duplicates:
            original_len = len(df)
            df = df.drop_duplicates()
            if len(df) < original_len:
                self.logger.info(f"Removed {original_len - len(df)} duplicate rows")
                
        # Convert back to list format
        cleaned_data = df.values.tolist()
        
        result = {
            "columns": df.columns.tolist(),
            "data": cleaned_data,
            "data_types": data_types,
            "row_count": len(cleaned_data),
            "missing_values": missing_values,
            "descriptions": descriptions
        }
        
        # Merge enhanced metadata
        result.update(enhanced_metadata)
        
        return result
    
    def clean_column_names(self, columns: List[Any]) -> List[str]:
        """Clean and standardize column names"""
        cleaned = []
        seen = set()
        
        for i, col in enumerate(columns):
            if col is None or (isinstance(col, str) and not col.strip()):
                col_name = f"Column_{i + 1}"
            else:
                col_name = str(col).strip()
                
                # Remove special characters
                col_name = re.sub(r'[^\w\s]', '_', col_name)
                
                # Replace multiple spaces/underscores with single underscore
                col_name = re.sub(r'[\s_]+', '_', col_name)
                
                # Remove leading/trailing underscores
                col_name = col_name.strip('_')
                
                # Ensure not empty
                if not col_name:
                    col_name = f"Column_{i + 1}"
                    
            # Handle duplicates
            original_name = col_name
            counter = 1
            while col_name in seen:
                col_name = f"{original_name}_{counter}"
                counter += 1
                
            seen.add(col_name)
            cleaned.append(col_name)
            
        return cleaned
    
    def clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean DataFrame data"""
        # Trim whitespace
        if self.trim_whitespace:
            for col in df.columns:
                if df[col].dtype == object:
                    df[col] = df[col].apply(
                        lambda x: x.strip() if isinstance(x, str) else x
                    )
                    
        # Replace empty strings with None
        df = df.replace('', None)
        df = df.replace(r'^\s*$', None, regex=True)
        
        # Replace specific missing value indicators
        missing_indicators = ['N/A', 'n/a', 'NA', 'null', 'NULL', 'None', 'NONE', '-', '--', '---']
        for indicator in missing_indicators:
            df = df.replace(indicator, None)
            
        # Replace missing values
        if self.replace_missing_with is not None:
            df = df.fillna(self.replace_missing_with)
            
        return df
    
    def infer_column_types(self, df: pd.DataFrame) -> Dict[str, str]:
        """Infer data types for each column"""
        data_types = {}
        
        for col in df.columns:
            col_data = df[col].dropna()
            
            if len(col_data) == 0:
                data_types[col] = "unknown"
                continue
                
            # Sample the data
            sample_size = min(100, len(col_data))
            sample = col_data.sample(n=sample_size) if len(col_data) > sample_size else col_data
            
            # Check for boolean
            if self.is_boolean_column(sample):
                data_types[col] = "boolean"
                
            # Check for date using enhanced detector
            elif self.date_detector.is_date_column(col, sample.tolist()):
                data_types[col] = "date"
                
            # Check for numeric
            elif self.is_numeric_column(sample):
                if self.is_integer_column(sample):
                    data_types[col] = "integer"
                else:
                    data_types[col] = "float"
                    
            # Check for categorical
            elif self.is_categorical_column(col_data):
                data_types[col] = "categorical"
                
            # Default to text
            else:
                data_types[col] = "text"
                
        return data_types
    
    def is_boolean_column(self, data: pd.Series) -> bool:
        """Check if column contains boolean values"""
        boolean_values = {
            'true', 'false', 'yes', 'no', 'y', 'n', 
            '1', '0', 'on', 'off', 'enabled', 'disabled'
        }
        
        str_data = data.astype(str).str.lower()
        unique_values = set(str_data.unique())
        
        return len(unique_values) <= 2 and unique_values.issubset(boolean_values)
    
    def is_date_column(self, data: pd.Series) -> bool:
        """Check if column contains date values"""
        success_count = 0
        
        for value in data.head(20):  # Check first 20 values
            if self.parse_date(str(value)):
                success_count += 1
                
        return success_count / min(20, len(data)) > 0.5
    
    def is_numeric_column(self, data: pd.Series) -> bool:
        """Check if column contains numeric values"""
        try:
            pd.to_numeric(data, errors='coerce')
            non_numeric = pd.to_numeric(data, errors='coerce').isna().sum()
            return non_numeric / len(data) < 0.1  # Less than 10% non-numeric
        except:
            return False
    
    def is_integer_column(self, data: pd.Series) -> bool:
        """Check if numeric column contains only integers"""
        try:
            numeric_data = pd.to_numeric(data, errors='coerce').dropna()
            return all(float(x).is_integer() for x in numeric_data)
        except:
            return False
    
    def is_categorical_column(self, data: pd.Series) -> bool:
        """Check if column is categorical"""
        unique_ratio = len(data.unique()) / len(data)
        return unique_ratio < 0.5 and len(data.unique()) < 100
    
    def parse_date(self, value: str) -> Optional[datetime]:
        """Try to parse a date string"""
        if not value or not isinstance(value, str):
            return None
            
        # Try standard formats
        for fmt in self.date_formats:
            try:
                return datetime.strptime(value, fmt)
            except:
                continue
                
        # Try pandas parser
        try:
            return pd.to_datetime(value)
        except:
            return None
    
    def apply_data_types(self, df: pd.DataFrame, 
                        data_types: Dict[str, str]) -> pd.DataFrame:
        """Apply inferred data types to DataFrame"""
        for col, dtype in data_types.items():
            if col not in df.columns:
                continue
                
            try:
                if dtype == "integer":
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype('Int64')
                    
                elif dtype == "float":
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                    
                elif dtype == "boolean":
                    df[col] = df[col].apply(self.convert_to_boolean)
                    
                elif dtype == "date" and self.standardize_dates:
                    df[col] = df[col].apply(self.standardize_date)
                    
                elif dtype == "categorical":
                    df[col] = pd.Categorical(df[col])
                    
            except Exception as e:
                self.logger.warning(f"Failed to convert column {col} to {dtype}: {str(e)}")
                
        return df
    
    def convert_to_boolean(self, value: Any) -> Optional[bool]:
        """Convert value to boolean"""
        if pd.isna(value) or value is None:
            return None
            
        str_value = str(value).lower().strip()
        
        true_values = {'true', 'yes', 'y', '1', 'on', 'enabled'}
        false_values = {'false', 'no', 'n', '0', 'off', 'disabled'}
        
        if str_value in true_values:
            return True
        elif str_value in false_values:
            return False
        else:
            return None
    
    def standardize_date(self, value: Any) -> Optional[str]:
        """Standardize date format"""
        if pd.isna(value) or value is None:
            return None
            
        parsed_date = self.parse_date(str(value))
        
        if parsed_date:
            return parsed_date.strftime('%Y-%m-%d')
        else:
            return str(value)  # Keep original if can't parse
    
    def calculate_missing_values(self, df: pd.DataFrame) -> Dict[str, Dict]:
        """Calculate missing value statistics"""
        missing_stats = {}
        
        for col in df.columns:
            missing_count = df[col].isna().sum()
            missing_stats[col] = {
                "count": int(missing_count),
                "percentage": round(missing_count / len(df) * 100, 2) if len(df) > 0 else 0
            }
            
        return missing_stats
    
    def generate_column_descriptions(self, df: pd.DataFrame, 
                                    data_types: Dict[str, str]) -> Dict[str, Dict]:
        """Generate descriptions for each column"""
        descriptions = {}
        
        for col in df.columns:
            col_type = data_types.get(col, "unknown")
            col_data = df[col].dropna()
            
            description = {
                "type": col_type,
                "non_null_count": len(col_data),
                "null_count": len(df) - len(col_data),
                "unique_count": len(col_data.unique()) if len(col_data) > 0 else 0
            }
            
            if col_type in ["integer", "float"] and len(col_data) > 0:
                numeric_data = pd.to_numeric(col_data, errors='coerce').dropna()
                if len(numeric_data) > 0:
                    description.update({
                        "min": float(numeric_data.min()),
                        "max": float(numeric_data.max()),
                        "mean": float(numeric_data.mean()),
                        "median": float(numeric_data.median()),
                        "std": float(numeric_data.std()) if len(numeric_data) > 1 else 0
                    })
                    
            elif col_type == "categorical" and len(col_data) > 0:
                value_counts = col_data.value_counts()
                description["top_values"] = value_counts.head(5).to_dict()
                description["category_count"] = len(value_counts)
                
            elif col_type == "text" and len(col_data) > 0:
                str_lengths = col_data.astype(str).str.len()
                description.update({
                    "min_length": int(str_lengths.min()),
                    "max_length": int(str_lengths.max()),
                    "avg_length": round(str_lengths.mean(), 2)
                })
                
            elif col_type == "date" and len(col_data) > 0:
                date_data = pd.to_datetime(col_data, errors='coerce').dropna()
                if len(date_data) > 0:
                    description.update({
                        "min_date": date_data.min().strftime('%Y-%m-%d'),
                        "max_date": date_data.max().strftime('%Y-%m-%d')
                    })
                    
            descriptions[col] = description
            
        return descriptions
    
    def clean_cell_value(self, value: Any) -> Any:
        """Clean individual cell value"""
        if value is None or pd.isna(value):
            return self.replace_missing_with
            
        if isinstance(value, str):
            # Trim whitespace
            if self.trim_whitespace:
                value = value.strip()
                
            # Remove control characters
            value = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', value)
            
            # Normalize whitespace
            value = ' '.join(value.split())
            
            # Check for missing indicators
            if value.upper() in ['N/A', 'NA', 'NULL', 'NONE', '-', '--', '---']:
                return self.replace_missing_with
                
        return value
    
    def remove_empty_rows_cols(self, data: List[List[Any]]) -> List[List[Any]]:
        """Remove completely empty rows and columns"""
        if not data:
            return data
            
        # Remove empty rows
        non_empty_rows = []
        for row in data:
            if any(cell is not None and str(cell).strip() for cell in row):
                non_empty_rows.append(row)
                
        if not non_empty_rows:
            return []
            
        # Remove empty columns
        max_cols = max(len(row) for row in non_empty_rows)
        non_empty_cols = []
        
        for col_idx in range(max_cols):
            has_data = False
            for row in non_empty_rows:
                if col_idx < len(row) and row[col_idx] is not None and str(row[col_idx]).strip():
                    has_data = True
                    break
                    
            if has_data:
                non_empty_cols.append(col_idx)
                
        # Filter columns
        cleaned_data = []
        for row in non_empty_rows:
            cleaned_row = [row[col_idx] if col_idx < len(row) else None 
                          for col_idx in non_empty_cols]
            cleaned_data.append(cleaned_row)
            
        return cleaned_data
    
    def generate_enhanced_metadata(self, df: pd.DataFrame, data_types: Dict[str, str]) -> Dict[str, Any]:
        """Generate enhanced metadata using new detectors"""
        enhanced = {
            "entity_columns": {},
            "date_columns": {},
            "period_info": {},
            "company_info": {}
        }
        
        # Analyze each column for entities and dates
        for col in df.columns:
            col_data = df[col].dropna().tolist()
            
            # Check for entities
            if self.entity_detector.is_entity_column(col, col_data):
                entity_analysis = self.entity_detector.analyze_entity_column(col_data)
                if entity_analysis.get("has_entities"):
                    enhanced["entity_columns"][col] = {
                        "unique_entities": entity_analysis["unique_entities"],
                        "primary_entity": entity_analysis.get("likely_primary_entity"),
                        "entity_types": entity_analysis.get("entity_types", {})
                    }
                    
            # Check for dates with enhanced analysis
            if self.date_detector.is_date_column(col, col_data):
                date_analysis = self.date_detector.analyze_date_column(col_data)
                if date_analysis.get("is_date"):
                    enhanced["date_columns"][col] = date_analysis
                    
                    # Extract period information
                    parsed_dates = []
                    for val in col_data:
                        parsed = self.date_detector.parse_date(val)
                        if parsed:
                            parsed_dates.append(parsed)
                            
                    if parsed_dates:
                        period_info = self.date_detector.extract_period_info(parsed_dates)
                        enhanced["period_info"][col] = period_info
        
        # Extract company information
        primary_entities = []
        for col_info in enhanced["entity_columns"].values():
            if col_info.get("primary_entity"):
                primary_entities.append(col_info["primary_entity"])
                
        if primary_entities:
            # Find the most common entity (likely the main company)
            entity_counts = {}
            for entity in primary_entities:
                entity_counts[entity] = entity_counts.get(entity, 0) + 1
                
            most_common_entity = max(entity_counts.items(), key=lambda x: x[1])[0]
            enhanced["company_info"] = {
                "primary_company": most_common_entity,
                "all_entities": list(set(primary_entities)),
                "entity_frequency": entity_counts
            }
        
        return enhanced