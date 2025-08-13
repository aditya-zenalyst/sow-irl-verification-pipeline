"""
Parser for unstructured Excel data - extracts key-value pairs with hierarchy
"""

import re
from typing import Dict, Any, List, Tuple, Optional, Union
import logging
from collections import OrderedDict


class UnstructuredParser:
    """Parse unstructured data to extract meaningful information"""
    
    def __init__(self, config: Any):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Patterns for identifying keys
        self.key_patterns = [
            r'^[A-Z][a-zA-Z\s]+:',  # Title case followed by colon
            r'^[A-Z][A-Z\s]+:',  # All caps followed by colon
            r'^\d+\.\s+[A-Za-z]',  # Numbered items
            r'^[•·▪▫◦‣⁃]\s+',  # Bullet points
            r'^\([a-z]\)',  # Letter in parentheses
            r'^\d+\)',  # Number with closing parenthesis
        ]
        
        # Patterns for hierarchy detection
        self.hierarchy_indicators = {
            'section': [r'^[A-Z][A-Z\s]+$', r'^\d+\.\s+[A-Z]', r'^Section\s+\d+'],
            'subsection': [r'^\d+\.\d+\s+', r'^[a-z]\)', r'^\s{2,}[A-Z]'],
            'item': [r'^\s*[-•·▪▫◦‣⁃]\s+', r'^\s{4,}']
        }
        
    def parse(self, sheet_data: Dict[str, Any], 
             structure_info: Dict) -> Dict[str, Any]:
        """Parse unstructured data"""
        data = sheet_data.get("data", [])
        
        if not data:
            return {"type": "unstructured", "content": {}}
            
        # Determine parsing strategy
        kv_regions = structure_info.get("key_value_regions", [])
        
        if kv_regions:
            # Parse specific regions
            parsed_content = self.parse_regions(data, kv_regions)
        else:
            # Parse entire sheet
            parsed_content = self.parse_full_sheet(data)
            
        return {
            "type": "unstructured",
            "content": parsed_content,
            "metadata": {
                "total_keys": self.count_keys(parsed_content),
                "max_depth": self.get_max_depth(parsed_content)
            }
        }
    
    def parse_regions(self, data: List[List[Any]], 
                     regions: List[Dict]) -> Dict[str, Any]:
        """Parse specific regions of the data"""
        all_content = OrderedDict()
        
        for idx, region in enumerate(regions):
            region_key = f"Region_{idx + 1}"
            region_data = self.extract_region_data(data, region)
            region_content = self.parse_data_block(region_data)
            
            if region_content:
                all_content[region_key] = region_content
                
        return all_content
    
    def extract_region_data(self, data: List[List[Any]], 
                           region: Dict) -> List[List[Any]]:
        """Extract data from a specific region"""
        region_data = []
        
        for row_idx in range(region["min_row"], 
                           min(region["max_row"] + 1, len(data))):
            row = []
            for col_idx in range(region["min_col"], 
                               min(region["max_col"] + 1, 
                                   len(data[row_idx]) if row_idx < len(data) else 0)):
                if row_idx < len(data) and col_idx < len(data[row_idx]):
                    row.append(data[row_idx][col_idx])
                else:
                    row.append(None)
            region_data.append(row)
            
        return region_data
    
    def parse_full_sheet(self, data: List[List[Any]]) -> Dict[str, Any]:
        """Parse entire sheet as unstructured data"""
        return self.parse_data_block(data)
    
    def parse_data_block(self, data: List[List[Any]]) -> Dict[str, Any]:
        """Parse a block of data into hierarchical structure"""
        content = OrderedDict()
        current_section = None
        current_subsection = None
        pending_value = []
        
        for row in data:
            # Process each cell in the row
            for col_idx, cell in enumerate(row):
                if cell is None or (isinstance(cell, str) and not cell.strip()):
                    continue
                    
                cell_str = str(cell).strip()
                
                # Check if it's a section header
                if self.is_section_header(cell_str, col_idx):
                    # Save any pending values
                    if pending_value and current_section:
                        self.add_to_structure(content, current_section, 
                                            current_subsection, pending_value)
                        pending_value = []
                        
                    current_section = self.clean_header(cell_str)
                    current_subsection = None
                    if current_section not in content:
                        content[current_section] = OrderedDict()
                        
                # Check if it's a subsection
                elif self.is_subsection_header(cell_str, col_idx):
                    # Save any pending values
                    if pending_value and current_section:
                        self.add_to_structure(content, current_section, 
                                            current_subsection, pending_value)
                        pending_value = []
                        
                    current_subsection = self.clean_header(cell_str)
                    if current_section:
                        if current_subsection not in content[current_section]:
                            content[current_section][current_subsection] = OrderedDict()
                            
                # Check if it's a key-value pair
                elif self.is_key_value_pair(cell_str):
                    key, value = self.extract_key_value(cell_str)
                    
                    # Check if value continues in next cell
                    if col_idx + 1 < len(row) and row[col_idx + 1] is not None:
                        next_cell = str(row[col_idx + 1]).strip()
                        if not self.is_key_value_pair(next_cell) and not self.is_header(next_cell):
                            value = f"{value} {next_cell}" if value else next_cell
                            
                    self.add_key_value_to_structure(content, current_section, 
                                                   current_subsection, key, value)
                    
                # Check if it's a standalone key (value might be in next cell/row)
                elif self.is_standalone_key(cell_str):
                    key = self.clean_key(cell_str)
                    value = None
                    
                    # Look for value in next cell
                    if col_idx + 1 < len(row) and row[col_idx + 1] is not None:
                        next_cell = str(row[col_idx + 1]).strip()
                        if not self.is_key_value_pair(next_cell) and not self.is_header(next_cell):
                            value = next_cell
                            
                    self.add_key_value_to_structure(content, current_section, 
                                                   current_subsection, key, value)
                    
                # Otherwise, treat as content
                else:
                    pending_value.append(cell_str)
                    
        # Add any remaining pending values
        if pending_value:
            self.add_to_structure(content, current_section, 
                                current_subsection, pending_value)
            
        return content
    
    def is_section_header(self, text: str, col_idx: int) -> bool:
        """Check if text is a section header"""
        if col_idx > 2:  # Section headers usually start from first few columns
            return False
            
        for pattern in self.hierarchy_indicators['section']:
            if re.match(pattern, text):
                return True
                
        # Check for all caps with multiple words
        if text.isupper() and len(text.split()) > 1 and not text.endswith(':'):
            return True
            
        return False
    
    def is_subsection_header(self, text: str, col_idx: int) -> bool:
        """Check if text is a subsection header"""
        for pattern in self.hierarchy_indicators['subsection']:
            if re.match(pattern, text):
                return True
                
        # Check for title case with multiple words
        words = text.split()
        if (len(words) > 1 and 
            all(word[0].isupper() for word in words if word) and 
            not text.endswith(':')):
            return True
            
        return False
    
    def is_header(self, text: str) -> bool:
        """Check if text is any kind of header"""
        return self.is_section_header(text, 0) or self.is_subsection_header(text, 1)
    
    def is_key_value_pair(self, text: str) -> bool:
        """Check if text contains a key-value pair"""
        # Check for colon separator
        if ':' in text:
            parts = text.split(':', 1)
            if len(parts) == 2 and parts[0].strip() and len(parts[0]) < 50:
                return True
                
        # Check for equals separator
        if '=' in text:
            parts = text.split('=', 1)
            if len(parts) == 2 and parts[0].strip() and len(parts[0]) < 50:
                return True
                
        return False
    
    def is_standalone_key(self, text: str) -> bool:
        """Check if text is a standalone key"""
        # Check if ends with colon
        if text.endswith(':'):
            return True
            
        # Check for key patterns
        for pattern in self.key_patterns:
            if re.match(pattern, text):
                return True
                
        return False
    
    def extract_key_value(self, text: str) -> Tuple[str, Optional[str]]:
        """Extract key and value from text"""
        # Try colon separator
        if ':' in text:
            parts = text.split(':', 1)
            if len(parts) == 2:
                return parts[0].strip(), parts[1].strip() or None
                
        # Try equals separator
        if '=' in text:
            parts = text.split('=', 1)
            if len(parts) == 2:
                return parts[0].strip(), parts[1].strip() or None
                
        return text, None
    
    def clean_header(self, text: str) -> str:
        """Clean header text"""
        # Remove numbering
        text = re.sub(r'^\d+\.?\s*', '', text)
        text = re.sub(r'^\([a-z]\)\s*', '', text)
        
        # Remove special characters
        text = re.sub(r'^[•·▪▫◦‣⁃]\s*', '', text)
        
        return text.strip()
    
    def clean_key(self, text: str) -> str:
        """Clean key text"""
        # Remove trailing colon
        if text.endswith(':'):
            text = text[:-1]
            
        # Clean whitespace
        text = ' '.join(text.split())
        
        return text
    
    def add_to_structure(self, content: Dict, section: Optional[str], 
                        subsection: Optional[str], values: List[str]):
        """Add values to the hierarchical structure"""
        if not values:
            return
            
        # Combine values
        combined_value = ' '.join(values)
        
        if section and subsection:
            if section not in content:
                content[section] = OrderedDict()
            if subsection not in content[section]:
                content[section][subsection] = OrderedDict()
                
            # Add as content
            if "_content" not in content[section][subsection]:
                content[section][subsection]["_content"] = []
            content[section][subsection]["_content"].append(combined_value)
            
        elif section:
            if section not in content:
                content[section] = OrderedDict()
            if "_content" not in content[section]:
                content[section]["_content"] = []
            content[section]["_content"].append(combined_value)
            
        else:
            if "_content" not in content:
                content["_content"] = []
            content["_content"].append(combined_value)
    
    def add_key_value_to_structure(self, content: Dict, section: Optional[str],
                                  subsection: Optional[str], key: str, 
                                  value: Optional[str]):
        """Add key-value pair to the hierarchical structure"""
        if section and subsection:
            if section not in content:
                content[section] = OrderedDict()
            if subsection not in content[section]:
                content[section][subsection] = OrderedDict()
            content[section][subsection][key] = value
            
        elif section:
            if section not in content:
                content[section] = OrderedDict()
            content[section][key] = value
            
        else:
            content[key] = value
    
    def count_keys(self, content: Dict, count: int = 0) -> int:
        """Count total number of keys in the structure"""
        for key, value in content.items():
            count += 1
            if isinstance(value, dict):
                count = self.count_keys(value, count)
        return count
    
    def get_max_depth(self, content: Dict, current_depth: int = 0) -> int:
        """Get maximum depth of the hierarchical structure"""
        if not isinstance(content, dict) or not content:
            return current_depth
            
        max_depth = current_depth
        for value in content.values():
            if isinstance(value, dict):
                depth = self.get_max_depth(value, current_depth + 1)
                max_depth = max(max_depth, depth)
                
        return max_depth
    
    def parse_horizontal_kv(self, row: List[Any]) -> Dict[str, Any]:
        """Parse horizontal key-value pairs from a row"""
        kv_pairs = OrderedDict()
        
        i = 0
        while i < len(row) - 1:
            if row[i] is not None:
                key_str = str(row[i]).strip()
                
                if self.is_standalone_key(key_str) or self.is_key_value_pair(key_str):
                    if self.is_key_value_pair(key_str):
                        key, value = self.extract_key_value(key_str)
                    else:
                        key = self.clean_key(key_str)
                        value = str(row[i + 1]).strip() if i + 1 < len(row) and row[i + 1] is not None else None
                        i += 1  # Skip the value cell
                        
                    kv_pairs[key] = value
                    
            i += 1
            
        return kv_pairs
    
    def parse_vertical_kv(self, data: List[List[Any]], col_idx: int) -> Dict[str, Any]:
        """Parse vertical key-value pairs from a column"""
        kv_pairs = OrderedDict()
        
        i = 0
        while i < len(data) - 1:
            if col_idx < len(data[i]) and data[i][col_idx] is not None:
                key_str = str(data[i][col_idx]).strip()
                
                if self.is_standalone_key(key_str) or self.is_key_value_pair(key_str):
                    if self.is_key_value_pair(key_str):
                        key, value = self.extract_key_value(key_str)
                    else:
                        key = self.clean_key(key_str)
                        # Look for value in next row same column or next column same row
                        value = None
                        if i + 1 < len(data) and col_idx < len(data[i + 1]):
                            value = str(data[i + 1][col_idx]).strip() if data[i + 1][col_idx] is not None else None
                            i += 1  # Skip the value row
                        elif col_idx + 1 < len(data[i]):
                            value = str(data[i][col_idx + 1]).strip() if data[i][col_idx + 1] is not None else None
                            
                    kv_pairs[key] = value
                    
            i += 1
            
        return kv_pairs