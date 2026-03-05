#!/usr/bin/env python3
"""
Health Check Script for Clara AI Automation Pipeline
Validates all system components before processing.
"""

import os
import sys
from pathlib import Path
import requests
from dotenv import load_dotenv

# Load environment
project_root = Path(__file__).parent.parent
load_dotenv(project_root / '.env')

sys.path.insert(0, str(project_root / 'scripts'))

import config
from logger import setup_logger

logger = setup_logger(__name__)


class HealthCheck:
    """System health checker."""

    def __init__(self):
        self.checks_passed = 0
        self.checks_failed = 0
        self.warnings = []

    def print_header(self, text: str):
        """Print formatted header."""
        print(f"\n{'='*70}")
        print(f"  {text}")
        print(f"{'='*70}\n")

    def check(self, name: str, func) -> bool:
        """Run a health check."""
        try:
            print(f"[{self.checks_passed + self.checks_failed + 1}] Checking {name}...", end=" ")
            result, message = func()
            if result:
                print(f"✅ {message}")
                self.checks_passed += 1
                return True
            else:
                print(f"⚠️  {message}")
                self.warnings.append(f"{name}: {message}")
                return False
        except Exception as e:
            print(f"❌ ERROR: {str(e)[:100]}")
            self.checks_failed += 1
            return False

    def check_environment_variables(self) -> tuple[bool, str]:
        """Check required environment variables."""
        required_vars = ['LLM_PROVIDER', 'STORAGE_TYPE']
        missing = [var for var in required_vars if not os.getenv(var)]

        if missing:
            return False, f"Missing: {', '.join(missing)}"

        provider = os.getenv('LLM_PROVIDER')
        storage = os.getenv('STORAGE_TYPE')
        return True, f"Provider={provider}, Storage={storage}"

    def check_directories(self) -> tuple[bool, str]:
        """Check required directories exist."""
        required_dirs = [
            'data/demo_calls',
            'data/onboarding_calls',
            'outputs/accounts',
            'logs',
            'prompts',
            'scripts'
        ]

        missing = []
        for dir_path in required_dirs:
            full_path = project_root / dir_path
            if not full_path.exists():
                missing.append(dir_path)

        if missing:
            return False, f"Missing directories: {', '.join(missing)}"

        return True, f"All {len(required_dirs)} directories exist"

    def check_prompt_templates(self) -> tuple[bool, str]:
        """Check prompt templates exist."""
        demo_prompt = project_root / 'prompts' / 'extract_demo.txt'
        onboarding_prompt = project_root / 'prompts' / 'extract_onboarding.txt'

        if not demo_prompt.exists():
            return False, "Missing: extract_demo.txt"
        if not onboarding_prompt.exists():
            return False, "Missing: extract_onboarding.txt"

        demo_size = demo_prompt.stat().st_size
        onboarding_size = onboarding_prompt.stat().st_size

        return True, f"Demo={demo_size}B, Onboarding={onboarding_size}B"

    def check_ollama_server(self) -> tuple[bool, str]:
        """Check Ollama server connectivity."""
        provider = os.getenv('LLM_PROVIDER')
        if provider != 'ollama':
            return True, f"Not using Ollama (provider={provider})"

        ollama_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')

        try:
            response = requests.get(f"{ollama_url}/api/version", timeout=5)
            if response.status_code == 200:
                version_data = response.json()
                version = version_data.get('version', 'unknown')
                return True, f"Connected (v{version})"
            else:
                return False, f"Server returned {response.status_code}"
        except requests.exceptions.ConnectionError:
            return False, "Server not running (run: ollama serve)"
        except Exception as e:
            return False, f"Connection error: {str(e)[:50]}"

    def check_ollama_model(self) -> tuple[bool, str]:
        """Check Ollama model is downloaded."""
        provider = os.getenv('LLM_PROVIDER')
        if provider != 'ollama':
            return True, "Not using Ollama"

        model = os.getenv('OLLAMA_MODEL', 'llama3.1')
        ollama_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')

        try:
            response = requests.get(f"{ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                models = [m['name'] for m in data.get('models', [])]

                # Check for exact match or with :latest suffix
                if model in models or f"{model}:latest" in models:
                    return True, f"Model '{model}' available"
                else:
                    return False, f"Model '{model}' not found (run: ollama pull {model})"
            else:
                return False, f"Cannot list models ({response.status_code})"
        except Exception as e:
            return False, f"Error: {str(e)[:50]}"

    def check_supabase_connection(self) -> tuple[bool, str]:
        """Check Supabase connectivity."""
        storage_type = os.getenv('STORAGE_TYPE')
        if storage_type != 'supabase':
            return True, f"Not using Supabase (storage={storage_type})"

        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')

        if not supabase_url or not supabase_key:
            return False, "Missing SUPABASE_URL or SUPABASE_KEY"

        try:
            headers = {
                'apikey': supabase_key,
                'Authorization': f'Bearer {supabase_key}'
            }
            response = requests.get(
                f'{supabase_url}/rest/v1/',
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                return True, "Connected successfully"
            else:
                return False, f"Server returned {response.status_code}"
        except Exception as e:
            return False, f"Connection error: {str(e)[:50]}"

    def check_python_dependencies(self) -> tuple[bool, str]:
        """Check Python dependencies are installed."""
        required_modules = [
            'pydantic',
            'colorlog',
            'requests',
            'python-dotenv'
        ]

        provider = os.getenv('LLM_PROVIDER')
        if provider == 'anthropic':
            required_modules.append('anthropic')
        elif provider == 'openai':
            required_modules.append('openai')
        elif provider == 'ollama':
            required_modules.append('ollama')

        missing = []
        for module in required_modules:
            try:
                module_name = 'dotenv' if module == 'python-dotenv' else module
                __import__(module_name)
            except ImportError:
                missing.append(module)

        if missing:
            return False, f"Missing: {', '.join(missing)}"

        return True, f"All {len(required_modules)} modules installed"

    def check_write_permissions(self) -> tuple[bool, str]:
        """Check write permissions for outputs and logs."""
        test_dirs = [
            project_root / 'outputs' / 'accounts',
            project_root / 'logs'
        ]

        for test_dir in test_dirs:
            test_file = test_dir / '.health_check_test'
            try:
                test_file.write_text('test')
                test_file.unlink()
            except Exception as e:
                return False, f"No write access to {test_dir.name}"

        return True, "Write access confirmed"

    def check_configuration_valid(self) -> tuple[bool, str]:
        """Check configuration loads correctly."""
        try:
            import config

            # Try accessing config values
            _ = config.LLM_PROVIDER
            _ = config.STORAGE_TYPE
            _ = config.OUTPUT_DIR

            return True, "Configuration loads successfully"
        except Exception as e:
            return False, f"Config error: {str(e)[:50]}"

    def run_all_checks(self) -> bool:
        """Run all health checks."""
        self.print_header("🏥 CLARA AI AUTOMATION - HEALTH CHECK")

        # Core checks
        print("📋 CORE SYSTEM CHECKS")
        self.check("Environment Variables", self.check_environment_variables)
        self.check("Configuration", self.check_configuration_valid)
        self.check("Directories", self.check_directories)
        self.check("Prompt Templates", self.check_prompt_templates)
        self.check("Python Dependencies", self.check_python_dependencies)
        self.check("Write Permissions", self.check_write_permissions)

        # LLM checks
        print(f"\n🧠 LLM PROVIDER CHECKS ({os.getenv('LLM_PROVIDER', 'unknown')})")
        self.check("Ollama Server", self.check_ollama_server)
        self.check("Ollama Model", self.check_ollama_model)

        # Storage checks
        print(f"\n💾 STORAGE CHECKS ({os.getenv('STORAGE_TYPE', 'unknown')})")
        self.check("Supabase Connection", self.check_supabase_connection)

        # Summary
        self.print_header("📊 HEALTH CHECK SUMMARY")

        total_checks = self.checks_passed + self.checks_failed + len(self.warnings)

        print(f"✅ Passed:   {self.checks_passed}/{total_checks}")
        if self.warnings:
            print(f"⚠️  Warnings: {len(self.warnings)}/{total_checks}")
        if self.checks_failed:
            print(f"❌ Failed:   {self.checks_failed}/{total_checks}")

        if self.warnings:
            print(f"\n⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"   • {warning}")

        print()

        if self.checks_failed > 0:
            print("❌ SYSTEM NOT READY - Fix errors above before proceeding")
            return False
        elif self.warnings:
            print("⚠️  SYSTEM OPERATIONAL - But has warnings (may need attention)")
            return True
        else:
            print("✅ SYSTEM READY - All checks passed!")
            return True


def main():
    """Run health check."""
    checker = HealthCheck()
    success = checker.run_all_checks()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
