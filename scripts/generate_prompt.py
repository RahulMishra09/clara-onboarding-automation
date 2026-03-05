"""
Generate Retell AI agent system prompts from Account Memo JSON.
Follows required business hours and after-hours flow patterns.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from schemas import AccountMemo, RetellAgentSpec, AgentVariables, Version, validate_agent_spec
from validators import validate_agent_spec_safety
from logger import get_extraction_logger

logger = get_extraction_logger()


class PromptGenerator:
    """Generate Retell agent specs from account memos."""

    def generate_agent_spec(self, memo: AccountMemo) -> RetellAgentSpec:
        """
        Generate Retell agent spec from account memo.

        Args:
            memo: AccountMemo object

        Returns:
            RetellAgentSpec object
        """
        logger.info(f"Generating agent spec for {memo.company_name}...")

        # Generate system prompt
        system_prompt = self._build_system_prompt(memo)

        # Extract variables
        variables = self._extract_variables(memo)

        # Build transfer protocols
        transfer_protocol = self._build_transfer_protocol(memo)
        transfer_fail_protocol = self._build_transfer_fail_protocol(memo)

        # Build tool placeholders
        tool_placeholders = self._build_tool_placeholders(memo)

        # Create spec
        spec = RetellAgentSpec(
            agent_name=f"Clara - {memo.company_name}",
            voice_style="professional, warm, efficient",
            system_prompt=system_prompt,
            variables=variables,
            tool_placeholders=tool_placeholders,
            call_transfer_protocol=transfer_protocol,
            transfer_fail_protocol=transfer_fail_protocol,
            version=memo.version,
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat()
        )

        # Validate safety
        violations = validate_agent_spec_safety(spec)
        if violations:
            logger.warning(f"⚠️  Safety violations detected ({len(violations)}):")
            for violation in violations:
                logger.warning(f"  - {violation}")

        logger.info(f"✅ Generated agent spec ({len(system_prompt)} chars)")
        return spec

    def _build_system_prompt(self, memo: AccountMemo) -> str:
        """Build the main system prompt for the agent."""

        # Format business hours
        business_hours_str = self._format_business_hours(memo)

        # Build emergency definitions
        emergency_def = ", ".join(memo.emergency_definition) if memo.emergency_definition else "system failures"

        # Build services list
        services = ", ".join(memo.services_supported) if memo.services_supported else "various services"

        prompt = f"""# Your Role
You are Clara, the AI receptionist for {memo.company_name}. You answer calls professionally, gather necessary information, and help route callers to the right person or service.

# Company Information
- Company: {memo.company_name}
- Services: {services}
"""

        # Add business hours if available
        if business_hours_str:
            prompt += f"- Business Hours: {business_hours_str}\n"

        # Add address if available
        if memo.office_address:
            prompt += f"- Office Address: {memo.office_address}\n"

        # Add emergency definition
        prompt += f"\n# Emergency Definition\nEmergencies include: {emergency_def}\n"

        # Add business hours flow
        prompt += "\n" + self._build_business_hours_flow(memo)

        # Add after hours flow
        prompt += "\n" + self._build_after_hours_flow(memo)

        # Add integration constraints
        if memo.integration_constraints:
            prompt += "\n# Important Constraints\n"
            for constraint in memo.integration_constraints:
                prompt += f"- {constraint}\n"

        # Add critical rules
        prompt += """
# Critical Rules
- NEVER mention "tools", "functions", "API calls", or technical implementation details to callers
- Keep questions minimal: only ask for name, callback number, and (for emergencies) address
- Always be professional, warm, and efficient
- If you don't know something, offer to take a message and have someone call back
- Never make up information - only use what you know about the company
"""

        return prompt.strip()

    def _build_business_hours_flow(self, memo: AccountMemo) -> str:
        """Build the business hours call flow section."""

        flow = """# Business Hours Call Flow

When the office is OPEN, follow this flow:

1. **Greeting**
   "Thank you for calling {company_name}, this is Clara. How can I help you today?"

