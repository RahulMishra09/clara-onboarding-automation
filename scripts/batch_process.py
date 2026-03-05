"""
Batch processor for Clara AI Automation Pipeline.
Processes all demo and onboarding transcripts end-to-end.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import time

from pipeline_a import PipelineA
from pipeline_b import PipelineB
from storage import AccountStorage
from logger import get_processing_logger, log_section
from config import DATA_DIR, OUTPUT_DIR

logger = get_processing_logger()


class BatchProcessor:
    """Batch processor for all transcripts."""

    def __init__(self):
        """Initialize batch processor."""
        self.pipeline_a = PipelineA()
        self.pipeline_b = PipelineB()
        self.storage = AccountStorage()
        logger.info("Batch processor initialized")

    def process_all(
        self,
        demo_dir: Optional[Path] = None,
        onboarding_dir: Optional[Path] = None,
        account_mapping: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Process all demo and onboarding transcripts.

        Args:
            demo_dir: Directory with demo transcripts (defaults to data/demo_calls)
            onboarding_dir: Directory with onboarding transcripts (defaults to data/onboarding_calls)
            account_mapping: Optional mapping of onboarding filename → account_id

        Returns:
            Complete processing summary
        """
        log_section(logger, "BATCH PROCESSING: ALL TRANSCRIPTS")

        start_time = time.time()

        summary = {
            "started_at": datetime.utcnow().isoformat(),
            "completed_at": None,
            "duration_seconds": None,
            "demo_processing": None,
            "onboarding_processing": None,
            "final_storage_summary": None,
            "errors": []
        }

        try:
            # Set default directories
            if demo_dir is None:
                demo_dir = DATA_DIR / "demo_calls"
            if onboarding_dir is None:
                onboarding_dir = DATA_DIR / "onboarding_calls"

            # Phase 1: Process all demo calls
            log_section(logger, "PHASE 1: PROCESSING DEMO CALLS")
            logger.info(f"Demo directory: {demo_dir}")

            demo_files = self._find_transcripts(demo_dir)
            logger.info(f"Found {len(demo_files)} demo transcripts")

            demo_results = []
            for i, demo_file in enumerate(demo_files, 1):
                logger.info(f"\n[Demo {i}/{len(demo_files)}] Processing: {demo_file.name}")
                try:
                    result = self.pipeline_a.process_demo_transcript(demo_file)
                    demo_results.append(result)

                    if result["status"] == "success":
                        logger.info(f"✅ Success: {result['account_id']}")
                    else:
                        logger.error(f"❌ Failed: {result.get('errors', [])}")

                except Exception as e:
                    logger.error(f"❌ Exception processing {demo_file.name}: {e}")
                    demo_results.append({
                        "transcript_path": str(demo_file),
                        "status": "error",
                        "errors": [str(e)]
                    })

            summary["demo_processing"] = {
                "total": len(demo_files),
                "successful": len([r for r in demo_results if r["status"] == "success"]),
                "failed": len([r for r in demo_results if r["status"] == "error"]),
                "results": demo_results
            }

            logger.info(f"\nDemo processing complete:")
            logger.info(f"  ✅ Success: {summary['demo_processing']['successful']}/{len(demo_files)}")
            logger.info(f"  ❌ Failed: {summary['demo_processing']['failed']}/{len(demo_files)}")

            # Phase 2: Process all onboarding calls
            log_section(logger, "PHASE 2: PROCESSING ONBOARDING CALLS")
            logger.info(f"Onboarding directory: {onboarding_dir}")

            onboarding_files = self._find_transcripts(onboarding_dir)
            logger.info(f"Found {len(onboarding_files)} onboarding transcripts")

            # Build account mapping if not provided
            if account_mapping is None:
                account_mapping = self._auto_map_accounts(onboarding_files, demo_results)

            onboarding_results = []
            for i, onboarding_file in enumerate(onboarding_files, 1):
                logger.info(f"\n[Onboarding {i}/{len(onboarding_files)}] Processing: {onboarding_file.name}")

                # Get account_id from mapping
                account_id = account_mapping.get(onboarding_file.name)

                if not account_id:
                    logger.warning(f"⚠️  No account mapping for {onboarding_file.name}, attempting auto-match")

                try:
                    result = self.pipeline_b.process_onboarding_transcript(
                        onboarding_file,
                        account_id=account_id
                    )
                    onboarding_results.append(result)

                    if result["status"] == "success":
                        logger.info(f"✅ Success: {result['account_id']}")
                    else:
                        logger.error(f"❌ Failed: {result.get('errors', [])}")

                except Exception as e:
                    logger.error(f"❌ Exception processing {onboarding_file.name}: {e}")
                    onboarding_results.append({
                        "transcript_path": str(onboarding_file),
                        "status": "error",
                        "errors": [str(e)]
                    })

            summary["onboarding_processing"] = {
                "total": len(onboarding_files),
                "successful": len([r for r in onboarding_results if r["status"] == "success"]),
                "failed": len([r for r in onboarding_results if r["status"] == "error"]),
                "results": onboarding_results
            }

            logger.info(f"\nOnboarding processing complete:")
            logger.info(f"  ✅ Success: {summary['onboarding_processing']['successful']}/{len(onboarding_files)}")
            logger.info(f"  ❌ Failed: {summary['onboarding_processing']['failed']}/{len(onboarding_files)}")

            # Phase 3: Generate final summary
            log_section(logger, "PHASE 3: GENERATING SUMMARY")

            storage_summary = self.storage.get_storage_summary()
            summary["final_storage_summary"] = storage_summary

            logger.info(f"Total accounts: {storage_summary['total_accounts']}")
            logger.info(f"  v1 complete: {storage_summary['accounts_with_v1']}")
            logger.info(f"  v2 complete: {storage_summary['accounts_with_v2']}")
            logger.info(f"  Fully complete: {storage_summary['accounts_complete']}")

        except Exception as e:
            logger.error(f"❌ Batch processing failed: {e}")
            summary["errors"].append(str(e))

        # Finalize
        end_time = time.time()
        summary["completed_at"] = datetime.utcnow().isoformat()
        summary["duration_seconds"] = round(end_time - start_time, 2)

        log_section(logger, "BATCH PROCESSING COMPLETE")
        logger.info(f"Duration: {summary['duration_seconds']}s")

        return summary

    def _find_transcripts(self, directory: Path) -> List[Path]:
        """Find all transcript files in a directory."""
        if not directory.exists():
            logger.warning(f"⚠️  Directory not found: {directory}")
            return []

        files = list(directory.glob("*.txt"))
        files.extend(directory.glob("*.md"))

        # Filter out README and other non-transcript files
        files = [f for f in files if not f.name.lower().startswith(('readme', '.', 'example'))]

        return sorted(files)

    def _auto_map_accounts(
        self,
        onboarding_files: List[Path],
        demo_results: List[Dict[str, Any]]
    ) -> Dict[str, str]:
        """
        Automatically map onboarding files to account IDs based on naming.

        Args:
            onboarding_files: List of onboarding transcript paths
            demo_results: Results from demo processing

        Returns:
            Dictionary mapping filename → account_id
        """
        mapping = {}

        # Build map of account_id → company_name from demo results
        accounts = {}
        for result in demo_results:
            if result["status"] == "success" and result.get("v1_memo"):
                account_id = result["account_id"]
                company_name = result["v1_memo"]["company_name"]
                accounts[account_id] = company_name

        # Try to match onboarding files to accounts
        for onboarding_file in onboarding_files:
            filename = onboarding_file.stem  # filename without extension

            # Strategy 1: Direct account_id match in filename
            for account_id in accounts.keys():
                if account_id in filename.lower():
                    mapping[onboarding_file.name] = account_id
                    logger.info(f"  Mapped {onboarding_file.name} → {account_id}")
                    break

            # Strategy 2: Company name match in filename
            if onboarding_file.name not in mapping:
                for account_id, company_name in accounts.items():
                    # Extract key words from company name
                    key_words = company_name.lower().split()
                    if any(word in filename.lower() for word in key_words if len(word) > 3):
                        mapping[onboarding_file.name] = account_id
                        logger.info(f"  Mapped {onboarding_file.name} → {account_id} (via company name)")
                        break

        return mapping

    def generate_report(self, summary: Dict[str, Any], output_path: Optional[Path] = None) -> Path:
        """
        Generate a detailed processing report.

        Args:
            summary: Processing summary from process_all()
            output_path: Optional path for report (defaults to outputs/batch_report.json)

        Returns:
            Path to report file
        """
        if output_path is None:
            output_path = OUTPUT_DIR.parent / "batch_report.json"

        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Add human-readable summary
        report = {
            "summary": {
                "total_demo_files": summary.get("demo_processing", {}).get("total", 0),
                "demo_success_rate": self._calculate_success_rate(summary.get("demo_processing")),
                "total_onboarding_files": summary.get("onboarding_processing", {}).get("total", 0),
                "onboarding_success_rate": self._calculate_success_rate(summary.get("onboarding_processing")),
                "total_accounts": summary.get("final_storage_summary", {}).get("total_accounts", 0),
                "fully_complete_accounts": summary.get("final_storage_summary", {}).get("accounts_complete", 0),
                "duration_seconds": summary.get("duration_seconds"),
            },
            "details": summary
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)

        logger.info(f"✅ Report saved to: {output_path}")
        return output_path

    def _calculate_success_rate(self, processing_result: Optional[Dict[str, Any]]) -> str:
        """Calculate success rate percentage."""
        if not processing_result or processing_result.get("total", 0) == 0:
            return "N/A"

        total = processing_result["total"]
        successful = processing_result.get("successful", 0)

        rate = (successful / total) * 100
        return f"{rate:.1f}%"


