"""
Configuration management for Clara AI Automation Pipeline.
Loads environment variables and provides centralized config access.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "accounts"
LOG_DIR = PROJECT_ROOT / "logs"
WORKFLOWS_DIR = PROJECT_ROOT / "workflows"
PROMPTS_DIR = PROJECT_ROOT / "prompts"

# Ensure directories exist
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# LLM Configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "anthropic")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")

# Storage Configuration
STORAGE_TYPE = os.getenv("STORAGE_TYPE", "local")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Processing Configuration
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
TIMEOUT_SECONDS = int(os.getenv("TIMEOUT_SECONDS", "30"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Retell Configuration
RETELL_API_KEY = os.getenv("RETELL_API_KEY")
RETELL_AGENT_VOICE = os.getenv("RETELL_AGENT_VOICE", "professional-female")

# Task Tracker Configuration
ASANA_ACCESS_TOKEN = os.getenv("ASANA_ACCESS_TOKEN")
TRELLO_API_KEY = os.getenv("TRELLO_API_KEY")
TRELLO_TOKEN = os.getenv("TRELLO_TOKEN")


def validate_config():
    """Validate that required configuration is present."""
    errors = []

    # Check LLM provider configuration
    if LLM_PROVIDER == "anthropic" and not ANTHROPIC_API_KEY:
        errors.append("ANTHROPIC_API_KEY is required when using 'anthropic' provider")
    elif LLM_PROVIDER == "openai" and not OPENAI_API_KEY:
        errors.append("OPENAI_API_KEY is required when using 'openai' provider")
    elif LLM_PROVIDER not in ["anthropic", "openai", "ollama"]:
        errors.append(f"Invalid LLM_PROVIDER: {LLM_PROVIDER}. Must be 'anthropic', 'openai', or 'ollama'")

    # Check storage configuration
    if STORAGE_TYPE == "supabase" and (not SUPABASE_URL or not SUPABASE_KEY):
        errors.append("SUPABASE_URL and SUPABASE_KEY are required when using 'supabase' storage")
    elif STORAGE_TYPE not in ["local", "supabase"]:
        errors.append(f"Invalid STORAGE_TYPE: {STORAGE_TYPE}. Must be 'local' or 'supabase'")

    if errors:
        raise ValueError(f"Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors))

    return True


if __name__ == "__main__":
    try:
        validate_config()
        print("Configuration is valid")
        print(f"LLM Provider: {LLM_PROVIDER}")
        print(f"Storage Type: {STORAGE_TYPE}")
        print(f"Output Directory: {OUTPUT_DIR}")
    except ValueError as e:
        print(f"{e}")
