"""
Configuration file for Claude API integration
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration class for API keys and settings"""
    
    # Claude API Configuration
    CLAUDE_API_KEY = os.getenv('CLAUDE_API_KEY')
    CLAUDE_MODEL = os.getenv('CLAUDE_MODEL', 'claude-3-5-sonnet-20241022')  # Default to Sonnet
    CLAUDE_MAX_TOKENS = int(os.getenv('CLAUDE_MAX_TOKENS', '4000'))
    
    # API Endpoints
    CLAUDE_API_URL = 'https://api.anthropic.com/v1/messages'
    
    # Validation
    @classmethod
    def validate_config(cls):
        """Validate that required configuration is present"""
        if not cls.CLAUDE_API_KEY:
            raise ValueError("CLAUDE_API_KEY environment variable is required")
        return True

# Example of how to use:
# config = Config()
# config.validate_config()