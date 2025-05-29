import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration
TEST_MODE = os.getenv('TEST_MODE', 'False').lower() == 'true'
OUTPUT_DIR = os.getenv('OUTPUT_DIR', 'short_story')

# API Keys
ANTHROPIC_KEY = os.getenv('ANTHROPIC_KEY')
STABILITY_KEY = os.getenv('STABILITY_KEY')
ELEVENLABS_KEY = os.getenv('ELEVENLABS_KEY')

if not TEST_MODE:
    if not ANTHROPIC_KEY:
        raise ValueError("ANTHROPIC_KEY not found in environment variables. Set it or run in TEST_MODE.")
    if not STABILITY_KEY:
        raise ValueError("STABILITY_KEY not found in environment variables. Set it or run in TEST_MODE.")
    if not ELEVENLABS_KEY:
        raise ValueError("ELEVENLABS_KEY not found in environment variables. Set it or run in TEST_MODE.")
