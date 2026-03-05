"""
Apply onboarding updates to v1 memo to create v2 memo.
Generate changelog tracking all changes.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from copy import deepcopy

from schemas import (
    AccountMemo,
    Changelog,
    ChangelogEntry,
    Version,
    validate_account_memo,
    validate_changelog
)
from validators import validate_changelog_completeness
from logger import get_extraction_logger

logger = get_extraction_logger()


class UpdateMerger:
    """Merge onboarding updates with v1 memo to create v2."""

    def merge_to_v2(
        self,
        v1_memo: Dict[str, Any],
        onboarding_updates: Dict[str, Any]
    ) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Merge v1 memo with onboarding updates to create v2 memo and changelog.

        Args:
            v1_memo: Original v1 Account Memo
            onboarding_updates: Updates from onboarding call

        Returns:
            Tuple of (v2_memo, changelog)
        """
        logger.info(f"Merging v1 with onboarding updates for {v1_memo['account_id']}...")

        # Start with v1 as base
        v2_memo = deepcopy(v1_memo)
        changes: List[Dict[str, Any]] = []

        # Apply updates
        updates = onboarding_updates.get("updates", {})

        for field, new_value in updates.items():
            if new_value is not None:  # Only apply non-null updates
                old_value = v2_memo.get(field)

                # Handle nested objects
                if isinstance(new_value, dict) and isinstance(old_value, dict):
                    nested_changes = self._merge_nested(field, old_value, new_value)
                    changes.extend(nested_changes)
                    v2_memo[field] = self._deep_merge(old_value, new_value)

                # Handle lists (replace or extend)
                elif isinstance(new_value, list):
                    if field == "questions_or_unknowns":
                        # For unknowns, replace with remaining unknowns
                        v2_memo[field] = onboarding_updates.get("remaining_unknowns", [])
                        changes.append({
                            "field": field,
                            "old_value": old_value,
                            "new_value": v2_memo[field],
                            "reason": "Updated based on onboarding call"
                        })
                    else:
                        # For other lists, replace completely
                        v2_memo[field] = new_value
                        if old_value != new_value:
                            changes.append({
                                "field": field,
                                "old_value": old_value,
                                "new_value": new_value,
                                "reason": "Updated from onboarding call"
                            })

                # Handle simple values
                elif old_value != new_value:
                    v2_memo[field] = new_value
                    changes.append({
                        "field": field,
                        "old_value": old_value,
                        "new_value": new_value,
                        "reason": "Updated from onboarding call"
                    })

        # Add changes from resolved unknowns
        for resolved in onboarding_updates.get("resolved_unknowns", []):
            changes.append({
                "field": "resolved_unknown",
                "old_value": resolved["v1_unknown"],
                "new_value": resolved["resolution"],
                "reason": f"Resolved in onboarding: {resolved.get('source', 'N/A')}"
            })

        # Update remaining unknowns
        remaining = onboarding_updates.get("remaining_unknowns", [])
        if remaining != v2_memo.get("questions_or_unknowns"):
            old_unknowns = v2_memo.get("questions_or_unknowns", [])
            v2_memo["questions_or_unknowns"] = remaining
            changes.append({
                "field": "questions_or_unknowns",
                "old_value": old_unknowns,
                "new_value": remaining,
                "reason": f"Resolved {len(old_unknowns) - len(remaining)} unknowns in onboarding"
            })

        # Update version and timestamp
        v2_memo["version"] = "v2"
        v2_memo["last_updated"] = datetime.utcnow().isoformat()

        # Validate v2 memo
        logger.info("Validating v2 memo schema...")
        v2_obj = validate_account_memo(v2_memo)

        # Build changelog
        changelog = self._build_changelog(
            v1_memo,
            v2_memo,
            changes,
            onboarding_updates
        )

        # Validate changelog
        logger.info("Validating changelog...")
        v1_obj = validate_account_memo(v1_memo)
        validation_issues = validate_changelog_completeness(changelog, v1_obj, v2_obj)

        if validation_issues:
            logger.warning(f"⚠️  Changelog validation issues ({len(validation_issues)}):")
            for issue in validation_issues:
                logger.warning(f"  - {issue}")

        logger.info(f"✅ Created v2 memo with {len(changes)} changes")
        logger.info(f"   Resolved unknowns: {len(onboarding_updates.get('resolved_unknowns', []))}")
        logger.info(f"   Remaining unknowns: {len(remaining)}")

        return v2_memo, changelog.model_dump()

    def _merge_nested(
        self,
        parent_field: str,
        old_dict: Dict[str, Any],
        new_dict: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Track changes in nested dictionaries."""
        changes = []

        for key, new_value in new_dict.items():
            old_value = old_dict.get(key)
            field_path = f"{parent_field}.{key}"

            if old_value != new_value:
                changes.append({
                    "field": field_path,
                    "old_value": old_value,
                    "new_value": new_value,
                    "reason": "Updated from onboarding call"
                })

        return changes

    def _deep_merge(self, old_dict: Dict[str, Any], new_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries."""
        result = deepcopy(old_dict)

        for key, value in new_dict.items():
            if value is not None:  # Only merge non-null values
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = self._deep_merge(result[key], value)
                else:
                    result[key] = value

        return result

    def _build_changelog(
        self,
        v1_memo: Dict[str, Any],
        v2_memo: Dict[str, Any],
        changes: List[Dict[str, Any]],
        onboarding_updates: Dict[str, Any]
    ) -> Changelog:
        """Build changelog object."""

        # Convert changes to ChangelogEntry objects
        changelog_entries = [
            ChangelogEntry(
                field=change["field"],
                old_value=change.get("old_value"),
                new_value=change.get("new_value"),
                reason=change.get("reason", "Updated in onboarding")
            )
            for change in changes
        ]

        # Generate prompt diff summary
        prompt_diff = self._generate_prompt_diff(onboarding_updates)

        # Create changelog
        changelog = Changelog(
            account_id=v1_memo["account_id"],
            from_version=Version.V1,
            to_version=Version.V2,
            timestamp=datetime.utcnow().isoformat(),
            changes=changelog_entries,
            prompt_diff=prompt_diff
        )

        return changelog

    def _generate_prompt_diff(self, onboarding_updates: Dict[str, Any]) -> str:
        """Generate human-readable summary of prompt changes."""
        new_info = onboarding_updates.get("new_information", [])
        resolved = onboarding_updates.get("resolved_unknowns", [])

        diff_parts = []

        if resolved:
            diff_parts.append(f"Resolved {len(resolved)} unknowns:")
            for r in resolved[:3]:  # Show first 3
                diff_parts.append(f"  - {r['v1_unknown']} → {r['resolution'][:50]}...")
            if len(resolved) > 3:
                diff_parts.append(f"  ... and {len(resolved) - 3} more")

        if new_info:
            diff_parts.append(f"\nAdded {len(new_info)} new details:")
            for info in new_info[:3]:  # Show first 3
                diff_parts.append(f"  - {info}")
            if len(new_info) > 3:
                diff_parts.append(f"  ... and {len(new_info) - 3} more")

        return "\n".join(diff_parts) if diff_parts else "No significant prompt changes"


def apply_onboarding_updates(
    v1_memo_path: Path,
    updates_path: Path,
    v2_output_path: Optional[Path] = None,
    changelog_output_path: Optional[Path] = None
) -> tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Apply onboarding updates to v1 memo.

    Args:
        v1_memo_path: Path to v1 memo JSON
        updates_path: Path to onboarding updates JSON
        v2_output_path: Optional path to save v2 memo
        changelog_output_path: Optional path to save changelog

    Returns:
        Tuple of (v2_memo, changelog)
    """
    logger.info(f"Applying updates: {v1_memo_path.name} + {updates_path.name}")

    # Load v1 memo
    with open(v1_memo_path, 'r', encoding='utf-8') as f:
        v1_memo = json.load(f)

    # Load updates
    with open(updates_path, 'r', encoding='utf-8') as f:
        updates = json.load(f)

    # Merge
    merger = UpdateMerger()
    v2_memo, changelog = merger.merge_to_v2(v1_memo, updates)

    # Save v2 memo
    if v2_output_path:
        v2_output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(v2_output_path, 'w', encoding='utf-8') as f:
            json.dump(v2_memo, f, indent=2)
        logger.info(f"✅ Saved v2 memo to: {v2_output_path}")

    # Save changelog
    if changelog_output_path:
        changelog_output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(changelog_output_path, 'w', encoding='utf-8') as f:
            json.dump(changelog, f, indent=2)
        logger.info(f"✅ Saved changelog to: {changelog_output_path}")

    return v2_memo, changelog


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python apply_updates.py <v1_memo_path> <updates_path> [v2_output_path] [changelog_output_path]")
        sys.exit(1)

    v1_path = Path(sys.argv[1])
    updates_path = Path(sys.argv[2])
    v2_path = Path(sys.argv[3]) if len(sys.argv) > 3 else None
    changelog_path = Path(sys.argv[4]) if len(sys.argv) > 4 else None

    v2, changelog = apply_onboarding_updates(v1_path, updates_path, v2_path, changelog_path)

    print("\n=== V2 MEMO ===")
    print(json.dumps(v2, indent=2))
    print("\n=== CHANGELOG ===")
    print(json.dumps(changelog, indent=2))