2. **Determine Need**
   Listen to the caller's request. Identify if it's:
   - An emergency requiring immediate attention
   - A service request or appointment
   - A billing or administrative question
   - A general inquiry

3. **Collect Information**
   "Can I have your name and a callback number in case we get disconnected?"

4. **Route or Transfer**
   Based on the caller's need, attempt to transfer to the appropriate person or department.
   {routing_rules}

5. **If Transfer Fails**
   {fail_protocol}

6. **Confirm and Close**
   "Is there anything else I can help you with today?"
   "Thank you for calling {company_name}, have a great day!"
"""

        # Add routing rules if available
        routing_rules = ""
        if memo.non_emergency_routing_rules and memo.non_emergency_routing_rules.business_hours:
            routing_rules = f"Routing: {memo.non_emergency_routing_rules.business_hours}"
        else:
            routing_rules = "Attempt to transfer to the main office line."

        # Add fail protocol
        fail_msg = memo.call_transfer_rules.fail_message if memo.call_transfer_rules else None
        fail_protocol = fail_msg or "I'm having trouble connecting you right now. Let me take down your information and I'll have someone call you back within the hour."

        return flow.format(
            company_name=memo.company_name,
            routing_rules=routing_rules,
            fail_protocol=fail_protocol
        )

    def _build_after_hours_flow(self, memo: AccountMemo) -> str:
        """Build the after-hours call flow section."""

        flow = """# After Hours Call Flow

When the office is CLOSED, follow this flow:

1. **Greeting**
   "Thank you for calling {company_name}, this is Clara. Our office is currently closed. How can I help you?"

2. **Check if Emergency**
   "Is this an emergency?"

3. **If YES - Emergency:**
   a. Collect critical information:
      "I need your name, callback number, and the address where the emergency is located."

   b. Get brief description:
      "Can you briefly describe the emergency?"
      {emergency_examples}

   c. Attempt emergency transfer:
      {emergency_routing}

   d. If transfer fails:
      "I've recorded your emergency information. Our on-call technician will contact you within 15 minutes."

4. **If NO - Non-Emergency:**
   "I'll take your information and someone will call you back during business hours{business_hours}."

   Collect:
   - Name
   - Callback number
   - Brief description of their need

5. **Confirm and Close**
   "Is there anything else I can help you with?"
   "Thank you for calling, stay safe."
"""

        # Add emergency examples
        emergency_examples = ""
        if memo.emergency_definition:
            examples = ", ".join(memo.emergency_definition[:3])
            emergency_examples = f"Examples: {examples}"

        # Add emergency routing
        emergency_routing = ""
        if memo.emergency_routing_rules and memo.emergency_routing_rules.primary_contact:
            primary = memo.emergency_routing_rules.primary_contact
            emergency_routing = f"Try to reach: {primary}"
            if memo.emergency_routing_rules.secondary_contact:
                emergency_routing += f", then {memo.emergency_routing_rules.secondary_contact}"
        else:
            emergency_routing = "Attempt to reach the on-call technician."

        # Format business hours
        business_hours_str = self._format_business_hours(memo)
        if business_hours_str:
            business_hours_str = f" ({business_hours_str})"
        else:
            business_hours_str = ""

        return flow.format(
            company_name=memo.company_name,
            emergency_examples=emergency_examples,
            emergency_routing=emergency_routing,
            business_hours=business_hours_str
        )

    def _format_business_hours(self, memo: AccountMemo) -> Optional[str]:
        """Format business hours for display."""
        if not memo.business_hours:
            return None

        bh = memo.business_hours

        # Build day range
        if bh.days:
            if len(bh.days) == 5 and set(bh.days) == {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday"}:
                day_str = "Monday-Friday"
            elif len(bh.days) == 7:
                day_str = "Daily"
            else:
                day_str = ", ".join(bh.days)
        else:
            day_str = None

        # Build time range
        if bh.start and bh.end:
            time_str = f"{self._format_time(bh.start)} - {self._format_time(bh.end)}"
        else:
            time_str = None

        # Build full string
        parts = []
        if day_str:
            parts.append(day_str)
        if time_str:
            parts.append(time_str)
        if bh.timezone:
            parts.append(bh.timezone.split("/")[-1].replace("_", " "))

        return " ".join(parts) if parts else None

    def _format_time(self, time_str: str) -> str:
        """Format time from HH:MM to 12-hour format."""
        try:
            hour, minute = map(int, time_str.split(":"))
            if hour == 0:
                return f"12:{minute:02d} AM"
            elif hour < 12:
                return f"{hour}:{minute:02d} AM"
            elif hour == 12:
                return f"12:{minute:02d} PM"
            else:
                return f"{hour-12}:{minute:02d} PM"
        except:
            return time_str

    def _extract_variables(self, memo: AccountMemo) -> AgentVariables:
        """Extract dynamic variables for the agent."""
        return AgentVariables(
            timezone=memo.business_hours.timezone if memo.business_hours else None,
            business_hours=self._format_business_hours(memo),
            office_address=memo.office_address,
            emergency_routing=memo.emergency_routing_rules.model_dump() if memo.emergency_routing_rules else None
        )

    def _build_transfer_protocol(self, memo: AccountMemo) -> str:
        """Build call transfer protocol steps."""
        timeout = memo.call_transfer_rules.timeout_seconds if memo.call_transfer_rules else 60
        retries = memo.call_transfer_rules.max_retries if memo.call_transfer_rules else 2

        return f"""1. Announce transfer: "Let me connect you with someone who can help."
