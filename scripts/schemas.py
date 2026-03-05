"""
JSON Schema definitions for Clara AI Automation Pipeline.
Defines the structure for Account Memos, Agent Specs, and Changelogs.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum


class Version(str, Enum):
    """Version enum for tracking memo versions."""
    V1 = "v1"
    V2 = "v2"


class BusinessHours(BaseModel):
    """Business hours configuration."""
    days: Optional[List[str]] = Field(None, description="Days of operation")
    start: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$", description="Start time in HH:MM format")
    end: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$", description="End time in HH:MM format")
    timezone: Optional[str] = Field(None, description="Timezone (e.g., America/New_York)")


class EmergencyRoutingRules(BaseModel):
    """Emergency routing configuration."""
    primary_contact: Optional[str] = Field(None, description="Primary emergency contact")
    secondary_contact: Optional[str] = Field(None, description="Secondary emergency contact")
    order: Optional[List[str]] = Field(None, description="Order of contact attempts")
    fallback: Optional[str] = Field(None, description="Fallback procedure if all contacts fail")


class NonEmergencyRoutingRules(BaseModel):
    """Non-emergency routing configuration."""
    business_hours: Optional[str] = Field(None, description="Routing during business hours")
    after_hours: Optional[str] = Field(None, description="Routing after hours")


class CallTransferRules(BaseModel):
    """Call transfer configuration."""
    timeout_seconds: Optional[int] = Field(60, description="Transfer timeout in seconds")
    max_retries: Optional[int] = Field(2, description="Maximum retry attempts")
    fail_message: Optional[str] = Field(None, description="Message when transfer fails")


class AccountMemo(BaseModel):
    """Account memo JSON schema - the core business rules document."""
    account_id: str = Field(..., description="Unique account identifier")
    company_name: str = Field(..., description="Company name")
    business_hours: Optional[BusinessHours] = Field(None, description="Business hours configuration")
    office_address: Optional[str] = Field(None, description="Physical office address")
    services_supported: Optional[List[str]] = Field(None, description="List of services offered")
    emergency_definition: Optional[List[str]] = Field(None, description="What constitutes an emergency")
    emergency_routing_rules: Optional[EmergencyRoutingRules] = Field(None, description="Emergency routing config")
    non_emergency_routing_rules: Optional[NonEmergencyRoutingRules] = Field(None, description="Non-emergency routing")
    call_transfer_rules: Optional[CallTransferRules] = Field(None, description="Transfer configuration")
    integration_constraints: Optional[List[str]] = Field(default_factory=list, description="System integration rules")
    after_hours_flow_summary: Optional[str] = Field(None, description="Summary of after-hours call flow")
    office_hours_flow_summary: Optional[str] = Field(None, description="Summary of business hours call flow")
    questions_or_unknowns: List[str] = Field(default_factory=list, description="Missing or unclear information")
    notes: Optional[str] = Field(None, description="Additional notes")
    version: Version = Field(..., description="Version identifier (v1 or v2)")
    last_updated: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="Last update timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "account_id": "acme-fire-protection",
                "company_name": "Acme Fire Protection",
                "business_hours": {
                    "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
                    "start": "08:00",
                    "end": "17:00",
                    "timezone": "America/New_York"
                },
                "services_supported": ["fire protection", "sprinkler systems", "fire alarms"],
                "emergency_definition": ["sprinkler leak", "fire alarm triggered"],
                "version": "v1",
                "questions_or_unknowns": ["exact emergency contact phone number"]
            }
        }


class ToolPlaceholder(BaseModel):
    """Placeholder for Retell agent tools."""
    name: str = Field(..., description="Tool name")
    params: Optional[Dict[str, Any]] = Field(None, description="Tool parameters")


class AgentVariables(BaseModel):
    """Variables used in the agent system prompt."""
    timezone: Optional[str] = None
    business_hours: Optional[str] = None
    office_address: Optional[str] = None
    emergency_routing: Optional[Dict[str, Any]] = None


class RetellAgentSpec(BaseModel):
    """Retell agent configuration specification."""
    agent_name: str = Field(..., description="Agent display name")
    voice_style: str = Field(default="professional, warm, efficient", description="Voice characteristics")
    system_prompt: str = Field(..., description="Full system prompt for the agent")
    variables: AgentVariables = Field(default_factory=AgentVariables, description="Dynamic variables")
    tool_placeholders: Optional[Dict[str, Any]] = Field(None, description="Tool configurations")
    call_transfer_protocol: Optional[str] = Field(None, description="Transfer procedure steps")
    transfer_fail_protocol: Optional[str] = Field(None, description="Fallback when transfer fails")
    version: Version = Field(..., description="Version identifier")
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

    class Config:
        json_schema_extra = {
            "example": {
                "agent_name": "Clara - Acme Fire Protection",
                "voice_style": "professional, warm, efficient",
                "system_prompt": "You are Clara, the AI receptionist for Acme Fire Protection...",
                "version": "v1"
            }
        }


class ChangelogEntry(BaseModel):
    """Individual change entry in the changelog."""
    field: str = Field(..., description="Field path that changed (e.g., 'business_hours.start')")
    old_value: Optional[Any] = Field(None, description="Previous value")
    new_value: Optional[Any] = Field(None, description="New value")
    reason: str = Field(..., description="Reason for the change")


class Changelog(BaseModel):
    """Changelog document tracking v1 to v2 changes."""
    account_id: str = Field(..., description="Account identifier")
    from_version: Version = Field(..., description="Source version")
    to_version: Version = Field(..., description="Target version")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    changes: List[ChangelogEntry] = Field(..., description="List of changes")
    prompt_diff: Optional[str] = Field(None, description="Summary of prompt changes")

    class Config:
        json_schema_extra = {
            "example": {
                "account_id": "acme-fire-protection",
                "from_version": "v1",
                "to_version": "v2",
                "changes": [
                    {
                        "field": "business_hours.start",
                        "old_value": None,
                        "new_value": "08:00",
                        "reason": "Confirmed in onboarding call"
                    }
                ]
            }
        }


class ProcessingMetadata(BaseModel):
    """Metadata about the processing of an account."""
    account_id: str
    company_name: str
    demo_transcript_path: Optional[str] = None
    onboarding_transcript_path: Optional[str] = None
    v1_created_at: Optional[str] = None
    v2_created_at: Optional[str] = None
    processing_status: str = Field(default="pending")  # pending, v1_complete, v2_complete, error
    error_message: Optional[str] = None
    last_processed: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# Validation functions
def validate_account_memo(data: dict) -> AccountMemo:
    """Validate and parse account memo JSON."""
    return AccountMemo(**data)


def validate_agent_spec(data: dict) -> RetellAgentSpec:
    """Validate and parse agent spec JSON."""
    return RetellAgentSpec(**data)


def validate_changelog(data: dict) -> Changelog:
    """Validate and parse changelog JSON."""
    return Changelog(**data)


if __name__ == "__main__":
    # Test schema validation
    print("Testing schemas...")

    # Test Account Memo
    memo = AccountMemo(
        account_id="test-account",
        company_name="Test Company",
        version=Version.V1,
        questions_or_unknowns=["missing business hours"]
    )
    print(f"✅ AccountMemo validated: {memo.account_id}")

    # Test Agent Spec
    spec = RetellAgentSpec(
        agent_name="Clara - Test Company",
        system_prompt="Test prompt",
        version=Version.V1
    )
    print(f"✅ RetellAgentSpec validated: {spec.agent_name}")

    # Test Changelog
    changelog = Changelog(
        account_id="test-account",
        from_version=Version.V1,
        to_version=Version.V2,
        changes=[
            ChangelogEntry(
                field="business_hours.start",
                old_value=None,
                new_value="08:00",
                reason="Test change"
            )
        ]
    )
    print(f"✅ Changelog validated: {changelog.account_id}")

    print("\n✅ All schemas are valid!")
