from typing import TypedDict, Optional
from app.models.alert import Alert
from app.models.triage import TriageResult

class AgentState(TypedDict):
    alert: Alert
    osint_data: Optional[dict]
    triage_result: Optional[TriageResult]
    