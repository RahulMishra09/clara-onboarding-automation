#!/usr/bin/env python3
"""
Quick LLM Test Script
Tests if Ollama is working correctly with your configuration.
"""

import sys
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent / 'scripts'))

from dotenv import load_dotenv
load_dotenv()

from llm_client import LLMClient
from logger import setup_logger

logger = setup_logger(__name__)

def test_llm():
    """Test LLM with a simple extraction."""

    print("=" * 70)
    print("  🧠 TESTING OLLAMA LLM")
    print("=" * 70)
    print()

    # Initialize LLM client
    print("[1/3] Initializing LLM client...")
    try:
        from config import OLLAMA_MODEL, OLLAMA_BASE_URL
        client = LLMClient()
        print("✅ LLM client initialized successfully")
        print(f"    Provider: {client.provider}")
        if client.provider == 'ollama':
            print(f"    Model: {OLLAMA_MODEL}")
            print(f"    Base URL: {OLLAMA_BASE_URL}")
    except Exception as e:
        print(f"❌ Failed to initialize LLM client: {e}")
        return False

    print()

    # Test 1: Simple completion
    print("[2/3] Testing simple text generation...")
    test_prompt = "Say 'Hello, I am working!' in one sentence."

    try:
        response = client.complete(test_prompt, max_tokens=50)
        print("✅ Text generation successful")
        print(f"    Response: {response[:100]}...")
    except Exception as e:
        print(f"❌ Text generation failed: {e}")
        return False

    print()

    # Test 2: JSON extraction (like we use in pipelines)
    print("[3/3] Testing JSON extraction...")
    test_json_prompt = """
Extract the following information and return it as JSON:

Text: "Acme Fire Protection Services operates Monday to Friday, 9 AM to 5 PM."

Return JSON with these fields:
{
  "company_name": "...",
  "business_hours": {
    "days": "...",
    "hours": "..."
  }
}

JSON:"""

    try:
        response = client.complete(test_json_prompt, max_tokens=200)

        # Try to extract JSON
        json_data = client.extract_json(response)

        print("✅ JSON extraction successful")
        print(f"    Extracted company: {json_data.get('company_name', 'N/A')}")
        print(f"    Extracted hours: {json_data.get('business_hours', {}).get('hours', 'N/A')}")
    except Exception as e:
        print(f"❌ JSON extraction failed: {e}")
        print(f"    Raw response: {response[:200] if 'response' in locals() else 'No response'}")
        return False

    print()
    print("=" * 70)
    print("  ✅ ALL TESTS PASSED - LLM IS WORKING!")
    print("=" * 70)
    print()
    print("Your Clara AI Automation Pipeline is ready to process calls!")
    print()
    print("Next steps:")
    print("  1. Process a demo call:")
    print("     python scripts/pipeline_a.py data/demo_calls/test_demo.txt")
    print()
    print("  2. View results:")
    print("     python scripts/dashboard_server.py")
    print("     Open: http://localhost:8000/viewer.html")
    print()

    return True


if __name__ == "__main__":
    success = test_llm()
    sys.exit(0 if success else 1)
