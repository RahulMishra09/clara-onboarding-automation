"""
Test suite for Clara AI schemas and validation.
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from schemas import (
    AccountMemo,
    RetellAgentSpec,
    Changelog,
    ChangelogEntry,
    ProcessingMetadata,
    Version,
    BusinessHours,
    EmergencyRoutingRules,
    validate_account_memo,
    validate_agent_spec,
    validate_changelog
)


class TestAccountMemo:
    """Test AccountMemo schema."""

    def test_valid_v1_memo(self):
        """Test creating a valid v1 memo."""
        memo = AccountMemo(
            account_id="test-account",
            company_name="Test Company",
            version=Version.V1,
            questions_or_unknowns=["missing: business hours"]
        )

        assert memo.account_id == "test-account"
        assert memo.company_name == "Test Company"
        assert memo.version == Version.V1
        assert len(memo.questions_or_unknowns) == 1

    def test_valid_v2_memo_with_business_hours(self):
        """Test creating a v2 memo with complete data."""
        memo = AccountMemo(
            account_id="test-account",
            company_name="Test Company",
            business_hours=BusinessHours(
                days=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
                start="08:00",
                end="17:00",
                timezone="America/New_York"
            ),
            services_supported=["fire protection", "sprinkler systems"],
            emergency_definition=["sprinkler leak", "fire alarm"],
            version=Version.V2,
            questions_or_unknowns=[]
        )

        assert memo.version == Version.V2
        assert memo.business_hours is not None
        assert memo.business_hours.start == "08:00"
        assert len(memo.services_supported) == 2
        assert len(memo.questions_or_unknowns) == 0

    def test_memo_with_integration_constraints(self):
        """Test memo with integration constraints."""
        memo = AccountMemo(
            account_id="test-account",
            company_name="Test Company",
            version=Version.V1,
            integration_constraints=[
                "Never create sprinkler jobs in ServiceTrade",
                "Only create fire alarm tickets"
            ],
            questions_or_unknowns=[]
        )

        assert len(memo.integration_constraints) == 2
        assert "ServiceTrade" in memo.integration_constraints[0]

    def test_memo_validation(self):
        """Test memo validation function."""
        memo_data = {
            "account_id": "test-validation",
            "company_name": "Validation Test Co",
            "version": "v1",
            "questions_or_unknowns": ["test unknown"],
            "last_updated": datetime.utcnow().isoformat()
        }

        memo = validate_account_memo(memo_data)
        assert isinstance(memo, AccountMemo)
        assert memo.account_id == "test-validation"


class TestRetellAgentSpec:
    """Test RetellAgentSpec schema."""

    def test_valid_agent_spec(self):
        """Test creating a valid agent spec."""
        spec = RetellAgentSpec(
            agent_name="Clara - Test Company",
            system_prompt="You are Clara, the AI receptionist for Test Company.",
            version=Version.V1
        )

        assert spec.agent_name == "Clara - Test Company"
        assert "Clara" in spec.system_prompt
        assert spec.version == Version.V1
        assert spec.voice_style == "professional, warm, efficient"  # default

    def test_agent_spec_with_protocols(self):
        """Test agent spec with transfer protocols."""
        spec = RetellAgentSpec(
            agent_name="Clara - Test Company",
            system_prompt="Test prompt",
            call_transfer_protocol="1. Announce transfer\n2. Attempt transfer",
            transfer_fail_protocol="1. Apologize\n2. Take message",
            version=Version.V1
        )

        assert spec.call_transfer_protocol is not None
        assert spec.transfer_fail_protocol is not None
        assert "Announce transfer" in spec.call_transfer_protocol
        assert "Apologize" in spec.transfer_fail_protocol

    def test_agent_spec_validation(self):
        """Test agent spec validation function."""
        spec_data = {
            "agent_name": "Clara - Test",
            "system_prompt": "Test prompt",
            "version": "v1",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }

        spec = validate_agent_spec(spec_data)
        assert isinstance(spec, RetellAgentSpec)
        assert spec.agent_name == "Clara - Test"


class TestChangelog:
    """Test Changelog schema."""

    def test_valid_changelog(self):
        """Test creating a valid changelog."""
        changelog = Changelog(
            account_id="test-account",
            from_version=Version.V1,
            to_version=Version.V2,
            changes=[
                ChangelogEntry(
                    field="business_hours.start",
                    old_value=None,
                    new_value="08:00",
                    reason="Confirmed in onboarding"
                )
            ]
        )

        assert changelog.account_id == "test-account"
        assert changelog.from_version == Version.V1
        assert changelog.to_version == Version.V2
        assert len(changelog.changes) == 1
        assert changelog.changes[0].field == "business_hours.start"

    def test_changelog_with_multiple_changes(self):
        """Test changelog with multiple changes."""
        changes = [
            ChangelogEntry(
                field="business_hours.start",
                old_value=None,
                new_value="08:00",
                reason="Onboarding"
            ),
            ChangelogEntry(
                field="emergency_routing_rules.primary_contact",
                old_value="unknown",
                new_value="John: 555-1234",
                reason="Onboarding"
            ),
            ChangelogEntry(
                field="questions_or_unknowns",
                old_value=["missing: hours", "missing: contact"],
                new_value=["missing: contact"],
                reason="Resolved business hours"
            )
        ]

        changelog = Changelog(
            account_id="test-account",
            from_version=Version.V1,
            to_version=Version.V2,
            changes=changes,
            prompt_diff="Resolved 1 unknown, added 1 contact detail"
        )

        assert len(changelog.changes) == 3
        assert changelog.prompt_diff is not None


class TestProcessingMetadata:
    """Test ProcessingMetadata schema."""

    def test_valid_metadata(self):
        """Test creating valid metadata."""
        metadata = ProcessingMetadata(
            account_id="test-account",
            company_name="Test Company",
            processing_status="v1_complete"
        )

        assert metadata.account_id == "test-account"
        assert metadata.processing_status == "v1_complete"

    def test_metadata_with_paths(self):
        """Test metadata with file paths."""
        metadata = ProcessingMetadata(
            account_id="test-account",
            company_name="Test Company",
            demo_transcript_path="data/demo_calls/test.txt",
            onboarding_transcript_path="data/onboarding_calls/test.txt",
            v1_created_at=datetime.utcnow().isoformat(),
            v2_created_at=datetime.utcnow().isoformat(),
            processing_status="v2_complete"
        )

        assert metadata.demo_transcript_path is not None
        assert metadata.onboarding_transcript_path is not None
        assert metadata.v1_created_at is not None
        assert metadata.v2_created_at is not None


class TestBusinessHours:
    """Test BusinessHours nested schema."""

    def test_valid_business_hours(self):
        """Test creating valid business hours."""
        hours = BusinessHours(
            days=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
            start="08:00",
            end="17:00",
            timezone="America/Chicago"
        )

        assert len(hours.days) == 5
        assert hours.start == "08:00"
        assert hours.end == "17:00"
        assert "Chicago" in hours.timezone

    def test_business_hours_with_weekend(self):
        """Test business hours including weekend."""
        hours = BusinessHours(
            days=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
            start="09:00",
            end="14:00",
            timezone="America/New_York"
        )

        assert len(hours.days) == 6
        assert "Saturday" in hours.days


class TestEmergencyRoutingRules:
    """Test EmergencyRoutingRules nested schema."""

    def test_valid_emergency_routing(self):
        """Test creating valid emergency routing rules."""
        routing = EmergencyRoutingRules(
            primary_contact="John Smith: 555-1234",
            secondary_contact="Dispatch: 555-FIRE",
            order=["try primary for 30s", "try secondary", "voicemail"],
            fallback="Leave message, on-call will respond within 15 min"
        )

        assert routing.primary_contact is not None
        assert routing.secondary_contact is not None
        assert len(routing.order) == 3
        assert routing.fallback is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
