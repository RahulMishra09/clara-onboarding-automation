"""
Pipeline A: Demo Call → v1 Agent
Processes demo call transcripts to generate v1 account memos and agent specs.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from extract_memo import MemoExtractor
from generate_prompt import PromptGenerator
from storage import AccountStorage
from schemas import ProcessingMetadata
from logger import get_processing_logger, log_section
from config import DATA_DIR

logger = get_processing_logger()


class PipelineA:
    """Pipeline A: Demo → v1 Account Memo + Agent Spec"""

    def __init__(self):
        """Initialize pipeline components."""
        self.memo_extractor = MemoExtractor()
        self.prompt_generator = PromptGenerator()
        self.storage = AccountStorage()
        logger.info("Pipeline A initialized")

    def process_demo_transcript(
        self,
        transcript_path: Path,
        save_outputs: bool = True
    ) -> Dict[str, Any]:
        """
        Process a demo call transcript through Pipeline A.

        Args:
            transcript_path: Path to demo transcript file
            save_outputs: Whether to save outputs to storage

        Returns:
            Dictionary with processing results
        """
        log_section(logger, f"PIPELINE A: {transcript_path.name}")

        results = {
            "transcript_path": str(transcript_path),
            "status": "pending",
            "account_id": None,
            "v1_memo": None,
            "v1_agent_spec": None,
            "errors": [],
            "warnings": [],
            "started_at": datetime.utcnow().isoformat(),
            "completed_at": None
        }

        try:
            # Step 1: Read transcript
            logger.info(f"[1/5] Reading transcript: {transcript_path}")
            with open(transcript_path, 'r', encoding='utf-8') as f:
                transcript = f.read()

            if len(transcript.strip()) == 0:
                raise ValueError("Transcript file is empty")

            logger.info(f"✅ Transcript loaded ({len(transcript)} chars)")

            # Step 2: Extract v1 memo
            logger.info("[2/5] Extracting v1 account memo...")
            v1_memo = self.memo_extractor.extract_from_demo(transcript)
            results["v1_memo"] = v1_memo
            results["account_id"] = v1_memo["account_id"]

            logger.info(f"✅ v1 memo extracted for {v1_memo['account_id']}")
            logger.info(f"   Company: {v1_memo['company_name']}")
            logger.info(f"   Unknowns: {len(v1_memo.get('questions_or_unknowns', []))}")

            # Check for data quality warnings
            if len(v1_memo.get('questions_or_unknowns', [])) > 10:
                warning = f"High number of unknowns: {len(v1_memo['questions_or_unknowns'])}"
                results["warnings"].append(warning)
                logger.warning(f"⚠️  {warning}")

            # Step 3: Generate v1 agent spec
            logger.info("[3/5] Generating v1 agent spec...")
            from schemas import AccountMemo
            memo_obj = AccountMemo(**v1_memo)
            agent_spec_obj = self.prompt_generator.generate_agent_spec(memo_obj)
            v1_agent_spec = agent_spec_obj.model_dump()
            results["v1_agent_spec"] = v1_agent_spec

            logger.info(f"✅ v1 agent spec generated ({len(agent_spec_obj.system_prompt)} chars)")

            # Step 4: Save outputs
            if save_outputs:
                logger.info("[4/5] Saving outputs to storage...")

                # Save v1 memo
                memo_path = self.storage.save_v1_memo(v1_memo)
                results["v1_memo_path"] = str(memo_path)

                # Save v1 agent spec
                spec_path = self.storage.save_agent_spec(
                    v1_memo["account_id"],
                    "v1",
                    v1_agent_spec
                )
                results["v1_agent_spec_path"] = str(spec_path)

                # Save metadata
                metadata = {
                    "account_id": v1_memo["account_id"],
                    "company_name": v1_memo["company_name"],
                    "demo_transcript_path": str(transcript_path),
                    "onboarding_transcript_path": None,
                    "v1_created_at": datetime.utcnow().isoformat(),
                    "v2_created_at": None,
                    "processing_status": "v1_complete",
                    "error_message": None,
                    "last_processed": datetime.utcnow().isoformat()
                }
                metadata_path = self.storage.save_metadata(metadata)
                results["metadata_path"] = str(metadata_path)

                logger.info("✅ All outputs saved")
            else:
                logger.info("[4/5] Skipping save (save_outputs=False)")

            # Step 5: Finalize
            results["status"] = "success"
            results["completed_at"] = datetime.utcnow().isoformat()

            logger.info("[5/5] Pipeline A complete!")
            log_section(logger, "PIPELINE A: SUCCESS")

            return results

        except Exception as e:
            logger.error(f"❌ Pipeline A failed: {e}")
            results["status"] = "error"
            results["errors"].append(str(e))
            results["completed_at"] = datetime.utcnow().isoformat()

            # Save error metadata if we have an account_id
            if results["account_id"] and save_outputs:
                try:
                    metadata = {
                        "account_id": results["account_id"],
                        "company_name": results.get("v1_memo", {}).get("company_name", "Unknown"),
                        "demo_transcript_path": str(transcript_path),
                        "processing_status": "error",
                        "error_message": str(e),
                        "last_processed": datetime.utcnow().isoformat()
                    }
                    self.storage.save_metadata(metadata)
                except Exception as meta_error:
                    logger.error(f"Failed to save error metadata: {meta_error}")

            log_section(logger, "PIPELINE A: FAILED")
            return results


def process_demo_file(transcript_path: Path) -> Dict[str, Any]:
    """
    Convenience function to process a single demo transcript.

    Args:
        transcript_path: Path to demo transcript

    Returns:
        Processing results
    """
    pipeline = PipelineA()
    return pipeline.process_demo_transcript(transcript_path)


def process_all_demos(demo_dir: Optional[Path] = None) -> Dict[str, Any]:
    """
    Process all demo transcripts in a directory.

    Args:
        demo_dir: Directory containing demo transcripts (defaults to data/demo_calls)

    Returns:
        Summary of processing results
    """
    if demo_dir is None:
        demo_dir = DATA_DIR / "demo_calls"

    if not demo_dir.exists():
        raise ValueError(f"Demo directory not found: {demo_dir}")

    log_section(logger, f"PROCESSING ALL DEMOS: {demo_dir}")

    # Find all transcript files
    transcript_files = list(demo_dir.glob("*.txt"))
    transcript_files.extend(demo_dir.glob("*.md"))

    logger.info(f"Found {len(transcript_files)} transcript files")

    if len(transcript_files) == 0:
        logger.warning("⚠️  No transcript files found")
        return {"status": "no_files", "results": []}

    # Process each transcript
    pipeline = PipelineA()
    results = []

    for i, transcript_path in enumerate(transcript_files, 1):
        logger.info(f"\n{'='*80}")
        logger.info(f"Processing {i}/{len(transcript_files)}: {transcript_path.name}")
        logger.info(f"{'='*80}\n")

        try:
            result = pipeline.process_demo_transcript(transcript_path)
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
        print("  Process single demo:")
        print("    python pipeline_a.py <transcript_path>")
        print("  Process all demos:")
        print("    python pipeline_a.py --all [demo_dir]")
        sys.exit(1)

    if sys.argv[1] == "--all":
        # Process all demos
        demo_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else None
        summary = process_all_demos(demo_dir)
        print(json.dumps(summary, indent=2))

    else:
        # Process single demo
        transcript_path = Path(sys.argv[1])
        result = process_demo_file(transcript_path)
        print(json.dumps(result, indent=2))
