"""
IRL (Information Requirements List) parser and requirement analyzer
"""

import re
from typing import Dict, Any, List, Optional
import logging
import json


class IRLParser:
    """Parse and analyze IRL requirements"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def parse_irl_requirements(self, irl_dict: Dict[str, str]) -> Dict[str, Any]:
        """Parse IRL requirements dictionary into structured format"""
        parsed_requirements = {}
        
        for category, requirements_text in irl_dict.items():
            parsed_requirements[category] = self.parse_requirement_text(requirements_text)
            
        return parsed_requirements
    
    def parse_requirement_text(self, text: str) -> Dict[str, Any]:
        """Parse individual requirement text"""
        requirement = {
            "raw_text": text,
            "files": [],
            "entities": [],
            "periods": [],
            "data_types": [],
            "keywords": []
        }
        
        # Extract file references (a), b), c), etc.)
        file_matches = re.findall(r'[a-z]\)\s*([^,\n]+)', text, re.IGNORECASE)
        requirement["files"] = [f.strip() for f in file_matches]
        
        # Extract entities/company references
        requirement["entities"] = self.extract_entities_from_text(text)
        
        # Extract time periods
        requirement["periods"] = self.extract_periods_from_text(text)
        
        # Extract data types/categories
        requirement["data_types"] = self.extract_data_types_from_text(text)
        
        # Extract keywords
        requirement["keywords"] = self.extract_keywords_from_text(text)
        
        return requirement
    
    def extract_entities_from_text(self, text: str) -> List[str]:
        """Extract entity references from requirement text"""
        entities = []
        
        # Common entity patterns in requirements
        entity_patterns = [
            r'\b([A-Z][A-Za-z\s&]+(?:Inc|LLC|Ltd|Corp|Company|Co|Group|Bank|Fund|Capital|Partners|Holdings))\b',
            r'\b(company|entity|organization|firm|corporation|business|client|customer)\b',
            r'\b(investor|fund|bank|lender|borrower|counterparty|issuer)\b',
            r'\b(portfolio|subsidiary|affiliate|parent|holding)\b'
        ]
        
        for pattern in entity_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities.extend(matches)
            
        # Remove duplicates and normalize
        unique_entities = list(set([e.strip().lower() for e in entities if e.strip()]))
        
        return unique_entities
    
    def extract_periods_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Extract time period references from requirement text"""
        periods = []
        
        # Period patterns
        period_patterns = [
            # Specific years
            (r'\b(20\d{2})\b', 'year'),
            # Year ranges
            (r'\b(20\d{2})[-\s](?:to|through|thru)[-\s](20\d{2})\b', 'year_range'),
            # Quarters
            (r'\b[Q]([1-4])[-\s]?(20\d{2})\b', 'quarter'),
            # Months
            (r'\b(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[-\s]?(20\d{2})?\b', 'month'),
            # Fiscal years
            (r'\b(?:fiscal|FY)[-\s]?(20\d{2})\b', 'fiscal_year'),
            # Relative periods
            (r'\b(current|latest|recent|prior|previous|last)\s+(year|quarter|month|period)\b', 'relative'),
            # Multi-year
            (r'\b(\d+)[-\s]?years?\b', 'multi_year'),
            # As of dates
            (r'\bas\s+of\s+([A-Za-z]+\s+\d{1,2},?\s+20\d{2}|\d{1,2}[/-]\d{1,2}[/-]20\d{2}|20\d{2}[-/]\d{1,2}[-/]\d{1,2})\b', 'as_of_date')
        ]
        
        for pattern, period_type in period_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    period_info = {
                        "type": period_type,
                        "values": list(match),
                        "raw_match": ' '.join(match)
                    }
                else:
                    period_info = {
                        "type": period_type,
                        "values": [match],
                        "raw_match": match
                    }
                periods.append(period_info)
                
        return periods
    
    def extract_data_types_from_text(self, text: str) -> List[str]:
        """Extract data type/category references from requirement text"""
        data_types = []
        
        # Financial data types
        financial_patterns = [
            r'\b(revenue|income|sales|earnings|profit|loss|expenses|costs|cash flow)\b',
            r'\b(balance sheet|income statement|cash flow statement|financial statements?)\b',
            r'\b(assets|liabilities|equity|debt|capital|investments?)\b',
            r'\b(accounts receivable|accounts payable|inventory|working capital)\b',
            r'\b(ratios?|metrics?|kpis?|performance indicators?)\b'
        ]
        
        # Analysis types
        analysis_patterns = [
            r'\b(analysis|breakdown|summary|report|schedule|listing)\b',
            r'\b(aging|maturity|rollforward|reconciliation)\b',
            r'\b(budget|forecast|projection|variance)\b'
        ]
        
        # Transaction types
        transaction_patterns = [
            r'\b(transactions?|activities|movements|transfers)\b',
            r'\b(purchases?|sales|payments?|receipts?)\b',
            r'\b(investments?|disposals?|acquisitions?)\b'
        ]
        
        all_patterns = financial_patterns + analysis_patterns + transaction_patterns
        
        for pattern in all_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            data_types.extend([match.lower() for match in matches])
            
        # Remove duplicates
        return list(set(data_types))
    
    def extract_keywords_from_text(self, text: str) -> List[str]:
        """Extract key business/financial keywords from requirement text"""
        keywords = []
        
        # Important business keywords
        keyword_patterns = [
            # Document types
            r'\b(report|statement|schedule|analysis|summary|listing|register)\b',
            # Time qualifiers
            r'\b(monthly|quarterly|annual|yearly|daily|weekly)\b',
            # Detail levels
            r'\b(detailed|summary|consolidated|separate|individual|combined)\b',
            # Formats
            r'\b(excel|spreadsheet|workbook|file|document|table)\b',
            # Financial terms
            r'\b(financial|accounting|tax|regulatory|compliance)\b',
            # Action words
            r'\b(provide|submit|prepare|include|show|detail|list)\b'
        ]
        
        for pattern in keyword_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            keywords.extend([match.lower() for match in matches])
            
        # Remove duplicates
        return list(set(keywords))
    
    def analyze_requirement_complexity(self, requirement: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the complexity of a requirement"""
        complexity = {
            "file_count": len(requirement["files"]),
            "entity_count": len(requirement["entities"]),
            "period_count": len(requirement["periods"]),
            "keyword_count": len(requirement["keywords"]),
            "complexity_score": 0,
            "complexity_level": "simple"
        }
        
        # Calculate complexity score
        score = 0
        score += complexity["file_count"] * 2  # Multiple files add complexity
        score += complexity["entity_count"] * 1  # Multiple entities add some complexity
        score += complexity["period_count"] * 3  # Time periods add significant complexity
        score += complexity["keyword_count"] * 0.5  # Keywords indicate detail level
        
        complexity["complexity_score"] = score
        
        # Determine complexity level
        if score <= 5:
            complexity["complexity_level"] = "simple"
        elif score <= 15:
            complexity["complexity_level"] = "moderate"
        else:
            complexity["complexity_level"] = "complex"
            
        return complexity
    
    def create_requirement_template(self, irl_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Create a template for requirement matching"""
        template = {
            "categories": {},
            "expected_files": [],
            "required_entities": [],
            "required_periods": [],
            "data_expectations": {}
        }
        
        all_files = []
        all_entities = []
        all_periods = []
        
        for category, requirement in irl_requirements.items():
            template["categories"][category] = {
                "files": requirement["files"],
                "entities": requirement["entities"],
                "periods": requirement["periods"],
                "complexity": self.analyze_requirement_complexity(requirement)
            }
            
            all_files.extend(requirement["files"])
            all_entities.extend(requirement["entities"])
            all_periods.extend([p["raw_match"] for p in requirement["periods"]])
            
        template["expected_files"] = list(set(all_files))
        template["required_entities"] = list(set(all_entities))
        template["required_periods"] = list(set(all_periods))
        
        # Create data expectations
        template["data_expectations"] = self.create_data_expectations(irl_requirements)
        
        return template
    
    def create_data_expectations(self, irl_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Create expectations about what data should be present"""
        expectations = {
            "should_have_financials": False,
            "should_have_dates": True,  # Almost all financial data has dates
            "should_have_entities": True,  # Should have company names
            "expected_columns": [],
            "expected_periods": []
        }
        
        # Analyze all requirements to set expectations
        all_data_types = []
        for requirement in irl_requirements.values():
            all_data_types.extend(requirement["data_types"])
            
        # Check for financial indicators
        financial_terms = ['revenue', 'income', 'profit', 'loss', 'assets', 'liabilities', 'cash']
        if any(term in ' '.join(all_data_types) for term in financial_terms):
            expectations["should_have_financials"] = True
            
        # Extract expected column types
        column_indicators = []
        for requirement in irl_requirements.values():
            column_indicators.extend(requirement["keywords"])
            column_indicators.extend(requirement["data_types"])
            
        expectations["expected_columns"] = list(set(column_indicators))
        
        return expectations