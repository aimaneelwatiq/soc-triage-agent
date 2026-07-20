from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, HttpUrl, IPvAnyAddress


class Alert(BaseModel):
    """Standardized alert schema coming from the SIEM (Wazuh/ELK)."""
    
    # Core identification
    event_type: str = Field(..., description="Type of event (e.g., 'SSH_Failed_Login', 'AS_REP_Roasting', 'Malware_Detected')")
    timestamp: datetime = Field(..., description="Timestamp of the event occurrence")
    
    # Network & Identity context
    source_ip: Optional[IPvAnyAddress] = Field(None, description="Source IP address of the attacker/source")
    destination_ip: Optional[IPvAnyAddress] = Field(None, description="Destination IP address of the target")
    username: Optional[str] = Field(None, description="Targeted or affected username")
    hostname: Optional[str] = Field(None, description="Machine hostname involved")
    
    # Raw payload
    raw_log: str = Field(..., description="Full raw log line or JSON payload from Wazuh")
    rule_id: Optional[str] = Field(None, description="Wazuh rule ID that triggered the alert")
    rule_description: Optional[str] = Field(None, description="Wazuh rule name/description")
    
    # Extensible metadata (for future fields)
    extra: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata (e.g., user agent, hash, etc.)")
    
    class Config:
        # Allows you to pass an example for the OpenAPI (FastAPI) docs
        json_schema_extra = {
            "example": {
                "event_type": "AS-REP Roasting",
                "timestamp": "2026-07-07T10:15:30Z",
                "source_ip": "192.168.1.100",
                "destination_ip": "10.0.0.5",
                "username": "svc_account",
                "hostname": "DC01",
                "raw_log": "{\"rule\":\"5710\",\"description\":\"AS-REP Roasting attack detected\"}",
                "rule_id": "5710",
                "rule_description": "Kerberos AS-REP Roasting"
            }
        }