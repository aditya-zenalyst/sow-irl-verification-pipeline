"""
LLM-based validator for comparing file metadata with IRL requirements
"""

import json
import re
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime


class LLMValidator:
    """LLM-based validation of files against IRL requirements"""
    
    def __init__(self, llm_client=None):
        self.logger = logging.getLogger(__name__)
        self.llm_client = llm_client  # Can be Claude, OpenAI, etc.
        
    def validate_against_requirements(self, file_metadata: Dict[str, Any], 
                                    irl_template: Dict[str, Any]) -> Dict[str, Any]:
        """Validate file metadata against IRL requirements using LLM"""
        
        # Create validation prompt
        prompt = self.create_validation_prompt(file_metadata, irl_template)
        
        # Get LLM response (placeholder for actual LLM call)
        llm_response = self.call_llm(prompt)
        
        # Parse and structure the response
        validation_result = self.parse_llm_response(llm_response)
        
        # Add metadata analysis
        validation_result.update(self.perform_rule_based_validation(file_metadata, irl_template))
        
        return validation_result
    
    def create_validation_prompt(self, file_metadata: Dict[str, Any], 
                                irl_template: Dict[str, Any]) -> str:
        """Create a comprehensive prompt for LLM validation"""
        
        prompt = f"""
You are a financial document validation expert. Your task is to analyze file metadata against Information Requirements List (IRL) requirements and determine if the submitted files meet the requirements.

## IRL REQUIREMENTS:
{json.dumps(irl_template, indent=2)}

## FILE METADATA (NO SENSITIVE DATA - STRUCTURE ONLY):
{json.dumps(file_metadata, indent=2)}

## VALIDATION TASKS:

1. **File Coverage Analysis:**
   - Are all required file types represented?
   - Are there any missing files based on the requirements?
   - Are there extra files not mentioned in requirements?

2. **Entity Matching:**
   - Do the files contain data about the correct entities/companies mentioned in requirements?
   - Are entity names consistent across files?
   - Any entity mismatches or missing entities?

3. **Time Period Analysis:**
   - Do the date ranges in files match the required periods?
   - Are all required periods covered?
   - Any period gaps or misalignments?

4. **Data Structure Assessment:**
   - Do the column structures align with expected data types?
   - Are the files structured appropriately for the requirements?
   - Any data quality concerns based on metadata?

5. **Content Relevance:**
   - Based on column names and data types, do files contain relevant information?
   - Are the data categories appropriate for the requirements?
   - Any obvious mismatches between file content and requirements?

## RESPONSE FORMAT:
Provide a detailed JSON response with this exact structure:

{{
  "overall_compliance": {{
    "status": "COMPLIANT|PARTIALLY_COMPLIANT|NON_COMPLIANT",
    "confidence_score": 0.0-1.0,
    "summary": "Brief overall assessment"
  }},
  "file_analysis": {{
    "total_files_submitted": number,
    "expected_files": number,
    "missing_files": ["list of missing file types"],
    "extra_files": ["list of unexpected files"],
    "file_matches": {{
      "requirement_category": {{
        "expected": "expected file description",
        "found": "actual file found or null",
        "match_quality": "EXACT|GOOD|PARTIAL|POOR|MISSING",
        "issues": ["list of issues if any"]
      }}
    }}
  }},
  "entity_analysis": {{
    "required_entities": ["list from requirements"],
    "found_entities": ["list from file metadata"],
    "entity_matches": {{
      "entity_name": {{
        "found": true/false,
        "files": ["files containing this entity"],
        "confidence": 0.0-1.0
      }}
    }},
    "missing_entities": ["list"],
    "unexpected_entities": ["list"]
  }},
  "period_analysis": {{
    "required_periods": ["list from requirements"],
    "found_periods": ["list from file metadata"],
    "period_coverage": {{
      "fully_covered": ["periods fully covered"],
      "partially_covered": ["periods with some data"],
      "missing": ["required periods not found"]
    }},
    "date_range_issues": ["any date range problems"]
  }},
  "data_quality": {{
    "structure_assessment": "GOOD|FAIR|POOR",
    "completeness": 0.0-1.0,
    "consistency": 0.0-1.0,
    "issues": ["list of quality concerns"]
  }},
  "recommendations": [
    "List of specific recommendations for improvement"
  ],
  "detailed_findings": {{
    "by_requirement": {{
      "requirement_category": {{
        "status": "MET|PARTIALLY_MET|NOT_MET",
        "evidence": "what supports this assessment",
        "gaps": ["specific gaps or issues"]
      }}
    }}
  }}
}}

## VALIDATION PRINCIPLES:
- Be thorough but not overly strict - allow for reasonable variations in naming and structure
- Focus on substance over form - similar content should match even with different column names
- Consider business context - financial data should have certain expected characteristics
- Be specific about issues and provide actionable recommendations
- Use confidence scores to indicate certainty of matches
- Don't penalize for having more data than required, only for missing required data

Please analyze the metadata carefully and provide your assessment.
"""
        
        return prompt
    
    def call_llm(self, prompt: str) -> str:
        """Call LLM API - placeholder for actual implementation"""
        # This would be replaced with actual LLM API calls
        # For now, return a mock response structure
        
        if self.llm_client:
            try:
                # Example for Claude/OpenAI API call
                response = self.llm_client.generate(prompt)
                return response
            except Exception as e:
                self.logger.error(f"LLM API call failed: {str(e)}")
                return self.create_fallback_response()
        else:
            # Return structured fallback for testing
            return self.create_fallback_response()
    
    def create_fallback_response(self) -> str:
        """Create a fallback response when LLM is not available"""
        fallback = {
            "overall_compliance": {
                "status": "UNKNOWN",
                "confidence_score": 0.5,
                "summary": "LLM validation not available - performed rule-based validation only"
            },
            "file_analysis": {
                "total_files_submitted": 0,
                "expected_files": 0,
                "missing_files": [],
                "extra_files": [],
                "file_matches": {}
            },
            "entity_analysis": {
                "required_entities": [],
                "found_entities": [],
                "entity_matches": {},
                "missing_entities": [],
                "unexpected_entities": []
            },
            "period_analysis": {
                "required_periods": [],
                "found_periods": [],
                "period_coverage": {
                    "fully_covered": [],
                    "partially_covered": [],
                    "missing": []
                },
                "date_range_issues": []
            },
            "data_quality": {
                "structure_assessment": "UNKNOWN",
                "completeness": 0.5,
                "consistency": 0.5,
                "issues": ["LLM validation not available"]
            },
            "recommendations": [
                "Enable LLM validation for detailed analysis"
            ],
            "detailed_findings": {
                "by_requirement": {}
            }
        }
        
        return json.dumps(fallback, indent=2)
    
    def parse_llm_response(self, llm_response: str) -> Dict[str, Any]:
        """Parse and validate LLM response"""
        try:
            # Try to parse JSON response
            response_data = json.loads(llm_response)
            
            # Validate structure
            required_keys = [
                "overall_compliance", "file_analysis", "entity_analysis", 
                "period_analysis", "data_quality", "recommendations", "detailed_findings"
            ]
            
            for key in required_keys:
                if key not in response_data:
                    self.logger.warning(f"Missing key in LLM response: {key}")
                    
            return response_data
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse LLM response as JSON: {str(e)}")
            
            # Try to extract JSON from response if it's wrapped in other text
            json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(0))
                except:
                    pass
                    
            # Return fallback
            return json.loads(self.create_fallback_response())
    
    def perform_rule_based_validation(self, file_metadata: Dict[str, Any], 
                                    irl_template: Dict[str, Any]) -> Dict[str, Any]:
        """Perform rule-based validation to supplement LLM analysis"""
        
        rule_based_results = {
            "rule_based_analysis": {
                "file_count_check": self.check_file_count(file_metadata, irl_template),
                "entity_presence_check": self.check_entity_presence(file_metadata, irl_template),
                "date_coverage_check": self.check_date_coverage(file_metadata, irl_template),
                "structure_consistency_check": self.check_structure_consistency(file_metadata),
                "data_completeness_check": self.check_data_completeness(file_metadata)
            }
        }
        
        return rule_based_results
    
    def check_file_count(self, file_metadata: Dict[str, Any], 
                        irl_template: Dict[str, Any]) -> Dict[str, Any]:
        """Check if the number of files matches expectations"""
        submitted_files = file_metadata.get("file_info", {}).get("sheet_count", 0)
        expected_files = len(irl_template.get("expected_files", []))
        
        return {
            "submitted": submitted_files,
            "expected": expected_files,
            "ratio": submitted_files / expected_files if expected_files > 0 else 0,
            "status": "SUFFICIENT" if submitted_files >= expected_files else "INSUFFICIENT"
        }
    
    def check_entity_presence(self, file_metadata: Dict[str, Any], 
                             irl_template: Dict[str, Any]) -> Dict[str, Any]:
        """Check if required entities are present"""
        found_entities = []
        
        # Extract entities from all sheets
        for sheet_meta in file_metadata.get("sheets_metadata", {}).values():
            sheet_entities = sheet_meta.get("entities", {})
            for col_entities in sheet_entities.values():
                if isinstance(col_entities, dict) and "primary_entity" in col_entities:
                    found_entities.append(col_entities["primary_entity"])
                    
        required_entities = irl_template.get("required_entities", [])
        
        return {
            "required": required_entities,
            "found": list(set(found_entities)),
            "missing": [e for e in required_entities if e not in found_entities],
            "coverage": len([e for e in required_entities if e in found_entities]) / len(required_entities) if required_entities else 1.0
        }
    
    def check_date_coverage(self, file_metadata: Dict[str, Any], 
                           irl_template: Dict[str, Any]) -> Dict[str, Any]:
        """Check if required time periods are covered"""
        found_periods = []
        
        # Extract date ranges from all sheets
        for sheet_meta in file_metadata.get("sheets_metadata", {}).values():
            date_info = sheet_meta.get("date_info", {})
            for col_dates in date_info.values():
                if isinstance(col_dates, dict):
                    if "start_year" in col_dates and "end_year" in col_dates:
                        found_periods.extend(col_dates.get("fiscal_years", []))
                        
        required_periods = irl_template.get("required_periods", [])
        
        return {
            "required": required_periods,
            "found": list(set(found_periods)),
            "coverage": "PARTIAL",  # Would need more sophisticated analysis
            "has_dates": len(found_periods) > 0
        }
    
    def check_structure_consistency(self, file_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Check consistency of data structure"""
        sheet_structures = []
        
        for sheet_name, sheet_meta in file_metadata.get("sheets_metadata", {}).items():
            sheet_structures.append(sheet_meta.get("structure_type", "unknown"))
            
        structure_counts = {s: sheet_structures.count(s) for s in set(sheet_structures)}
        
        return {
            "structure_types": structure_counts,
            "consistency": "CONSISTENT" if len(structure_counts) == 1 else "MIXED",
            "primary_structure": max(structure_counts.items(), key=lambda x: x[1])[0] if structure_counts else "unknown"
        }
    
    def check_data_completeness(self, file_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Check overall data completeness"""
        completeness_scores = []
        
        for sheet_meta in file_metadata.get("sheets_metadata", {}).values():
            if "data_quality" in sheet_meta:
                completeness = sheet_meta["data_quality"].get("completeness", 0)
                completeness_scores.append(completeness)
                
        avg_completeness = sum(completeness_scores) / len(completeness_scores) if completeness_scores else 0
        
        return {
            "average_completeness": avg_completeness,
            "completeness_level": "HIGH" if avg_completeness >= 80 else "MEDIUM" if avg_completeness >= 60 else "LOW",
            "sheets_with_issues": len([s for s in completeness_scores if s < 80])
        }
    
    def generate_validation_summary(self, validation_result: Dict[str, Any]) -> str:
        """Generate a human-readable summary of validation results"""
        
        overall_status = validation_result.get("overall_compliance", {}).get("status", "UNKNOWN")
        confidence = validation_result.get("overall_compliance", {}).get("confidence_score", 0)
        
        summary = f"""
IRL VALIDATION SUMMARY
=====================
Overall Status: {overall_status}
Confidence Score: {confidence:.2f}

FILE ANALYSIS:
- Files Submitted: {validation_result.get("file_analysis", {}).get("total_files_submitted", 0)}
- Files Expected: {validation_result.get("file_analysis", {}).get("expected_files", 0)}
- Missing Files: {len(validation_result.get("file_analysis", {}).get("missing_files", []))}

ENTITY ANALYSIS:
- Required Entities: {len(validation_result.get("entity_analysis", {}).get("required_entities", []))}
- Found Entities: {len(validation_result.get("entity_analysis", {}).get("found_entities", []))}
- Missing Entities: {len(validation_result.get("entity_analysis", {}).get("missing_entities", []))}

PERIOD ANALYSIS:
- Required Periods: {len(validation_result.get("period_analysis", {}).get("required_periods", []))}
- Covered Periods: {len(validation_result.get("period_analysis", {}).get("period_coverage", {}).get("fully_covered", []))}

DATA QUALITY:
- Structure: {validation_result.get("data_quality", {}).get("structure_assessment", "UNKNOWN")}
- Completeness: {validation_result.get("data_quality", {}).get("completeness", 0):.2f}
- Consistency: {validation_result.get("data_quality", {}).get("consistency", 0):.2f}

RECOMMENDATIONS:
"""
        
        for rec in validation_result.get("recommendations", []):
            summary += f"- {rec}\n"
            
        return summary