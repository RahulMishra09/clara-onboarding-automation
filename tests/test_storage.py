"""
Test suite for storage layer.
"""

import pytest
import sys
import json
import tempfile
from pathlib import Path
from datetime import datetime

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from storage import AccountStorage


@pytest.fixture
def temp_storage():
    """Create a temporary storage directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = AccountStorage(base_dir=Path(tmpdir))
        yield storage


@pytest.fixture
def sample_v1_memo():
    """Sample v1 memo for testing."""
    return {
        "account_id": "test-account",
        "company_name": "Test Company",
        "version": "v1",
        "questions_or_unknowns": ["missing: business hours"],
        "last_updated": datetime.utcnow().isoformat()
    }


@pytest.fixture
def sample_v2_memo():
    """Sample v2 memo for testing."""
    return {
        "account_id": "test-account",
        "company_name": "Test Company",
        "business_hours": {
            "days": ["Monday", "Tuesday"],
            "start": "08:00",
            "end": "17:00"
        },
        "version": "v2",
        "questions_or_unknowns": [],
        "last_updated": datetime.utcnow().isoformat()
    }


@pytest.fixture
def sample_agent_spec():
    """Sample agent spec for testing."""
    return {
        "agent_name": "Clara - Test Company",
        "system_prompt": "You are Clara.",
        "version": "v1",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }


class TestAccountStorage:
    """Test AccountStorage class."""

    def test_storage_initialization(self, temp_storage):
        """Test storage initializes correctly."""
        assert temp_storage.base_dir.exists()

    def test_save_and_load_v1_memo(self, temp_storage, sample_v1_memo):
        """Test saving and loading v1 memo."""
        # Save
        path = temp_storage.save_v1_memo(sample_v1_memo)
        assert path.exists()

        # Load
        loaded = temp_storage.load_v1_memo("test-account")
        assert loaded is not None
        assert loaded["account_id"] == "test-account"
        assert loaded["company_name"] == "Test Company"

    def test_save_and_load_v2_memo(self, temp_storage, sample_v2_memo):
        """Test saving and loading v2 memo."""
        # Save
        path = temp_storage.save_v2_memo(sample_v2_memo)
        assert path.exists()

        # Load
        loaded = temp_storage.load_v2_memo("test-account")
        assert loaded is not None
        assert loaded["version"] == "v2"
        assert loaded["business_hours"] is not None

    def test_save_and_load_agent_spec(self, temp_storage, sample_agent_spec):
        """Test saving and loading agent spec."""
        # Save
        path = temp_storage.save_agent_spec("test-account", "v1", sample_agent_spec)
        assert path.exists()

        # Load
        loaded = temp_storage.load_agent_spec("test-account", "v1")
        assert loaded is not None
        assert loaded["agent_name"] == "Clara - Test Company"

    def test_save_changelog(self, temp_storage):
        """Test saving changelog."""
        changelog = {
            "account_id": "test-account",
            "from_version": "v1",
            "to_version": "v2",
            "timestamp": datetime.utcnow().isoformat(),
            "changes": [
                {
                    "field": "business_hours",
                    "old_value": None,
                    "new_value": {"start": "08:00"},
                    "reason": "Onboarding"
                }
            ]
        }

        path = temp_storage.save_changelog(changelog)
        assert path.exists()

        loaded = temp_storage.load_changelog("test-account")
        assert loaded is not None
        assert len(loaded["changes"]) == 1

    def test_save_metadata(self, temp_storage):
        """Test saving metadata."""
        metadata = {
            "account_id": "test-account",
            "company_name": "Test Company",
            "processing_status": "v1_complete",
            "last_processed": datetime.utcnow().isoformat()
        }

        path = temp_storage.save_metadata(metadata)
        assert path.exists()

        loaded = temp_storage.load_metadata("test-account")
        assert loaded is not None
        assert loaded["processing_status"] == "v1_complete"

    def test_list_accounts(self, temp_storage, sample_v1_memo):
        """Test listing accounts."""
        # Initially empty
        accounts = temp_storage.list_accounts()
        assert len(accounts) == 0

        # Add an account
        temp_storage.save_v1_memo(sample_v1_memo)

        # Should now have one account
        accounts = temp_storage.list_accounts()
        assert len(accounts) == 1
        assert "test-account" in accounts

    def test_account_exists(self, temp_storage, sample_v1_memo):
        """Test checking if account exists."""
        assert not temp_storage.account_exists("test-account")

        temp_storage.save_v1_memo(sample_v1_memo)

        assert temp_storage.account_exists("test-account")

    def test_has_v1(self, temp_storage, sample_v1_memo):
        """Test checking if account has v1."""
        assert not temp_storage.has_v1("test-account")

        temp_storage.save_v1_memo(sample_v1_memo)

        assert temp_storage.has_v1("test-account")

    def test_has_v2(self, temp_storage, sample_v2_memo):
        """Test checking if account has v2."""
        assert not temp_storage.has_v2("test-account")

        temp_storage.save_v2_memo(sample_v2_memo)

        assert temp_storage.has_v2("test-account")

    def test_get_account_status(self, temp_storage, sample_v1_memo, sample_agent_spec):
        """Test getting account status."""
        # Initially no data
        status = temp_storage.get_account_status("test-account")
        assert status["exists"] is False
        assert status["has_v1_memo"] is False

        # Add v1 memo
        temp_storage.save_v1_memo(sample_v1_memo)
        status = temp_storage.get_account_status("test-account")
        assert status["exists"] is True
        assert status["has_v1_memo"] is True
        assert status["has_v1_agent"] is False

        # Add v1 agent spec
        temp_storage.save_agent_spec("test-account", "v1", sample_agent_spec)
        status = temp_storage.get_account_status("test-account")
        assert status["has_v1_agent"] is True

    def test_get_storage_summary(self, temp_storage, sample_v1_memo, sample_v2_memo):
        """Test getting storage summary."""
        # Empty storage
        summary = temp_storage.get_storage_summary()
        assert summary["total_accounts"] == 0

        # Add v1
        temp_storage.save_v1_memo(sample_v1_memo)
        summary = temp_storage.get_storage_summary()
        assert summary["total_accounts"] == 1
        assert summary["accounts_with_v1"] == 1
        assert summary["accounts_with_v2"] == 0

        # Add v2
        temp_storage.save_v2_memo(sample_v2_memo)
        summary = temp_storage.get_storage_summary()
        assert summary["accounts_with_v2"] == 1

    def test_load_nonexistent_memo(self, temp_storage):
        """Test loading non-existent memo returns None."""
        loaded = temp_storage.load_v1_memo("nonexistent")
        assert loaded is None

    def test_directory_structure(self, temp_storage, sample_v1_memo):
        """Test that directory structure is created correctly."""
        temp_storage.save_v1_memo(sample_v1_memo)

        account_dir = temp_storage.get_account_dir("test-account")
        v1_dir = temp_storage.get_version_dir("test-account", "v1")

        assert account_dir.exists()
        assert v1_dir.exists()
        assert (v1_dir / "memo.json").exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
