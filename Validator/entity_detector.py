"""
Entity detection for company names, investor names, and other relevant entities
"""

import re
from typing import List, Dict, Any, Optional, Set
import logging
from collections import Counter


class EntityDetector:
    """Detect and extract entity names from data"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Common business entity suffixes
        self.entity_suffixes = [
            r'\b(?:Inc|LLC|Ltd|Limited|Corp|Corporation|Company|Co|Group|Holdings|Partners|LP|LLP|GmbH|AG|SA|SPA|PLC|Pty|NV|BV|AB|AS|A\/S|KG|OOO|ZAO|SRL|SARL|SpA|Srl|SE|KK|GK|Bhd|Sdn|Pte|Pvt|Private|Public|Trust|Fund|Bank|Capital|Ventures|Investment|Advisors|Management|Financial|Securities|Asset|Equity|Advisory|Consulting|Services|Solutions|Technologies|Tech|Systems|Software|Digital|Global|International|National|Regional|Industries|Enterprises|Incorporated|Unlimited)\b',
            r'\b(?:& Co|& Sons|& Associates|& Partners|et al)\b'
        ]
        
        # Common entity name patterns
        self.entity_patterns = [
            # Company with suffix
            r'\b([A-Z][A-Za-z\s&\-\.]+(?:' + '|'.join(self.entity_suffixes) + r'))\b',
            # All caps abbreviations (likely company codes)
            r'\b([A-Z]{2,}(?:\.[A-Z]{2,})*)\b',
            # Names with "The" prefix
            r'\b(The\s+[A-Z][A-Za-z\s&\-\.]+)\b',
            # Camel case multi-word (likely company names)
            r'\b([A-Z][a-z]+(?:[A-Z][a-z]+){1,})\b'
        ]
        
        # Column patterns that might contain entity names
        self.entity_column_patterns = [
            r'company', r'corporation', r'firm', r'entity', r'organization', r'org',
            r'client', r'customer', r'vendor', r'supplier', r'partner', r'investor',
            r'fund', r'bank', r'issuer', r'borrower', r'lender', r'counterparty',
            r'name', r'party', r'account', r'holder', r'owner', r'beneficiary',
            r'sponsor', r'manager', r'advisor', r'trustee', r'custodian',
            r'underwriter', r'broker', r'dealer', r'agent', r'principal',
            r'portfolio', r'subsidiary', r'affiliate', r'parent', r'group'
        ]
        
        # Common words to exclude (not entity names)
        self.exclusions = {
            'the', 'and', 'or', 'not', 'all', 'any', 'none', 'total', 'sum',
            'average', 'mean', 'median', 'min', 'max', 'count', 'null', 'na',
            'yes', 'no', 'true', 'false', 'jan', 'feb', 'mar', 'apr', 'may',
            'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec', 'monday', 'tuesday',
            'wednesday', 'thursday', 'friday', 'saturday', 'sunday'
        }
        
    def is_entity_column(self, column_name: str, sample_data: List[Any] = None) -> bool:
        """Check if a column likely contains entity names"""
        col_lower = column_name.lower()
        
        # Check column name patterns
        for pattern in self.entity_column_patterns:
            if re.search(pattern, col_lower):
                return True
                
        # Check sample data if provided
        if sample_data:
            entity_count = sum(1 for val in sample_data[:20] 
                             if self.extract_entities(str(val)))
            return entity_count / min(20, len(sample_data)) > 0.3
            
        return False
    
    def extract_entities(self, text: str) -> List[str]:
        """Extract potential entity names from text"""
        if not text or not isinstance(text, str):
            return []
            
        entities = []
        text = str(text).strip()
        
        # Check for entity patterns
        for pattern in self.entity_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                # Clean and validate
                entity = self.clean_entity_name(match)
                if self.is_valid_entity(entity):
                    entities.append(entity)
                    
        return list(set(entities))  # Remove duplicates
    
    def clean_entity_name(self, name: str) -> str:
        """Clean and normalize entity name"""
        if isinstance(name, tuple):
            name = ' '.join(name)
            
        # Remove extra whitespace
        name = ' '.join(name.split())
        
        # Remove trailing punctuation
        name = re.sub(r'[,;:\.\s]+$', '', name)
        
        # Normalize separators
        name = re.sub(r'\s*[-–—]\s*', '-', name)
        name = re.sub(r'\s*[&]\s*', ' & ', name)
        
        return name.strip()
    
    def is_valid_entity(self, name: str) -> bool:
        """Check if a name is likely a valid entity"""
        if not name or len(name) < 2:
            return False
            
        # Check if it's in exclusions
        if name.lower() in self.exclusions:
            return False
            
        # Must have at least one letter
        if not re.search(r'[A-Za-z]', name):
            return False
            
        # Check for entity suffix
        for suffix_pattern in self.entity_suffixes:
            if re.search(suffix_pattern, name, re.IGNORECASE):
                return True
                
        # Check if it's a proper noun (starts with capital)
        if name[0].isupper() and len(name) > 3:
            # Additional checks for multi-word entities
            words = name.split()
            if len(words) > 1:
                # Most words should start with capital
                capital_words = sum(1 for w in words if w and w[0].isupper())
                if capital_words / len(words) > 0.5:
                    return True
                    
        # Check for all-caps abbreviations
        if re.match(r'^[A-Z]{2,}(?:\.[A-Z]{2,})*$', name):
            return True
            
        return False
    
    def analyze_entity_column(self, data: List[Any]) -> Dict[str, Any]:
        """Analyze a column for entity information"""
        all_entities = []
        entity_counts = Counter()
        
        for value in data:
            if value is None or (isinstance(value, str) and not value.strip()):
                continue
                
            entities = self.extract_entities(str(value))
            all_entities.extend(entities)
            for entity in entities:
                entity_counts[entity] += 1
                
        if not all_entities:
            return {
                "has_entities": False,
                "entity_count": 0,
                "unique_entities": 0
            }
            
        # Get most common entities
        most_common = entity_counts.most_common(10)
        
        return {
            "has_entities": True,
            "entity_count": len(all_entities),
            "unique_entities": len(set(all_entities)),
            "most_common_entities": [
                {"name": name, "count": count} 
                for name, count in most_common
            ],
            "likely_primary_entity": most_common[0][0] if most_common else None,
            "entity_types": self.classify_entities(list(entity_counts.keys())[:20])
        }
    
    def classify_entities(self, entities: List[str]) -> Dict[str, List[str]]:
        """Classify entities by type"""
        classified = {
            "companies": [],
            "banks": [],
            "funds": [],
            "others": []
        }
        
        for entity in entities:
            entity_lower = entity.lower()
            
            if any(term in entity_lower for term in ['bank', 'banking']):
                classified["banks"].append(entity)
            elif any(term in entity_lower for term in ['fund', 'capital', 'investment', 'ventures']):
                classified["funds"].append(entity)
            elif any(re.search(suffix, entity, re.IGNORECASE) for suffix in [r'\b(?:Inc|Corp|LLC|Ltd|Limited|Company|Co)\b']):
                classified["companies"].append(entity)
            else:
                classified["others"].append(entity)
                
        return {k: v for k, v in classified.items() if v}  # Only return non-empty categories
    
    def find_related_entities(self, primary_entity: str, all_entities: List[str]) -> List[str]:
        """Find entities related to a primary entity"""
        related = []
        primary_words = set(primary_entity.lower().split())
        
        for entity in all_entities:
            if entity == primary_entity:
                continue
                
            entity_words = set(entity.lower().split())
            
            # Check for common words
            common_words = primary_words & entity_words
            if len(common_words) > 0 and len(common_words) / len(primary_words) > 0.3:
                related.append(entity)
                
        return related
    
    def extract_entity_metadata(self, data: List[List[Any]], column_indices: Dict[str, int]) -> Dict[str, Any]:
        """Extract entity metadata from data without exposing sensitive information"""
        metadata = {
            "entities_found": {},
            "entity_relationships": []
        }
        
        # Find entity columns
        entity_columns = []
        for col_name, col_idx in column_indices.items():
            if self.is_entity_column(col_name):
                entity_columns.append((col_name, col_idx))
                
        # Analyze each entity column
        for col_name, col_idx in entity_columns:
            column_data = [row[col_idx] if col_idx < len(row) else None for row in data]
            analysis = self.analyze_entity_column(column_data)
            
            if analysis["has_entities"]:
                metadata["entities_found"][col_name] = {
                    "unique_count": analysis["unique_entities"],
                    "primary_entity": analysis.get("likely_primary_entity"),
                    "entity_types": analysis.get("entity_types", {})
                }
                
        return metadata