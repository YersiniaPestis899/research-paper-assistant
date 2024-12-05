import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # AWS Configuration
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_DEFAULT_REGION = os.getenv('AWS_DEFAULT_REGION')
    
    # Flask Configuration
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    DEBUG = os.getenv('FLASK_DEBUG', '1') == '1'
    
    # Application Configuration
    MAX_SEARCH_RESULTS = 5
    CLAUDE_MODEL_ID = 'anthropic.claude-3.sonnet-20240229-v1:0'
