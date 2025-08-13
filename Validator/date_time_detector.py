"""
Advanced date-time detection and parsing with support for various formats
"""

import re
from datetime import datetime, date
from typing import Optional, List, Tuple, Any, Dict
import pandas as pd
import logging
from dateutil import parser as date_parser
import calendar


class DateTimeDetector:
    """Robust date-time detection and parsing"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Common date patterns with various separators
        self.date_patterns = [
            # Numeric formats
            (r'\b(\d{1,2})[-/_\s](\d{1,2})[-/_\s](\d{2,4})\b', ['d', 'm', 'y']),  # DD-MM-YYYY
            (r'\b(\d{1,2})[-/_\s](\d{1,2})[-/_\s](\d{2,4})\b', ['m', 'd', 'y']),  # MM-DD-YYYY
            (r'\b(\d{4})[-/_\s](\d{1,2})[-/_\s](\d{1,2})\b', ['y', 'm', 'd']),  # YYYY-MM-DD
            (r'\b(\d{2,4})[-/_\s](\d{1,2})[-/_\s](\d{1,2})\b', ['y', 'm', 'd']),  # YY-MM-DD
            
            # With month names
            (r'\b(\d{1,2})[-\s]([A-Za-z]{3,9})[-\s](\d{2,4})\b', ['d', 'month_name', 'y']),  # DD-Month-YYYY
            (r'\b([A-Za-z]{3,9})[-\s](\d{1,2}),?\s*(\d{2,4})\b', ['month_name', 'd', 'y']),  # Month DD, YYYY
            (r'\b(\d{1,2})\s+([A-Za-z]{3,9})\s+(\d{2,4})\b', ['d', 'month_name', 'y']),  # DD Month YYYY
            
            # ISO format
            (r'\b(\d{4})(\d{2})(\d{2})\b', ['y', 'm', 'd']),  # YYYYMMDD
            
            # Quarter/Period formats
            (r'\b[Q]([1-4])[-\s]?(\d{2,4})\b', ['quarter', 'y']),  # Q1-2024
            (r'\b(\d{2,4})[-\s]?[Q]([1-4])\b', ['y', 'quarter']),  # 2024-Q1
            
            # Month-Year formats
            (r'\b([A-Za-z]{3,9})[-\s](\d{2,4})\b', ['month_name', 'y']),  # Jan-2024
            (r'\b(\d{1,2})[-/_](\d{2,4})\b', ['m', 'y']),  # MM-YYYY
            
            # Time components
            (r'\b(\d{1,2}):(\d{2})(?::(\d{2}))?\s*([AP]M)?\b', ['hour', 'minute', 'second', 'ampm']),
        ]
        
        # Month name mappings
        self.month_names = {
            'jan': 1, 'january': 1, 'feb': 2, 'february': 2, 'mar': 3, 'march': 3,
            'apr': 4, 'april': 4, 'may': 5, 'jun': 6, 'june': 6,
            'jul': 7, 'july': 7, 'aug': 8, 'august': 8, 'sep': 9, 'september': 9,
            'oct': 10, 'october': 10, 'nov': 11, 'november': 11, 'dec': 12, 'december': 12
        }
        
        # Common date column name patterns
        self.date_column_patterns = [
            r'date', r'time', r'datetime', r'dt', r'period', r'month', r'year',
            r'quarter', r'week', r'day', r'timestamp', r'created', r'updated',
            r'modified', r'effective', r'expiry', r'start', r'end', r'from', r'to',
            r'as_of', r'asof', r'reporting', r'transaction', r'trade', r'settlement',
            r'maturity', r'issue', r'dated', r'cal_', r'_dt$', r'_date$', r'_time$'
        ]
        
    def is_date_column(self, column_name: str, sample_data: List[Any] = None) -> bool:
        """Check if a column is likely to contain dates"""
        col_lower = column_name.lower()
        
        # Check column name patterns
        for pattern in self.date_column_patterns:
            if re.search(pattern, col_lower):
                return True
                
        # If sample data provided, check content
        if sample_data:
            date_count = sum(1 for val in sample_data[:20] if self.parse_date(val))
            return date_count / min(20, len(sample_data)) > 0.5
            
        return False
    
    def parse_date(self, value: Any) -> Optional[datetime]:
        """Parse a date from various formats"""
        if value is None or pd.isna(value):
            return None
            
        # Convert to string
        value_str = str(value).strip()
        if not value_str:
            return None
            
        # Try pandas datetime parsing first (handles many formats)
        try:
            result = pd.to_datetime(value_str, errors='coerce')
            if pd.notna(result):
                return result.to_pydatetime() if hasattr(result, 'to_pydatetime') else result
        except:
            pass
            
        # Try dateutil parser (very flexible)
        try:
            return date_parser.parse(value_str, fuzzy=True)
        except:
            pass
            
        # Try custom patterns
        for pattern, components in self.date_patterns:
            match = re.search(pattern, value_str, re.IGNORECASE)
            if match:
                try:
                    date_obj = self.construct_date_from_match(match, components)
                    if date_obj:
                        return date_obj
                except:
                    continue
                    
        # Try Excel serial date number
        try:
            serial = float(value_str)
            if 1 < serial < 100000:  # Reasonable range for Excel dates
                return self.excel_serial_to_datetime(serial)
        except:
            pass
            
        return None
    
    def construct_date_from_match(self, match, components: List[str]) -> Optional[datetime]:
        """Construct datetime from regex match"""
        groups = match.groups()
        date_parts = {'year': None, 'month': None, 'day': None, 
                     'hour': 0, 'minute': 0, 'second': 0}
        
        for i, component in enumerate(components):
            if i >= len(groups) or groups[i] is None:
                continue
                
            value = groups[i]
            
            if component == 'y':
                year = int(value)
                # Handle 2-digit years
                if year < 100:
                    year = 2000 + year if year < 50 else 1900 + year
                date_parts['year'] = year
                
            elif component == 'm':
                date_parts['month'] = int(value)
                
            elif component == 'd':
                date_parts['day'] = int(value)
                
            elif component == 'month_name':
                month_num = self.month_names.get(value.lower()[:3])
                if month_num:
                    date_parts['month'] = month_num
                    
            elif component == 'quarter':
                # Convert quarter to month (use middle month of quarter)
                quarter = int(value)
                date_parts['month'] = (quarter - 1) * 3 + 2
                date_parts['day'] = 1
                
            elif component == 'hour':
                date_parts['hour'] = int(value)
                
            elif component == 'minute':
                date_parts['minute'] = int(value)
                
            elif component == 'second':
                date_parts['second'] = int(value)
                
            elif component == 'ampm' and date_parts['hour']:
                if value.upper() == 'PM' and date_parts['hour'] < 12:
                    date_parts['hour'] += 12
                elif value.upper() == 'AM' and date_parts['hour'] == 12:
                    date_parts['hour'] = 0
                    
        # Validate and create datetime
        if date_parts['year'] and date_parts['month']:
            # Default day to 1 if not provided
            if not date_parts['day']:
                date_parts['day'] = 1
                
            try:
                return datetime(
                    date_parts['year'], date_parts['month'], date_parts['day'],
                    date_parts['hour'], date_parts['minute'], date_parts['second']
                )
            except ValueError:
                # Try to fix invalid dates (e.g., Feb 31)
                if date_parts['day'] > 28:
                    last_day = calendar.monthrange(date_parts['year'], date_parts['month'])[1]
                    date_parts['day'] = min(date_parts['day'], last_day)
                    return datetime(
                        date_parts['year'], date_parts['month'], date_parts['day'],
                        date_parts['hour'], date_parts['minute'], date_parts['second']
                    )
                    
        return None
    
    def excel_serial_to_datetime(self, serial: float) -> datetime:
        """Convert Excel serial date to datetime"""
        # Excel dates start from 1900-01-01 (serial = 1)
        # But Excel incorrectly treats 1900 as a leap year
        if serial < 60:
            delta_days = serial - 1
        else:
            delta_days = serial - 2
            
        return datetime(1900, 1, 1) + pd.Timedelta(days=delta_days)
    
    def analyze_date_column(self, data: List[Any]) -> Dict[str, Any]:
        """Analyze a column of date data"""
        parsed_dates = []
        formats_found = set()
        
        for value in data:
            if value is None or pd.isna(value):
                continue
                
            parsed = self.parse_date(value)
            if parsed:
                parsed_dates.append(parsed)
                # Try to identify format
                format_type = self.identify_date_format(str(value))
                if format_type:
                    formats_found.add(format_type)
                    
        if not parsed_dates:
            return {
                "is_date": False,
                "parsed_count": 0,
                "total_count": len(data)
            }
            
        # Calculate statistics
        min_date = min(parsed_dates)
        max_date = max(parsed_dates)
        
        # Determine granularity
        granularity = self.determine_granularity(parsed_dates)
        
        return {
            "is_date": True,
            "parsed_count": len(parsed_dates),
            "total_count": len(data),
            "parse_rate": len(parsed_dates) / len(data) if data else 0,
            "min_date": min_date.isoformat(),
            "max_date": max_date.isoformat(),
            "date_range_days": (max_date - min_date).days,
            "formats_found": list(formats_found),
            "granularity": granularity,
            "unique_dates": len(set(parsed_dates))
        }
    
    def identify_date_format(self, value_str: str) -> Optional[str]:
        """Identify the format of a date string"""
        value_str = value_str.strip()
        
        # Check common formats
        if re.match(r'^\d{4}-\d{2}-\d{2}', value_str):
            return "ISO (YYYY-MM-DD)"
        elif re.match(r'^\d{1,2}/\d{1,2}/\d{2,4}', value_str):
            return "US (MM/DD/YYYY) or EU (DD/MM/YYYY)"
        elif re.match(r'^\d{1,2}-\d{1,2}-\d{2,4}', value_str):
            return "Hyphenated (DD-MM-YYYY or MM-DD-YYYY)"
        elif re.match(r'^\d{1,2}\s+[A-Za-z]{3,9}\s+\d{2,4}', value_str):
            return "Named month (DD Month YYYY)"
        elif re.match(r'^[A-Za-z]{3,9}\s+\d{1,2},?\s+\d{2,4}', value_str):
            return "US long (Month DD, YYYY)"
        elif re.match(r'^Q[1-4][-\s]?\d{2,4}', value_str, re.IGNORECASE):
            return "Quarter (Q1-YYYY)"
        elif re.match(r'^\d{8}$', value_str):
            return "Compact (YYYYMMDD)"
            
        return "Custom/Unknown"
    
    def determine_granularity(self, dates: List[datetime]) -> str:
        """Determine the granularity of date data"""
        if len(dates) < 2:
            return "unknown"
            
        # Check if all dates have time components
        has_time = any(d.hour != 0 or d.minute != 0 or d.second != 0 for d in dates)
        if has_time:
            return "datetime"
            
        # Check date differences
        sorted_dates = sorted(dates)
        min_diff = min((sorted_dates[i+1] - sorted_dates[i]).days 
                      for i in range(len(sorted_dates)-1) if sorted_dates[i+1] != sorted_dates[i])
        
        if min_diff == 0:
            return "intraday"
        elif min_diff == 1:
            return "daily"
        elif min_diff <= 7:
            return "weekly"
        elif min_diff <= 31:
            return "monthly"
        elif min_diff <= 92:
            return "quarterly"
        else:
            return "yearly"
    
    def extract_period_info(self, dates: List[datetime]) -> Dict[str, Any]:
        """Extract period information from dates"""
        if not dates:
            return {}
            
        min_date = min(dates)
        max_date = max(dates)
        
        return {
            "start_date": min_date.isoformat(),
            "end_date": max_date.isoformat(),
            "start_year": min_date.year,
            "end_year": max_date.year,
            "start_quarter": f"Q{(min_date.month - 1) // 3 + 1}-{min_date.year}",
            "end_quarter": f"Q{(max_date.month - 1) // 3 + 1}-{max_date.year}",
            "span_days": (max_date - min_date).days,
            "span_years": max_date.year - min_date.year + 1,
            "fiscal_years": list(range(min_date.year, max_date.year + 1))
        }