def run_batch_processing(
    demo_dir: Optional[str] = None,
    onboarding_dir: Optional[str] = None,
    save_report: bool = True
) -> Dict[str, Any]:
    """
    Run complete batch processing.

    Args:
        demo_dir: Path to demo transcripts directory
        onboarding_dir: Path to onboarding transcripts directory
        save_report: Whether to save JSON report

    Returns:
        Processing summary
    """
    processor = BatchProcessor()

    # Convert string paths to Path objects
    demo_path = Path(demo_dir) if demo_dir else None
    onboarding_path = Path(onboarding_dir) if onboarding_dir else None

    # Process all files
    summary = processor.process_all(
        demo_dir=demo_path,
        onboarding_dir=onboarding_path
    )

    # Generate report
    if save_report:
        processor.generate_report(summary)

    return summary


if __name__ == "__main__":
    import sys

    demo_dir = sys.argv[1] if len(sys.argv) > 1 else None
    onboarding_dir = sys.argv[2] if len(sys.argv) > 2 else None

    logger.info("Starting batch processing...")
    logger.info(f"Demo directory: {demo_dir or 'default (data/demo_calls)'}")
    logger.info(f"Onboarding directory: {onboarding_dir or 'default (data/onboarding_calls)'}")

    summary = run_batch_processing(demo_dir, onboarding_dir)

    print("\n" + "="*80)
    print("BATCH PROCESSING SUMMARY")
    print("="*80)
    print(json.dumps(summary, indent=2))
