"""
Validation utilities for Clara AI Automation Pipeline.
Provides JSON schema validation and data quality checks.
"""

import json
from typing import Dict, Any, List, Tuple
from pathlib import Path

from schemas import (
    AccountMemo,
    RetellAgentSpec,
    Changelog,
    validate_account_memo,
    validate_agent_spec,
    validate_changelog
)
from logger import get_validation_logger

logger = get_validation_logger()


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


def validate_json_file(file_path: Path, schema_type: str) -> Tuple[bool, Any, List[str]]:
    """
    Validate a JSON file against a schema.

    Args:
        file_path: Path to the JSON file
        schema_type: Type of schema ('memo', 'agent', 'changelog')

    Returns:
        Tuple of (is_valid, parsed_object, errors)
    """
    errors = []

    try:
        # Read the file
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Validate against schema
        if schema_type == 'memo':
            obj = validate_account_memo(data)
        elif schema_type == 'agent':
            obj = validate_agent_spec(data)
        elif schema_type == 'changelog':
            obj = validate_changelog(data)
        else:
            raise ValueError(f"Unknown schema type: {schema_type}")

        logger.info(f"✅ {file_path.name} validated successfully as {schema_type}")
        return True, obj, []

    except json.JSONDecodeError as e:
        error_msg = f"Invalid JSON: {str(e)}"
        errors.append(error_msg)
        logger.error(f"❌ {file_path.name}: {error_msg}")
        return False, None, errors

    except Exception as e:
        error_msg = f"Validation error: {str(e)}"
        errors.append(error_msg)
        logger.error(f"❌ {file_path.name}: {error_msg}")
        return False, None, errors


def validate_memo_data_quality(memo: AccountMemo) -> List[str]:
    """
    Check data quality of an account memo.
    Returns list of warnings (not errors).

    Args:
        memo: AccountMemo object

    Returns:
        List of warning messages
    """
    warnings = []

    # Check if critical fields are missing
    if not memo.business_hours or not memo.business_hours.start:
        warnings.append("Business hours not specified")

    if not memo.services_supported or len(memo.services_supported) == 0:
        warnings.append("No services listed")

    if not memo.emergency_definition or len(memo.emergency_definition) == 0:
        warnings.append("Emergency definition not provided")

    if not memo.emergency_routing_rules or not memo.emergency_routing_rules.primary_contact:
        warnings.append("No emergency contact specified")

    # Check if unknowns are properly flagged
    if len(memo.questions_or_unknowns) > 5:
        warnings.append(f"High number of unknowns ({len(memo.questions_or_unknowns)})")

    # V2 should have fewer unknowns than v1
    if memo.version == "v2" and len(memo.questions_or_unknowns) > 3:
        warnings.append("V2 memo still has significant unknowns")

    return warnings


def validate_agent_spec_safety(spec: RetellAgentSpec) -> List[str]:
    """
    Check that agent spec follows safety requirements.

    Args:
        spec: RetellAgentSpec object

    Returns:
        List of safety violation messages
    """
    violations = []

    # Check that system prompt doesn't expose internal implementation
    forbidden_terms = [
        "function call",
        "API call",
        "tool call",
        "execute function",
        "invoke tool"
    ]

    prompt_lower = spec.system_prompt.lower()
    for term in forbidden_terms:
        if term in prompt_lower:
            violations.append(f"System prompt contains forbidden term: '{term}'")

    # Check that transfer fail protocol exists
    if not spec.transfer_fail_protocol or len(spec.transfer_fail_protocol) < 10:
        violations.append("Missing or incomplete transfer fail protocol")

    # Check that transfer protocol exists
    if not spec.call_transfer_protocol or len(spec.call_transfer_protocol) < 10:
        violations.append("Missing or incomplete call transfer protocol")

    return violations


def check_no_hallucination(memo: AccountMemo) -> bool:
    """
    Verify that unknown fields are properly flagged instead of hallucinated.

    Args:
        memo: AccountMemo object

    Returns:
        True if no hallucination detected, False otherwise
    """
    # If critical fields are None, they should be in questions_or_unknowns
    checks = []

    if not memo.business_hours or not memo.business_hours.start:
        has_unknown = any("business hours" in q.lower() or "hours" in q.lower()
                         for q in memo.questions_or_unknowns)
        if not has_unknown:
            logger.warning("Business hours missing but not flagged in unknowns")
            checks.append(False)

    if not memo.emergency_routing_rules or not memo.emergency_routing_rules.primary_contact:
        has_unknown = any("emergency" in q.lower() and "contact" in q.lower()
                         for q in memo.questions_or_unknowns)
        if not has_unknown:
            logger.warning("Emergency contact missing but not flagged in unknowns")
            checks.append(False)

    return all(checks) if checks else True


def validate_changelog_completeness(changelog: Changelog, v1_memo: AccountMemo, v2_memo: AccountMemo) -> List[str]:
    """
    Verify that changelog captures all changes between v1 and v2.

    Args:
        changelog: Changelog object
        v1_memo: Original v1 memo
        v2_memo: Updated v2 memo

    Returns:
        List of missing changes
    """
    issues = []

    # This is a simplified check - in production, you'd do deep comparison
    if len(changelog.changes) == 0:
        issues.append("Changelog is empty but versions differ")

    # Check that version transition makes sense
    if changelog.from_version != v1_memo.version:
        issues.append(f"Changelog from_version ({changelog.from_version}) doesn't match v1 memo ({v1_memo.version})")

    if changelog.to_version != v2_memo.version:
        issues.append(f"Changelog to_version ({changelog.to_version}) doesn't match v2 memo ({v2_memo.version})")

    # Check that unknowns decreased
    if len(v2_memo.questions_or_unknowns) > len(v1_memo.questions_or_unknowns):
        issues.append("V2 has MORE unknowns than V1 - onboarding should reduce unknowns")

    return issues


if __name__ == "__main__":
    # Test validation
    from schemas import Version, BusinessHours

    print("Testing validators...")

    # Test memo validation
    memo = AccountMemo(
        account_id="test-account",
        company_name="Test Company",
        version=Version.V1,
        questions_or_unknowns=["missing business hours"]
    )

    warnings = validate_memo_data_quality(memo)
    print(f"✅ Memo validation warnings: {len(warnings)}")
    for w in warnings:
        print(f"  ⚠️  {w}")

    # Test agent spec safety
    spec = RetellAgentSpec(
        agent_name="Clara - Test",
        system_prompt="You are Clara. When transferring calls, use the function call API.",
        version=Version.V1
    )

    violations = validate_agent_spec_safety(spec)
    print(f"\n✅ Agent safety violations: {len(violations)}")
    for v in violations:
        print(f"  ❌ {v}")

    print("\n✅ Validators test complete!")
