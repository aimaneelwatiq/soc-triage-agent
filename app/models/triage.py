from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field


class SeverityLevel(str, Enum):
    """Standardized severity levels for SOC triage."""
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    INFORMATIONAL = "Informational"


class TriageResult(BaseModel):
    """The final output of the SOC Triage Agent."""
    severity: SeverityLevel = Field(..., description="Assigned severity level")
    justification: str = Field(..., description="Detailed reasoning for the severity, referencing specific threat indicators")
    suggested_action: str = Field(..., description="Concrete, actionable recommendation for the analyst (e.g., 'Isolate host X', 'Revoke token Y')")
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Confidence of the AI in its classification (0.0 to 1.0)")
    osint_context: Optional[dict] = Field(default=None, description="Aggregated OSINT data (e.g., VT malicious hits, AbuseIPDB score)")
    suggested_actions: Optional[List[str]] = Field(default=None, description="List of additional suggested actions for the analyst to consider")


class TriageResponse(TriageResult):
    """TriageResult enrichi avec l'ID en base, retourné par l'API."""
    id: int = Field(..., description="ID unique de l'alerte en base de données")