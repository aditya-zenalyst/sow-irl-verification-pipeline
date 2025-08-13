"""
Claude API Integration for Financial Analysis System
"""

import requests
import json
from typing import Dict, Any, Optional
from SOW.config import Config

class ClaudeFinancialAnalyzer:
    """
    Integration class for Claude Sonnet API to perform financial analysis
    """
    
    def __init__(self):
        """Initialize Claude client with API key"""
        Config.validate_config()
        self.api_key = Config.CLAUDE_API_KEY
        self.model = Config.CLAUDE_MODEL
        self.max_tokens = Config.CLAUDE_MAX_TOKENS
        self.api_url = Config.CLAUDE_API_URL
        
        self.headers = {
            'Content-Type': 'application/json',
            'x-api-key': self.api_key,
            'anthropic-version': '2023-06-01'
        }
    
    def analyze_financial_document(self, document_text: str, analysis_type: str = "comprehensive") -> Dict[str, Any]:
        """
        Analyze financial document using Claude Sonnet
        
        Args:
            document_text: The financial document content (PDF text, statements, etc.)
            analysis_type: Type of analysis ("comprehensive", "executive_summary", "credit_risk", etc.)
            
        Returns:
            Dict containing analysis results and scope of work
        """
        
        # Load the appropriate prompt based on analysis type
        if analysis_type == "due_diligence":
            try:
                with open('due_diligence_prompt.txt', 'r') as f:
                    base_prompt = f.read()
            except FileNotFoundError:
                base_prompt = self._get_default_due_diligence_prompt()
        else:
            try:
                with open('claude_financial_analysis_prompt.txt', 'r') as f:
                    base_prompt = f.read()
            except FileNotFoundError:
                base_prompt = self._get_default_prompt()
        
        # Customize prompt based on analysis type
        customized_prompt = self._customize_prompt(base_prompt, analysis_type)
        
        # Prepare the full prompt with document
        full_prompt = f"""
{customized_prompt}

FINANCIAL DOCUMENT TO ANALYZE:
{'='*50}
{document_text}
{'='*50}

Please provide a comprehensive analysis and detailed scope of work recommendation following the framework above.
"""
        
        # Prepare API request
        payload = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": [
                {
                    "role": "user",
                    "content": full_prompt
                }
            ]
        }
        
        try:
            # Make API request
            response = requests.post(
                self.api_url, 
                headers=self.headers, 
                data=json.dumps(payload),
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                analysis_content = result['content'][0]['text']
                
                return {
                    "status": "success",
                    "analysis": analysis_content,
                    "token_usage": result.get('usage', {}),
                    "model_used": self.model
                }
            else:
                return {
                    "status": "error",
                    "error": f"API Error: {response.status_code} - {response.text}",
                    "analysis": None
                }
                
        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "error": f"Request failed: {str(e)}",
                "analysis": None
            }
        except Exception as e:
            return {
                "status": "error", 
                "error": f"Unexpected error: {str(e)}",
                "analysis": None
            }
    
    def _customize_prompt(self, base_prompt: str, analysis_type: str) -> str:
        """Customize the prompt based on analysis type"""
        
        customizations = {
            "due_diligence": """
FOCUS: Generate a professional due diligence scope of work following investment banking standards:
- Use the exact format from the due diligence prompt template
- Structure as detailed table format with Key Buyer Objective and Scope of Work columns
- Include company-specific customization with actual dates and business details
- Cover all major due diligence areas: Quality of earnings, Business drivers, Cash flows, Working capital, Net debt, Quality of assets
- Provide specific, actionable work items suitable for M&A transactions
""",
            "executive_summary": """
FOCUS: Provide a concise executive summary focusing on:
- Overall financial health (3-4 key metrics)
- Top 3 strengths and top 3 concerns
- Immediate action items for management
- High-level scope recommendations (max 5 reports)
""",
            "credit_risk": """
FOCUS: Emphasize credit risk assessment:
- Debt service capability and coverage ratios
- Collateral quality and asset backing
- Cash flow stability and predictability
- Default risk indicators and early warning signs
- Recommended credit monitoring framework
""",
            "investment_analysis": """
FOCUS: Investment and valuation perspective:
- Return on investment metrics and trends
- Growth potential and scalability assessment
- Market position and competitive advantages
- Valuation multiples and fair value indicators
- Investment recommendation framework
""",
            "comprehensive": """
FOCUS: Complete financial health assessment covering all aspects:
- Full financial statement analysis
- Operational efficiency evaluation
- Strategic positioning assessment
- Risk management evaluation
- Growth and sustainability analysis
"""
        }
        
        customization = customizations.get(analysis_type, customizations["comprehensive"])
        return f"{customization}\n\n{base_prompt}"
    
    def _get_default_prompt(self) -> str:
        """Fallback prompt if file is not found"""
        return """
You are a senior financial analyst. Analyze the provided financial document and create:
1. Executive summary of financial health
2. Key metrics and ratios analysis  
3. Strengths and weaknesses identification
4. Detailed scope of work recommendations
5. Data requirements for further analysis
6. Timeline and deliverable specifications

Structure your response professionally with clear sections and actionable recommendations.
"""
    
    def _get_default_due_diligence_prompt(self) -> str:
        """Fallback due diligence prompt if file is not found"""
        return """
You are a senior financial due diligence specialist. Generate a comprehensive due diligence scope of work 
following professional investment banking standards. Structure your response in a detailed table format 
covering Quality of earnings, Business drivers, Cash flows, Working capital, Net debt, and Quality of assets.
Use professional consulting language and provide specific, actionable work items suitable for M&A transactions.
"""
    
    def generate_scope_document(self, company_name: str, analysis_results: str) -> str:
        """
        Generate a formatted scope of work document
        """
        scope_template = f"""
FINANCIAL ANALYSIS SCOPE OF WORK
================================
Company: {company_name}
Generated: {self._get_current_date()}
Analyst: Claude Sonnet AI Financial Analyzer

{analysis_results}

---
This scope of work was generated using Claude Sonnet AI with advanced financial analysis capabilities.
For questions or modifications, please contact your financial analysis team.
"""
        return scope_template
    
    def _get_current_date(self) -> str:
        """Get current date for document generation"""
        from datetime import datetime
        return datetime.now().strftime("%B %d, %Y")
    
    def call_claude_api(self, prompt: str, max_tokens: Optional[int] = None) -> str:
        """
        Generic Claude API call method
        
        Args:
            prompt: The prompt to send to Claude
            max_tokens: Maximum tokens for response (defaults to self.max_tokens)
            
        Returns:
            The response text from Claude
        """
        if max_tokens is None:
            max_tokens = self.max_tokens
            
        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        try:
            response = requests.post(
                self.api_url, 
                headers=self.headers, 
                data=json.dumps(payload),
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['content'][0]['text']
            else:
                raise Exception(f"API call failed with status {response.status_code}: {response.text}")
                
        except Exception as e:
            raise Exception(f"Claude API call error: {str(e)}")
    
    def extract_company_name(self, text: str) -> str:
        """
        Extract company name from financial document text using Claude
        
        Args:
            text: Document text to analyze
            
        Returns:
            Extracted company name or empty string if not found
        """
        prompt = f"""Extract the company name from this financial document. 
        Return ONLY the company name, nothing else. 
        If you cannot find a company name, return "Unknown".
        
        Document text:
        {text[:2000]}
        """
        
        try:
            response = self.call_claude_api(prompt, max_tokens=100)
            company_name = response.strip()
            
            # Clean up common issues
            if company_name.lower() in ['unknown', 'not found', 'n/a']:
                return ""
            
            return company_name
            
        except Exception as e:
            print(f"Error extracting company name: {e}")
            return ""

# Example usage function
def analyze_pdf_document(pdf_text: str, company_name: str = "Client Company") -> Dict[str, Any]:
    """
    Main function to analyze PDF financial document
    
    Args:
        pdf_text: Extracted text from financial PDF
        company_name: Name of the company being analyzed
        
    Returns:
        Complete analysis results and formatted scope document
    """
    
    try:
        # Initialize Claude analyzer
        analyzer = ClaudeFinancialAnalyzer()
        
        # Perform analysis
        results = analyzer.analyze_financial_document(pdf_text, "comprehensive")
        
        if results["status"] == "success":
            # Generate formatted scope document
            scope_document = analyzer.generate_scope_document(company_name, results["analysis"])
            
            return {
                "status": "success",
                "raw_analysis": results["analysis"],
                "formatted_scope": scope_document,
                "token_usage": results.get("token_usage", {}),
                "model_used": results.get("model_used", "")
            }
        else:
            return results
            
    except Exception as e:
        return {
            "status": "error",
            "error": f"Analysis failed: {str(e)}"
        }

if __name__ == "__main__":
    # Example usage
    print("Claude Financial Analysis System")
    print("Make sure to set your CLAUDE_API_KEY in the .env file")
    
    # Test with sample text
    sample_financial_text = """
    Sample Balance Sheet Data:
    Total Assets: $1,000,000
    Total Liabilities: $600,000
    Equity: $400,000
    Revenue: $2,000,000
    Net Income: $150,000
    """
    
    # Uncomment to test (after setting API key)
    # results = analyze_pdf_document(sample_financial_text, "Test Company")
    # print(json.dumps(results, indent=2))