2. Attempt transfer with {timeout} second timeout
3. If no answer, retry up to {retries} times
4. If all attempts fail, use transfer fail protocol"""

    def _build_transfer_fail_protocol(self, memo: AccountMemo) -> str:
        """Build transfer failure fallback protocol."""
        fail_msg = memo.call_transfer_rules.fail_message if memo.call_transfer_rules else None

        if fail_msg:
            return fail_msg

        return """1. Apologize: "I'm having trouble connecting you right now."
2. Offer alternative: "Let me take down your information and have someone call you back."
3. Collect: name, callback number, brief description
4. Confirm: "Someone will call you back within [timeframe based on urgency]."
5. Thank caller for their patience"""

    def _build_tool_placeholders(self, memo: AccountMemo) -> Dict[str, Any]:
        """Build tool configuration placeholders."""
        return {
            "transfer_call": {
                "description": "Transfer caller to specified number",
                "parameters": {
                    "phone_number": "string",
                    "timeout_seconds": memo.call_transfer_rules.timeout_seconds if memo.call_transfer_rules else 60
                }
            },
            "create_ticket": {
                "description": "Create a service ticket or callback request",
                "parameters": {
                    "caller_name": "string",
                    "callback_number": "string",
                    "description": "string",
                    "priority": "normal|high|emergency"
                }
            },
            "send_notification": {
                "description": "Send notification to on-call team",
                "parameters": {
                    "message": "string",
                    "priority": "normal|high|emergency"
                }
            }
        }


def generate_agent_spec_from_memo(
    memo_path: Path,
    output_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Generate agent spec from memo JSON file.

    Args:
        memo_path: Path to account memo JSON
        output_path: Optional path to save agent spec

    Returns:
        Agent spec JSON
    """
    logger.info(f"Generating agent spec from: {memo_path}")

    # Load memo
    with open(memo_path, 'r', encoding='utf-8') as f:
        memo_data = json.load(f)

    memo = AccountMemo(**memo_data)

    # Generate spec
    generator = PromptGenerator()
    spec = generator.generate_agent_spec(memo)

    # Convert to dict
    spec_dict = spec.model_dump()

    # Save if output path provided
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(spec_dict, f, indent=2)
        logger.info(f"✅ Saved agent spec to: {output_path}")

    return spec_dict


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python generate_prompt.py <memo_json_path> [output_path]")
        sys.exit(1)

    memo_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else None

    spec = generate_agent_spec_from_memo(memo_path, output_path)
    print(json.dumps(spec, indent=2))
