import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Keys
ANTHROPIC_KEY = os.getenv('ANTHROPIC_KEY')
if not ANTHROPIC_KEY:
    raise ValueError("ANTHROPIC_KEY not found in environment variables")

STABILITY_KEY = os.getenv('STABILITY_KEY')
if not STABILITY_KEY:
    raise ValueError("STABILITY_KEY not found in environment variables")

ELEVENLABS_KEY = os.getenv('ELEVENLABS_KEY')
if not ELEVENLABS_KEY:
    raise ValueError("ELEVENLABS_KEY not found in environment variables")

# Configuration
TEST_MODE = os.getenv('TEST_MODE', 'False').lower() == 'true'
OUTPUT_DIR = os.getenv('OUTPUT_DIR', 'short_story')
