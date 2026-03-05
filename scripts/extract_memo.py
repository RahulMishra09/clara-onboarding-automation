"""
Extract Account Memo JSON from demo or onboarding call transcripts using LLM.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from llm_client import LLMClient
from schemas import AccountMemo, validate_account_memo, Version
from validators import validate_memo_data_quality, check_no_hallucination
from logger import get_extraction_logger
from config import PROMPTS_DIR

logger = get_extraction_logger()


class MemoExtractor:
    """Extract structured memos from call transcripts."""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        """
        Initialize memo extractor.

        Args:
            llm_client: Optional LLM client (creates new one if not provided)
        """
        self.llm = llm_client or LLMClient()
        self.demo_prompt_template = self._load_prompt("extract_demo.txt")
        self.onboarding_prompt_template = self._load_prompt("extract_onboarding.txt")

    def _load_prompt(self, filename: str) -> str:
        """Load prompt template from file."""
        prompt_path = PROMPTS_DIR / filename
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                content = f.read()
            logger.info(f"✅ Loaded prompt: {filename}")
            return content
        except FileNotFoundError:
            logger.error(f"❌ Prompt file not found: {prompt_path}")
            raise

    def extract_from_demo(self, transcript: str) -> Dict[str, Any]:
        """
        Extract v1 Account Memo from demo call transcript.

        Args:
            transcript: Demo call transcript text

        Returns:
            Account Memo JSON (v1)
        """
        logger.info("Extracting memo from demo call transcript...")

        # Build prompt
        prompt = self.demo_prompt_template.replace("{{TRANSCRIPT}}", transcript)

        # Get LLM response
        logger.info("Calling LLM for extraction...")
        response = self.llm.complete(prompt, max_tokens=4000, temperature=0.0)

        # Parse JSON
        logger.info("Parsing JSON response...")
        memo_data = self.llm.extract_json(response)

        # Ensure version is v1
        memo_data["version"] = "v1"
        memo_data["last_updated"] = datetime.utcnow().isoformat()

        # Validate schema
        logger.info("Validating schema...")
        memo = validate_account_memo(memo_data)

        # Check data quality
        warnings = validate_memo_data_quality(memo)
        if warnings:
            logger.warning(f"⚠️  Data quality warnings ({len(warnings)}):")
            for warning in warnings:
                logger.warning(f"  - {warning}")

        # Check for hallucination
        if not check_no_hallucination(memo):
            logger.warning("⚠️  Possible hallucination detected - review unknowns")

        logger.info(f"✅ Successfully extracted v1 memo for {memo.account_id}")
        logger.info(f"   Company: {memo.company_name}")
        logger.info(f"   Unknowns: {len(memo.questions_or_unknowns)}")

        return memo.model_dump()

    def extract_onboarding_updates(
        self,
        transcript: str,
        v1_memo: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract updates from onboarding call transcript.

        Args:
            transcript: Onboarding call transcript text
            v1_memo: Existing v1 Account Memo

        Returns:
            Onboarding updates JSON
        """
        logger.info("Extracting updates from onboarding call transcript...")

        # Build prompt with v1 context
        v1_memo_json = json.dumps(v1_memo, indent=2)
        prompt = self.onboarding_prompt_template.replace("{{V1_MEMO}}", v1_memo_json)
        prompt = prompt.replace("{{TRANSCRIPT}}", transcript)

        # Get LLM response
        logger.info("Calling LLM for update extraction...")
        response = self.llm.complete(prompt, max_tokens=4000, temperature=0.0)

        # Parse JSON
        logger.info("Parsing JSON response...")
        updates_data = self.llm.extract_json(response)

        # Validate that account_id matches
        if updates_data.get("account_id") != v1_memo.get("account_id"):
            logger.error(
                f"❌ Account ID mismatch: "
                f"v1={v1_memo.get('account_id')}, "
                f"update={updates_data.get('account_id')}"
            )
            raise ValueError("Account ID mismatch between v1 and onboarding updates")

        logger.info(f"✅ Successfully extracted onboarding updates")
        logger.info(f"   Resolved unknowns: {len(updates_data.get('resolved_unknowns', []))}")
        logger.info(f"   New information: {len(updates_data.get('new_information', []))}")
        logger.info(f"   Remaining unknowns: {len(updates_data.get('remaining_unknowns', []))}")

        return updates_data


def extract_demo_memo(transcript_path: Path, output_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Extract v1 memo from demo transcript file.

    Args:
        transcript_path: Path to demo transcript file
        output_path: Optional path to save memo JSON

    Returns:
        Account Memo JSON
    """
    logger.info(f"Processing demo transcript: {transcript_path}")

    # Read transcript
    with open(transcript_path, 'r', encoding='utf-8') as f:
        transcript = f.read()

    # Extract memo
    extractor = MemoExtractor()
    memo = extractor.extract_from_demo(transcript)

    # Save if output path provided
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(memo, f, indent=2)
        logger.info(f"✅ Saved memo to: {output_path}")

    return memo


def extract_onboarding_updates(
    transcript_path: Path,
    v1_memo_path: Path,
    output_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Extract onboarding updates from transcript file.

    Args:
        transcript_path: Path to onboarding transcript file
        v1_memo_path: Path to existing v1 memo JSON
        output_path: Optional path to save updates JSON

    Returns:
        Onboarding updates JSON
    """
    logger.info(f"Processing onboarding transcript: {transcript_path}")

    # Read transcript
    with open(transcript_path, 'r', encoding='utf-8') as f:
        transcript = f.read()

    # Read v1 memo
    with open(v1_memo_path, 'r', encoding='utf-8') as f:
        v1_memo = json.load(f)

    # Extract updates
    extractor = MemoExtractor()
    updates = extractor.extract_onboarding_updates(transcript, v1_memo)

    # Save if output path provided
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(updates, f, indent=2)
        logger.info(f"✅ Saved updates to: {output_path}")

    return updates


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage:")
        print("  Demo extraction:")
        print("    python extract_memo.py demo <transcript_path> [output_path]")
        print("  Onboarding extraction:")
        print("    python extract_memo.py onboarding <transcript_path> <v1_memo_path> [output_path]")
        sys.exit(1)

    mode = sys.argv[1]

    if mode == "demo":
        transcript_path = Path(sys.argv[2])
        output_path = Path(sys.argv[3]) if len(sys.argv) > 3 else None
        memo = extract_demo_memo(transcript_path, output_path)
        print(json.dumps(memo, indent=2))

    elif mode == "onboarding":
        transcript_path = Path(sys.argv[2])
        v1_memo_path = Path(sys.argv[3])
        output_path = Path(sys.argv[4]) if len(sys.argv) > 4 else None
        updates = extract_onboarding_updates(transcript_path, v1_memo_path, output_path)
        print(json.dumps(updates, indent=2))

    else:
        print(f"Unknown mode: {mode}")
        sys.exit(1)
