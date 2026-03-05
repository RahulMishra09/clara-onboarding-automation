"""
Pipeline B: Onboarding Call → v2 Agent
Processes onboarding call transcripts to update v1 to v2 and generate changelogs.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from extract_memo import MemoExtractor
from generate_prompt import PromptGenerator
from apply_updates import UpdateMerger
from storage import AccountStorage
from logger import get_processing_logger, log_section
from config import DATA_DIR

logger = get_processing_logger()


class PipelineB:
    """Pipeline B: Onboarding → v2 Account Memo + Agent Spec + Changelog"""

    def __init__(self):
        """Initialize pipeline components."""
        self.memo_extractor = MemoExtractor()
        self.prompt_generator = PromptGenerator()
        self.update_merger = UpdateMerger()
        self.storage = AccountStorage()
        logger.info("Pipeline B initialized")

    def process_onboarding_transcript(
        self,
        transcript_path: Path,
        account_id: Optional[str] = None,
        v1_memo_path: Optional[Path] = None,
        save_outputs: bool = True
    ) -> Dict[str, Any]:
        """
        Process an onboarding call transcript through Pipeline B.

        Args:
            transcript_path: Path to onboarding transcript file
            account_id: Optional account ID (will try to extract from transcript if not provided)
            v1_memo_path: Optional path to v1 memo (will load from storage if not provided)
            save_outputs: Whether to save outputs to storage

        Returns:
            Dictionary with processing results
        """
        log_section(logger, f"PIPELINE B: {transcript_path.name}")

        results = {
            "transcript_path": str(transcript_path),
            "status": "pending",
            "account_id": account_id,
            "onboarding_updates": None,
            "v2_memo": None,
            "v2_agent_spec": None,
            "changelog": None,
            "errors": [],
            "warnings": [],
            "started_at": datetime.utcnow().isoformat(),
            "completed_at": None
        }

        try:
            # Step 1: Read transcript
            logger.info(f"[1/7] Reading transcript: {transcript_path}")
            with open(transcript_path, 'r', encoding='utf-8') as f:
                transcript = f.read()

            if len(transcript.strip()) == 0:
                raise ValueError("Transcript file is empty")

            logger.info(f"✅ Transcript loaded ({len(transcript)} chars)")

            # Step 2: Load v1 memo
            logger.info("[2/7] Loading v1 memo...")

            if v1_memo_path:
                # Load from provided path
                with open(v1_memo_path, 'r', encoding='utf-8') as f:
                    v1_memo = json.load(f)
                account_id = v1_memo["account_id"]
                logger.info(f"✅ Loaded v1 memo from {v1_memo_path}")

            elif account_id:
                # Load from storage by account_id
                v1_memo = self.storage.load_v1_memo(account_id)
                if not v1_memo:
                    raise ValueError(f"v1 memo not found in storage for account: {account_id}")
                logger.info(f"✅ Loaded v1 memo from storage")

            else:
                # Try to extract account_id from transcript
                logger.info("No account_id provided, attempting to extract from transcript...")
                # This is a simplified approach - in production, you'd have better matching logic
                v1_memo = None
                accounts = self.storage.list_accounts()

                for acc_id in accounts:
                    test_memo = self.storage.load_v1_memo(acc_id)
                    if test_memo and test_memo["company_name"].lower() in transcript.lower():
                        v1_memo = test_memo
                        account_id = acc_id
                        logger.info(f"✅ Matched account: {account_id}")
                        break

                if not v1_memo:
                    raise ValueError(
                        "Could not find matching v1 memo. "
                        "Please provide account_id or v1_memo_path."
                    )

            results["account_id"] = account_id
            logger.info(f"   Account: {account_id}")
            logger.info(f"   Company: {v1_memo['company_name']}")
            logger.info(f"   v1 Unknowns: {len(v1_memo.get('questions_or_unknowns', []))}")

            # Step 3: Extract onboarding updates
            logger.info("[3/7] Extracting onboarding updates...")
            onboarding_updates = self.memo_extractor.extract_onboarding_updates(
                transcript,
                v1_memo
            )
            results["onboarding_updates"] = onboarding_updates

            logger.info(f"✅ Onboarding updates extracted")
            logger.info(f"   Resolved unknowns: {len(onboarding_updates.get('resolved_unknowns', []))}")
            logger.info(f"   New information: {len(onboarding_updates.get('new_information', []))}")
            logger.info(f"   Remaining unknowns: {len(onboarding_updates.get('remaining_unknowns', []))}")

            # Check if unknowns were reduced
            v1_unknown_count = len(v1_memo.get('questions_or_unknowns', []))
            v2_unknown_count = len(onboarding_updates.get('remaining_unknowns', []))

            if v2_unknown_count >= v1_unknown_count:
                warning = f"Unknowns not reduced (v1: {v1_unknown_count}, v2: {v2_unknown_count})"
                results["warnings"].append(warning)
                logger.warning(f"⚠️  {warning}")

            # Step 4: Merge to create v2 memo
            logger.info("[4/7] Merging v1 + updates → v2 memo...")
            v2_memo, changelog = self.update_merger.merge_to_v2(v1_memo, onboarding_updates)
            results["v2_memo"] = v2_memo
            results["changelog"] = changelog

            logger.info(f"✅ v2 memo created")
            logger.info(f"   Changes: {len(changelog['changes'])}")
            logger.info(f"   Final unknowns: {len(v2_memo.get('questions_or_unknowns', []))}")

            # Step 5: Generate v2 agent spec
            logger.info("[5/7] Generating v2 agent spec...")
            from schemas import AccountMemo
            memo_obj = AccountMemo(**v2_memo)
            agent_spec_obj = self.prompt_generator.generate_agent_spec(memo_obj)
            v2_agent_spec = agent_spec_obj.model_dump()
            results["v2_agent_spec"] = v2_agent_spec

            logger.info(f"✅ v2 agent spec generated ({len(agent_spec_obj.system_prompt)} chars)")

            # Step 6: Save outputs
            if save_outputs:
                logger.info("[6/7] Saving outputs to storage...")

                # Save onboarding updates (raw)
                updates_path = self.storage.save_onboarding_updates(account_id, onboarding_updates)
                results["onboarding_updates_path"] = str(updates_path)

                # Save v2 memo
                memo_path = self.storage.save_v2_memo(v2_memo)
                results["v2_memo_path"] = str(memo_path)

                # Save v2 agent spec
                spec_path = self.storage.save_agent_spec(account_id, "v2", v2_agent_spec)
                results["v2_agent_spec_path"] = str(spec_path)

                # Save changelog
                changelog_path = self.storage.save_changelog(changelog)
                results["changelog_path"] = str(changelog_path)

                # Update metadata
                metadata = self.storage.load_metadata(account_id) or {}
                metadata.update({
                    "account_id": account_id,
                    "company_name": v2_memo["company_name"],
                    "onboarding_transcript_path": str(transcript_path),
                    "v2_created_at": datetime.utcnow().isoformat(),
                    "processing_status": "v2_complete",
                    "error_message": None,
                    "last_processed": datetime.utcnow().isoformat()
                })
                metadata_path = self.storage.save_metadata(metadata)
                results["metadata_path"] = str(metadata_path)

                logger.info("✅ All outputs saved")
            else:
                logger.info("[6/7] Skipping save (save_outputs=False)")

            # Step 7: Finalize
            results["status"] = "success"
            results["completed_at"] = datetime.utcnow().isoformat()

            logger.info("[7/7] Pipeline B complete!")
            log_section(logger, "PIPELINE B: SUCCESS")

            return results

        except Exception as e:
            logger.error(f"❌ Pipeline B failed: {e}")
            results["status"] = "error"
            results["errors"].append(str(e))
            results["completed_at"] = datetime.utcnow().isoformat()

            # Save error metadata if we have an account_id
            if results["account_id"] and save_outputs:
                try:
                    metadata = self.storage.load_metadata(results["account_id"]) or {}
                    metadata.update({
                        "processing_status": "error",
                        "error_message": str(e),
                        "last_processed": datetime.utcnow().isoformat()
                    })
                    self.storage.save_metadata(metadata)
                except Exception as meta_error:
                    logger.error(f"Failed to save error metadata: {meta_error}")

            log_section(logger, "PIPELINE B: FAILED")
            return results


def process_onboarding_file(
    transcript_path: Path,
    account_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function to process a single onboarding transcript.

    Args:
        transcript_path: Path to onboarding transcript
        account_id: Optional account ID

    Returns:
        Processing results
    """
    pipeline = PipelineB()
    return pipeline.process_onboarding_transcript(transcript_path, account_id=account_id)


