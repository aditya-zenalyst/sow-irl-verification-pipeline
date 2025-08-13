"""
Structure detection for Excel data - identifies if data is structured, unstructured, or semi-structured
"""

import numpy as np
from typing import Dict, Any, List, Tuple, Optional
import re
import logging
from collections import Counter
import statistics


class StructureDetector:
    """Detect and analyze data structure in Excel sheets"""
    
    def __init__(self, config: Any):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Configuration parameters
        self.max_scan_rows = getattr(config, 'max_scan_rows', 20)
        self.max_scan_cols = getattr(config, 'max_scan_cols', 20)
        self.min_data_density = getattr(config, 'min_data_density', 0.3)
        self.header_confidence_threshold = getattr(config, 'header_confidence_threshold', 0.7)
        
    def detect_structure(self, sheet_data: Dict[str, Any]) -> Dict[str, Any]:
        """Main method to detect data structure"""
        data = sheet_data.get("data", [])
        
        if not data:
            return {
                "type": "empty",
                "confidence": 1.0,
                "details": {}
            }
            
        # Analyze the data
        analysis = self.analyze_data_patterns(data)
        
        # Determine structure type
        if analysis["has_table_structure"]:
            return {
                "type": "structured",
                "confidence": analysis["table_confidence"],
                "table_bounds": analysis["table_bounds"],
                "header_row": analysis["header_row"],
                "data_start_row": analysis["data_start_row"],
                "details": analysis
            }
        elif analysis["has_key_value_pairs"]:
            return {
                "type": "unstructured",
                "confidence": analysis["kv_confidence"],
                "key_value_regions": analysis["key_value_regions"],
                "details": analysis
            }
        elif analysis["mixed_structure"]:
            return {
                "type": "semi_structured",
                "confidence": analysis["overall_confidence"],
                "regions": analysis["regions"],
                "details": analysis
            }
        else:
            return {
                "type": "unknown",
                "confidence": 0.0,
                "details": analysis
            }
    
    def analyze_data_patterns(self, data: List[List[Any]]) -> Dict[str, Any]:
        """Analyze patterns in the data"""
        analysis = {
            "has_table_structure": False,
            "has_key_value_pairs": False,
            "mixed_structure": False,
            "table_confidence": 0.0,
            "kv_confidence": 0.0,
            "overall_confidence": 0.0,
            "table_bounds": None,
            "header_row": None,
            "data_start_row": None,
            "key_value_regions": [],
            "regions": []
        }
        
        # Find non-empty regions
        regions = self.find_data_regions(data)
        analysis["regions"] = regions
        
        if not regions:
            return analysis
            
        # Analyze each region
        for region in regions:
            region_type = self.analyze_region(data, region)
            
            if region_type["type"] == "table":
                analysis["has_table_structure"] = True
                analysis["table_confidence"] = max(
                    analysis["table_confidence"], 
                    region_type["confidence"]
                )
                if not analysis["table_bounds"]:
                    analysis["table_bounds"] = region
                    analysis["header_row"] = region_type.get("header_row")
                    analysis["data_start_row"] = region_type.get("data_start_row")
                    
            elif region_type["type"] == "key_value":
                analysis["has_key_value_pairs"] = True
                analysis["kv_confidence"] = max(
                    analysis["kv_confidence"],
                    region_type["confidence"]
                )
                analysis["key_value_regions"].append(region)
                
        # Check for mixed structure
        if analysis["has_table_structure"] and analysis["has_key_value_pairs"]:
            analysis["mixed_structure"] = True
            analysis["overall_confidence"] = (
                analysis["table_confidence"] + analysis["kv_confidence"]
            ) / 2
        else:
            analysis["overall_confidence"] = max(
                analysis["table_confidence"],
                analysis["kv_confidence"]
            )
            
        return analysis
    
    def find_data_regions(self, data: List[List[Any]]) -> List[Dict]:
        """Find regions containing data"""
        regions = []
        
        if not data:
            return regions
            
        rows = len(data)
        cols = max(len(row) for row in data) if data else 0
        
        # Create a binary matrix of non-empty cells
        data_matrix = np.zeros((rows, cols), dtype=bool)
        
        for i, row in enumerate(data):
            for j, cell in enumerate(row[:cols]):
                if cell is not None and str(cell).strip():
                    data_matrix[i, j] = True
                    
        # Find continuous regions
        visited = np.zeros_like(data_matrix, dtype=bool)
        
        for i in range(rows):
            for j in range(cols):
                if data_matrix[i, j] and not visited[i, j]:
                    # Start a new region
                    region = self.expand_region(data_matrix, visited, i, j)
                    if region["area"] > 1:  # Ignore single cells
                        regions.append(region)
                        
        return regions
    
    def expand_region(self, data_matrix: np.ndarray, visited: np.ndarray,
                     start_row: int, start_col: int) -> Dict:
        """Expand a region from a starting point"""
        rows, cols = data_matrix.shape
        
        # Find the bounding box of the connected region
        min_row, max_row = start_row, start_row
        min_col, max_col = start_col, start_col
        
        # Use flood fill algorithm
        stack = [(start_row, start_col)]
        visited[start_row, start_col] = True
        cells = []
        
        while stack:
            r, c = stack.pop()
            cells.append((r, c))
            
            # Check neighbors
            for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nr, nc = r + dr, c + dc
                if (0 <= nr < rows and 0 <= nc < cols and 
                    data_matrix[nr, nc] and not visited[nr, nc]):
                    visited[nr, nc] = True
                    stack.append((nr, nc))
                    min_row = min(min_row, nr)
                    max_row = max(max_row, nr)
                    min_col = min(min_col, nc)
                    max_col = max(max_col, nc)
                    
        return {
            "min_row": min_row,
            "max_row": max_row,
            "min_col": min_col,
            "max_col": max_col,
            "area": len(cells),
            "cells": cells
        }
    
    def analyze_region(self, data: List[List[Any]], region: Dict) -> Dict:
        """Analyze a specific region to determine its type"""
        min_row = region["min_row"]
        max_row = region["max_row"]
        min_col = region["min_col"]
        max_col = region["max_col"]
        
        # Extract region data
        region_data = []
        for i in range(min_row, min(max_row + 1, len(data))):
            row = []
            for j in range(min_col, min(max_col + 1, len(data[i]) if i < len(data) else 0)):
                if j < len(data[i]):
                    row.append(data[i][j])
                else:
                    row.append(None)
            region_data.append(row)
            
        # Check if it's a table
        table_check = self.check_table_structure(region_data)
        if table_check["is_table"]:
            return {
                "type": "table",
                "confidence": table_check["confidence"],
                "header_row": min_row + table_check.get("header_index", 0),
                "data_start_row": min_row + table_check.get("data_start_index", 1)
            }
            
        # Check if it's key-value pairs
        kv_check = self.check_key_value_structure(region_data)
        if kv_check["is_key_value"]:
            return {
                "type": "key_value",
                "confidence": kv_check["confidence"]
            }
            
        return {
            "type": "unknown",
            "confidence": 0.0
        }
    
    def check_table_structure(self, data: List[List[Any]]) -> Dict:
        """Check if data has table structure"""
        if not data or len(data) < 2:
            return {"is_table": False, "confidence": 0.0}
            
        # Find potential header row
        header_index = self.find_header_row(data)
        
        if header_index is None:
            return {"is_table": False, "confidence": 0.0}
            
        # Check column consistency
        header_row = data[header_index]
        non_empty_cols = [i for i, cell in enumerate(header_row) 
                         if cell is not None and str(cell).strip()]
        
        if len(non_empty_cols) < 2:
            return {"is_table": False, "confidence": 0.0}
            
        # Check data rows
        data_rows = data[header_index + 1:]
        if not data_rows:
            return {"is_table": False, "confidence": 0.0}
            
        # Calculate consistency score
        consistency_scores = []
        for row in data_rows[:10]:  # Check first 10 data rows
            row_score = self.calculate_row_consistency(row, non_empty_cols)
            consistency_scores.append(row_score)
            
        if consistency_scores:
            avg_consistency = statistics.mean(consistency_scores)
            
            return {
                "is_table": avg_consistency > 0.5,
                "confidence": avg_consistency,
                "header_index": header_index,
                "data_start_index": header_index + 1
            }
            
        return {"is_table": False, "confidence": 0.0}
    
    def find_header_row(self, data: List[List[Any]]) -> Optional[int]:
        """Find the likely header row in the data"""
        max_score = 0
        best_index = None
        
        for i in range(min(self.max_scan_rows, len(data))):
            row = data[i]
            score = self.score_header_row(row, data[i+1:] if i+1 < len(data) else [])
            
            if score > max_score and score > self.header_confidence_threshold:
                max_score = score
                best_index = i
                
        return best_index
    
    def score_header_row(self, row: List[Any], following_rows: List[List[Any]]) -> float:
        """Score a row's likelihood of being a header"""
        if not row:
            return 0.0
            
        scores = []
        
        # Check for text content
        text_cells = sum(1 for cell in row 
                        if cell is not None and isinstance(cell, str) and cell.strip())
        scores.append(text_cells / len(row) if row else 0)
        
        # Check for unique values
        non_empty = [cell for cell in row if cell is not None and str(cell).strip()]
        if non_empty:
            uniqueness = len(set(str(c) for c in non_empty)) / len(non_empty)
            scores.append(uniqueness)
            
        # Check for typical header patterns
        header_patterns = [
            r'^[A-Z]',  # Starts with capital
            r'(?i)(name|id|date|time|value|amount|total|count|type|status)',
            r'(?i)(description|category|code|number|qty|quantity|price)'
        ]
        
        pattern_matches = 0
        for cell in non_empty:
            cell_str = str(cell)
            if any(re.search(pattern, cell_str) for pattern in header_patterns):
                pattern_matches += 1
                
        if non_empty:
            scores.append(pattern_matches / len(non_empty))
            
        # Check difference from following rows
        if following_rows:
            type_diff_score = self.calculate_type_difference(row, following_rows[0])
            scores.append(type_diff_score)
            
        return statistics.mean(scores) if scores else 0.0
    
    def calculate_type_difference(self, row1: List[Any], row2: List[Any]) -> float:
        """Calculate type difference between two rows"""
        if not row1 or not row2:
            return 0.0
            
        min_len = min(len(row1), len(row2))
        differences = 0
        
        for i in range(min_len):
            type1 = self.get_cell_type(row1[i])
            type2 = self.get_cell_type(row2[i])
            
            if type1 != type2 and type1 != 'empty' and type2 != 'empty':
                differences += 1
                
        return differences / min_len if min_len > 0 else 0.0
    
    def get_cell_type(self, cell: Any) -> str:
        """Get the type of a cell value"""
        if cell is None or (isinstance(cell, str) and not cell.strip()):
            return 'empty'
        
        # Try to parse as number
        try:
            float(str(cell))
            return 'number'
        except:
            pass
            
        # Check for date patterns
        date_patterns = [
            r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
            r'\d{4}[/-]\d{1,2}[/-]\d{1,2}'
        ]
        
        cell_str = str(cell)
        if any(re.search(pattern, cell_str) for pattern in date_patterns):
            return 'date'
            
        return 'text'
    
    def calculate_row_consistency(self, row: List[Any], expected_cols: List[int]) -> float:
        """Calculate how consistent a row is with expected column positions"""
        if not row or not expected_cols:
            return 0.0
            
        filled_expected = sum(1 for col in expected_cols 
                            if col < len(row) and row[col] is not None 
                            and str(row[col]).strip())
        
        return filled_expected / len(expected_cols)
    
    def check_key_value_structure(self, data: List[List[Any]]) -> Dict:
        """Check if data has key-value pair structure"""
        if not data:
            return {"is_key_value": False, "confidence": 0.0}
            
        kv_patterns = []
        
        # Check horizontal key-value pairs
        for row in data[:self.max_scan_rows]:
            if len(row) >= 2:
                # Check if first column looks like keys
                if (row[0] is not None and isinstance(row[0], str) and 
                    row[0].strip() and ':' in str(row[0]) or 
                    (row[1] is not None and row[0] != row[1])):
                    kv_patterns.append('horizontal')
                    
        # Check vertical key-value pairs
        if len(data) >= 2:
            for col_idx in range(min(self.max_scan_cols, 
                                    min(len(row) for row in data) if data else 0)):
                col_data = [row[col_idx] if col_idx < len(row) else None 
                          for row in data]
                
                # Check if this column has key-value pattern
                if self.check_column_kv_pattern(col_data):
                    kv_patterns.append('vertical')
                    
        if kv_patterns:
            confidence = len(kv_patterns) / (len(data) + len(data[0]) if data else 1)
            return {
                "is_key_value": True,
                "confidence": min(confidence, 1.0)
            }
            
        return {"is_key_value": False, "confidence": 0.0}
    
    def check_column_kv_pattern(self, col_data: List[Any]) -> bool:
        """Check if a column has key-value pattern"""
        if len(col_data) < 2:
            return False
            
        # Look for alternating pattern of keys and values
        potential_keys = []
        for i in range(0, len(col_data) - 1, 2):
            if col_data[i] is not None and isinstance(col_data[i], str):
                key_str = str(col_data[i]).strip()
                if key_str and (key_str.endswith(':') or 
                              any(word in key_str.lower() 
                                  for word in ['name', 'id', 'date', 'value', 'type'])):
                    potential_keys.append(i)
                    
        return len(potential_keys) >= 2
    
    def extract_table(self, sheet_data: Dict[str, Any], 
                     structure_info: Dict) -> Dict[str, Any]:
        """Extract table data from detected bounds"""
        data = sheet_data.get("data", [])
        
        if not structure_info.get("table_bounds"):
            return {"data": [], "columns": []}
            
        bounds = structure_info["table_bounds"]
        header_row = structure_info.get("header_row", bounds["min_row"])
        data_start = structure_info.get("data_start_row", header_row + 1)
        
        # Extract headers
        headers = []
        if header_row < len(data):
            header_data = data[header_row]
            for col in range(bounds["min_col"], 
                           min(bounds["max_col"] + 1, len(header_data))):
                if col < len(header_data):
                    headers.append(header_data[col])
                else:
                    headers.append(f"Column_{col}")
                    
        # Extract data rows
        table_data = []
        for row_idx in range(data_start, min(bounds["max_row"] + 1, len(data))):
            row_data = []
            for col_idx in range(bounds["min_col"], bounds["max_col"] + 1):
                if col_idx < len(data[row_idx]):
                    row_data.append(data[row_idx][col_idx])
                else:
                    row_data.append(None)
            table_data.append(row_data)
            
        return {
            "columns": headers,
            "data": table_data,
            "bounds": bounds
        }