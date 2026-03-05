"""
Storage layer for Clara AI Automation Pipeline.
Supports local JSON file storage with Git versioning.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import shutil

from schemas import (
    AccountMemo,
    RetellAgentSpec,
    Changelog,
    ProcessingMetadata,
    Version
)
from logger import get_processing_logger
from config import OUTPUT_DIR

logger = get_processing_logger()


class AccountStorage:
    """Manages storage of account memos, agent specs, and changelogs."""

    def __init__(self, base_dir: Optional[Path] = None):
        """
        Initialize storage manager.

        Args:
            base_dir: Base directory for outputs (defaults to config.OUTPUT_DIR)
        """
        self.base_dir = base_dir or OUTPUT_DIR
        self.base_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Storage initialized: {self.base_dir}")

    def get_account_dir(self, account_id: str) -> Path:
        """Get the directory for a specific account."""
        account_dir = self.base_dir / account_id
        account_dir.mkdir(parents=True, exist_ok=True)
        return account_dir

    def get_version_dir(self, account_id: str, version: str) -> Path:
        """Get the version directory (v1 or v2) for an account."""
        version_dir = self.get_account_dir(account_id) / version
        version_dir.mkdir(parents=True, exist_ok=True)
        return version_dir

    # ===== Save Operations =====

    def save_v1_memo(self, memo: Dict[str, Any]) -> Path:
        """
        Save v1 account memo.

        Args:
            memo: Account memo dictionary

        Returns:
            Path to saved file
        """
        account_id = memo["account_id"]
        version_dir = self.get_version_dir(account_id, "v1")
        memo_path = version_dir / "memo.json"

        with open(memo_path, 'w', encoding='utf-8') as f:
            json.dump(memo, f, indent=2)

        logger.info(f"✅ Saved v1 memo: {memo_path}")
        return memo_path

    def save_v2_memo(self, memo: Dict[str, Any]) -> Path:
        """
        Save v2 account memo.

        Args:
            memo: Account memo dictionary

        Returns:
            Path to saved file
        """
        account_id = memo["account_id"]
        version_dir = self.get_version_dir(account_id, "v2")
        memo_path = version_dir / "memo.json"

        with open(memo_path, 'w', encoding='utf-8') as f:
            json.dump(memo, f, indent=2)

        logger.info(f"✅ Saved v2 memo: {memo_path}")
        return memo_path

    def save_agent_spec(self, account_id: str, version: str, spec: Dict[str, Any]) -> Path:
        """
        Save agent spec.

        Args:
            account_id: Account identifier
            version: Version (v1 or v2)
            spec: Agent spec dictionary

        Returns:
            Path to saved file
        """
        version_dir = self.get_version_dir(account_id, version)
        spec_path = version_dir / "agent_spec.json"

        with open(spec_path, 'w', encoding='utf-8') as f:
            json.dump(spec, f, indent=2)

        logger.info(f"✅ Saved {version} agent spec: {spec_path}")
        return spec_path

    def save_changelog(self, changelog: Dict[str, Any]) -> Path:
        """
        Save changelog (v1 → v2).

        Args:
            changelog: Changelog dictionary

        Returns:
            Path to saved file
        """
        account_id = changelog["account_id"]
        version_dir = self.get_version_dir(account_id, "v2")
        changelog_path = version_dir / "changelog.json"

        with open(changelog_path, 'w', encoding='utf-8') as f:
            json.dump(changelog, f, indent=2)

        logger.info(f"✅ Saved changelog: {changelog_path}")
        return changelog_path

    def save_onboarding_updates(self, account_id: str, updates: Dict[str, Any]) -> Path:
        """
        Save raw onboarding updates (before merge).

        Args:
            account_id: Account identifier
            updates: Onboarding updates dictionary

        Returns:
            Path to saved file
        """
        version_dir = self.get_version_dir(account_id, "v2")
        updates_path = version_dir / "onboarding_updates.json"

        with open(updates_path, 'w', encoding='utf-8') as f:
            json.dump(updates, f, indent=2)

        logger.info(f"✅ Saved onboarding updates: {updates_path}")
        return updates_path

    def save_metadata(self, metadata: Dict[str, Any]) -> Path:
        """
        Save processing metadata for an account.

        Args:
            metadata: Metadata dictionary

        Returns:
            Path to saved file
        """
        account_id = metadata["account_id"]
        account_dir = self.get_account_dir(account_id)
        metadata_path = account_dir / "metadata.json"

        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"✅ Saved metadata: {metadata_path}")
        return metadata_path

    # ===== Load Operations =====

    def load_v1_memo(self, account_id: str) -> Optional[Dict[str, Any]]:
        """
        Load v1 account memo.

        Args:
            account_id: Account identifier

        Returns:
            Memo dictionary or None if not found
        """
        memo_path = self.get_version_dir(account_id, "v1") / "memo.json"

        if not memo_path.exists():
            logger.warning(f"⚠️  v1 memo not found: {memo_path}")
            return None

        with open(memo_path, 'r', encoding='utf-8') as f:
            memo = json.load(f)

        logger.info(f"✅ Loaded v1 memo: {memo_path}")
        return memo

    def load_v2_memo(self, account_id: str) -> Optional[Dict[str, Any]]:
        """
        Load v2 account memo.

        Args:
            account_id: Account identifier

        Returns:
            Memo dictionary or None if not found
        """
        memo_path = self.get_version_dir(account_id, "v2") / "memo.json"

        if not memo_path.exists():
            logger.warning(f"⚠️  v2 memo not found: {memo_path}")
            return None

        with open(memo_path, 'r', encoding='utf-8') as f:
            memo = json.load(f)

        logger.info(f"✅ Loaded v2 memo: {memo_path}")
        return memo

    def load_agent_spec(self, account_id: str, version: str) -> Optional[Dict[str, Any]]:
        """
        Load agent spec.

        Args:
            account_id: Account identifier
            version: Version (v1 or v2)

        Returns:
            Spec dictionary or None if not found
        """
        spec_path = self.get_version_dir(account_id, version) / "agent_spec.json"

        if not spec_path.exists():
            logger.warning(f"⚠️  {version} agent spec not found: {spec_path}")
            return None

        with open(spec_path, 'r', encoding='utf-8') as f:
            spec = json.load(f)

        logger.info(f"✅ Loaded {version} agent spec: {spec_path}")
        return spec

    def load_changelog(self, account_id: str) -> Optional[Dict[str, Any]]:
        """
        Load changelog.

        Args:
            account_id: Account identifier

        Returns:
            Changelog dictionary or None if not found
        """
        changelog_path = self.get_version_dir(account_id, "v2") / "changelog.json"

        if not changelog_path.exists():
            logger.warning(f"⚠️  Changelog not found: {changelog_path}")
            return None

        with open(changelog_path, 'r', encoding='utf-8') as f:
            changelog = json.load(f)

        logger.info(f"✅ Loaded changelog: {changelog_path}")
        return changelog

    def load_metadata(self, account_id: str) -> Optional[Dict[str, Any]]:
        """
        Load processing metadata.

        Args:
            account_id: Account identifier

        Returns:
            Metadata dictionary or None if not found
        """
        metadata_path = self.get_account_dir(account_id) / "metadata.json"

        if not metadata_path.exists():
            logger.warning(f"⚠️  Metadata not found: {metadata_path}")
            return None

        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        logger.info(f"✅ Loaded metadata: {metadata_path}")
        return metadata

    # ===== Query Operations =====

    def list_accounts(self) -> List[str]:
        """
        List all account IDs in storage.

        Returns:
            List of account IDs
        """
        if not self.base_dir.exists():
            return []

        accounts = [
            d.name for d in self.base_dir.iterdir()
            if d.is_dir() and not d.name.startswith('.')
        ]

        logger.info(f"Found {len(accounts)} accounts in storage")
        return sorted(accounts)

    def account_exists(self, account_id: str) -> bool:
        """Check if an account exists in storage."""
        return self.get_account_dir(account_id).exists()

    def has_v1(self, account_id: str) -> bool:
        """Check if account has v1 memo."""
        memo_path = self.get_version_dir(account_id, "v1") / "memo.json"
        return memo_path.exists()

    def has_v2(self, account_id: str) -> bool:
        """Check if account has v2 memo."""
        memo_path = self.get_version_dir(account_id, "v2") / "memo.json"
        return memo_path.exists()

    def get_account_status(self, account_id: str) -> Dict[str, bool]:
        """
        Get processing status for an account.

        Returns:
            Dictionary with status flags
        """
        return {
            "exists": self.account_exists(account_id),
            "has_v1_memo": self.has_v1(account_id),
            "has_v1_agent": (self.get_version_dir(account_id, "v1") / "agent_spec.json").exists(),
            "has_v2_memo": self.has_v2(account_id),
            "has_v2_agent": (self.get_version_dir(account_id, "v2") / "agent_spec.json").exists(),
            "has_changelog": (self.get_version_dir(account_id, "v2") / "changelog.json").exists()
        }

    # ===== Utility Operations =====

    def backup_account(self, account_id: str, backup_dir: Optional[Path] = None) -> Path:
        """
        Create a backup of an account's data.

        Args:
            account_id: Account identifier
            backup_dir: Optional backup directory

        Returns:
            Path to backup directory
        """
        account_dir = self.get_account_dir(account_id)

        if not account_dir.exists():
            raise ValueError(f"Account not found: {account_id}")

        if backup_dir is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = self.base_dir.parent / "backups" / f"{account_id}_{timestamp}"

        backup_dir.mkdir(parents=True, exist_ok=True)
        shutil.copytree(account_dir, backup_dir / account_id, dirs_exist_ok=True)

        logger.info(f"✅ Backed up account to: {backup_dir}")
        return backup_dir

    def get_storage_summary(self) -> Dict[str, Any]:
        """
        Get summary of all accounts in storage.

        Returns:
            Summary dictionary
        """
        accounts = self.list_accounts()

        summary = {
            "total_accounts": len(accounts),
            "accounts_with_v1": 0,
            "accounts_with_v2": 0,
            "accounts_complete": 0,
            "accounts": []
        }

        for account_id in accounts:
            status = self.get_account_status(account_id)

            if status["has_v1_memo"]:
                summary["accounts_with_v1"] += 1

            if status["has_v2_memo"]:
                summary["accounts_with_v2"] += 1

            if status["has_v2_agent"] and status["has_changelog"]:
                summary["accounts_complete"] += 1

            summary["accounts"].append({
                "account_id": account_id,
                "status": status
            })

        return summary


if __name__ == "__main__":
    # Test storage
    logger.info("Testing storage layer...")

    storage = AccountStorage()

    # Create test data
    test_memo = {
        "account_id": "test-storage",
        "company_name": "Test Storage Company",
        "version": "v1",
        "questions_or_unknowns": ["test unknown"],
        "last_updated": datetime.utcnow().isoformat()
    }

    # Save v1
    storage.save_v1_memo(test_memo)

    # Load v1
    loaded = storage.load_v1_memo("test-storage")
    assert loaded is not None
    assert loaded["company_name"] == "Test Storage Company"

    # Check status
    status = storage.get_account_status("test-storage")
    logger.info(f"Account status: {status}")

    # Get summary
    summary = storage.get_storage_summary()
    logger.info(f"Storage summary: {json.dumps(summary, indent=2)}")

    logger.info("✅ Storage layer test complete!")