def process_all_onboardings(
    onboarding_dir: Optional[Path] = None,
    account_mapping: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Process all onboarding transcripts in a directory.

    Args:
        onboarding_dir: Directory containing onboarding transcripts
        account_mapping: Optional dict mapping filename → account_id

    Returns:
        Summary of processing results
    """
    if onboarding_dir is None:
        onboarding_dir = DATA_DIR / "onboarding_calls"

    if not onboarding_dir.exists():
        raise ValueError(f"Onboarding directory not found: {onboarding_dir}")

    log_section(logger, f"PROCESSING ALL ONBOARDINGS: {onboarding_dir}")

    # Find all transcript files
    transcript_files = list(onboarding_dir.glob("*.txt"))
    transcript_files.extend(onboarding_dir.glob("*.md"))

    logger.info(f"Found {len(transcript_files)} transcript files")

    if len(transcript_files) == 0:
        logger.warning("⚠️  No transcript files found")
        return {"status": "no_files", "results": []}

    # Process each transcript
    pipeline = PipelineB()
    results = []

    for i, transcript_path in enumerate(transcript_files, 1):
        logger.info(f"\n{'='*80}")
        logger.info(f"Processing {i}/{len(transcript_files)}: {transcript_path.name}")
        logger.info(f"{'='*80}\n")

        # Get account_id from mapping if provided
        account_id = None
        if account_mapping:
            account_id = account_mapping.get(transcript_path.name)

        try:
            result = pipeline.process_onboarding_transcript(
                transcript_path,
                account_id=account_id
            )
            results.append(result)
        except Exception as e:
            logger.error(f"❌ Failed to process {transcript_path.name}: {e}")
            results.append({
                "transcript_path": str(transcript_path),
                "status": "error",
                "errors": [str(e)]
            })

    # Generate summary
    summary = {
        "total_files": len(transcript_files),
        "successful": len([r for r in results if r["status"] == "success"]),
        "failed": len([r for r in results if r["status"] == "error"]),
        "results": results
    }

    log_section(logger, "BATCH PROCESSING SUMMARY")
    logger.info(f"Total: {summary['total_files']}")
    logger.info(f"✅ Success: {summary['successful']}")
    logger.info(f"❌ Failed: {summary['failed']}")

    return summary


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  Process single onboarding:")
        print("    python pipeline_b.py <transcript_path> [account_id]")
        print("  Process all onboardings:")
        print("    python pipeline_b.py --all [onboarding_dir]")
        sys.exit(1)

    if sys.argv[1] == "--all":
        # Process all onboardings
        onboarding_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else None
        summary = process_all_onboardings(onboarding_dir)
        print(json.dumps(summary, indent=2))

    else:
        # Process single onboarding
        transcript_path = Path(sys.argv[1])
        account_id = sys.argv[2] if len(sys.argv) > 2 else None
        result = process_onboarding_file(transcript_path, account_id)
        print(json.dumps(result, indent=2))
