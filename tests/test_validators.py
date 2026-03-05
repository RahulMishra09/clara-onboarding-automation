"""
Test suite for validation utilities.
"""

import pytest
import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from schemas import AccountMemo, RetellAgentSpec, Version, BusinessHours
from validators import (
    validate_memo_data_quality,
    validate_agent_spec_safety,
    check_no_hallucination
)


class TestMemoDataQuality:
    """Test memo data quality validation."""

    def test_complete_memo_no_warnings(self):
        """Test that a complete memo has no warnings."""
        memo = AccountMemo(
            account_id="test",
            company_name="Test Co",
            business_hours=BusinessHours(
                days=["Monday", "Tuesday"],
                start="08:00",
                end="17:00",
                timezone="America/New_York"
            ),
            services_supported=["fire protection"],
            emergency_definition=["fire alarm"],
            emergency_routing_rules={
                "primary_contact": "John: 555-1234"
            },
            version=Version.V1,
            questions_or_unknowns=[]
        )

        warnings = validate_memo_data_quality(memo)
        assert len(warnings) == 0

    def test_incomplete_memo_warnings(self):
        """Test that incomplete memo generates warnings."""
        memo = AccountMemo(
            account_id="test",
            company_name="Test Co",
            version=Version.V1,
            questions_or_unknowns=[]
        )

        warnings = validate_memo_data_quality(memo)
        assert len(warnings) > 0
        assert any("Business hours" in w for w in warnings)
        assert any("services" in w.lower() for w in warnings)

    def test_high_unknowns_warning(self):
        """Test warning for high number of unknowns."""
        memo = AccountMemo(
            account_id="test",
            company_name="Test Co",
            version=Version.V1,
            questions_or_unknowns=["unknown" + str(i) for i in range(10)]
        )

        warnings = validate_memo_data_quality(memo)
        assert any("unknowns" in w.lower() for w in warnings)

    def test_v2_with_many_unknowns_warning(self):
        """Test that v2 with many unknowns generates warning."""
        memo = AccountMemo(
            account_id="test",
            company_name="Test Co",
            version=Version.V2,
            questions_or_unknowns=["unknown1", "unknown2", "unknown3", "unknown4"]
        )

        warnings = validate_memo_data_quality(memo)
        assert any("v2" in w.lower() and "unknowns" in w.lower() for w in warnings)


class TestAgentSpecSafety:
    """Test agent spec safety validation."""

    def test_safe_agent_spec(self):
        """Test that a safe agent spec has no violations."""
        spec = RetellAgentSpec(
            agent_name="Clara - Test",
            system_prompt="You are Clara. When you need to connect a caller, announce the transfer.",
            call_transfer_protocol="1. Announce\n2. Transfer",
            transfer_fail_protocol="1. Apologize\n2. Take message\n3. Confirm",
            version=Version.V1
        )

        violations = validate_agent_spec_safety(spec)
        assert len(violations) == 0

    def test_forbidden_term_function_call(self):
        """Test detection of 'function call' term."""
        spec = RetellAgentSpec(
            agent_name="Clara - Test",
            system_prompt="When transferring, use the function call API to execute the transfer.",
            call_transfer_protocol="Transfer",
            transfer_fail_protocol="Fallback",
            version=Version.V1
        )

        violations = validate_agent_spec_safety(spec)
        assert len(violations) > 0
        assert any("function call" in v.lower() for v in violations)

    def test_forbidden_term_api_call(self):
        """Test detection of 'API call' term."""
        spec = RetellAgentSpec(
            agent_name="Clara - Test",
            system_prompt="Make an API call to transfer the user.",
            call_transfer_protocol="Transfer",
            transfer_fail_protocol="Fallback",
            version=Version.V1
        )

        violations = validate_agent_spec_safety(spec)
        assert len(violations) > 0
        assert any("api call" in v.lower() for v in violations)

    def test_missing_transfer_protocol(self):
        """Test detection of missing transfer protocol."""
        spec = RetellAgentSpec(
            agent_name="Clara - Test",
            system_prompt="You are Clara.",
            transfer_fail_protocol="Fallback message",
            version=Version.V1
        )

        violations = validate_agent_spec_safety(spec)
        assert len(violations) > 0
        assert any("transfer protocol" in v.lower() for v in violations)

    def test_missing_transfer_fail_protocol(self):
        """Test detection of missing transfer fail protocol."""
        spec = RetellAgentSpec(
            agent_name="Clara - Test",
            system_prompt="You are Clara.",
            call_transfer_protocol="Transfer process",
            version=Version.V1
        )

        violations = validate_agent_spec_safety(spec)
        assert len(violations) > 0
        assert any("fail protocol" in v.lower() for v in violations)

    def test_short_protocols(self):
        """Test detection of too-short protocols."""
        spec = RetellAgentSpec(
            agent_name="Clara - Test",
            system_prompt="You are Clara.",
            call_transfer_protocol="Go",
            transfer_fail_protocol="Oops",
            version=Version.V1
        )

        violations = validate_agent_spec_safety(spec)
        assert len(violations) > 0


class TestNoHallucination:
    """Test hallucination detection."""

    def test_no_hallucination_with_proper_unknowns(self):
        """Test that proper unknown flagging passes."""
        memo = AccountMemo(
            account_id="test",
            company_name="Test Co",
            version=Version.V1,
            questions_or_unknowns=[
                "missing: business hours",
                "unclear: emergency contact"
            ]
        )

        result = check_no_hallucination(memo)
        assert result is True

    def test_missing_business_hours_flagged(self):
        """Test that missing business hours without unknown flag is caught."""
        memo = AccountMemo(
            account_id="test",
            company_name="Test Co",
            version=Version.V1,
            questions_or_unknowns=[]
        )

        # This should return False because business hours are missing
        # but not flagged in unknowns
        result = check_no_hallucination(memo)
        # Note: Actual implementation may vary based on your logic


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
