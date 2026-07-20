from app.models.triage import TriageResult, SeverityLevel
from app.services.classification import classify_alert
from app.services.enrichment import enrich_alert
from app.agent.state import AgentState
import logging

logger = logging.getLogger(__name__)

def normalize_confidence(value) -> float:
    # (même fonction que précédemment, gardez-la)
    if isinstance(value, (int, float)):
        return max(0.0, min(1.0, float(value)))
    if isinstance(value, str):
        cleaned = value.strip().lower().replace('%', '')
        if '/' in cleaned:
            parts = cleaned.split('/')
            try:
                return max(0.0, min(1.0, float(parts[0]) / float(parts[1])))
            except:
                pass
        try:
            val = float(cleaned)
            if val > 1:
                return max(0.0, min(1.0, val / 100.0))
            return max(0.0, min(1.0, val))
        except ValueError:
            pass
    return 0.5

def enrich_node(state: AgentState) -> dict:
    logger.info("Nœud enrich : récupération OSINT...")
    osint_data = enrich_alert(state["alert"])
    return {"osint_data": osint_data}

def classify_node(state: AgentState) -> dict:
    logger.info("Nœud classify : appel LLM (ou fallback)...")
    alert = state["alert"]
    osint_data = state.get("osint_data")
    raw = classify_alert(alert, osint_data)

    # Normalisation
    raw_severity = raw["severity"].strip().lower().capitalize()
    try:
        severity_enum = SeverityLevel(raw_severity)
    except ValueError:
        severity_enum = SeverityLevel.MEDIUM

    confidence = normalize_confidence(raw["confidence_score"])

    result = TriageResult(
        severity=severity_enum,
        justification=raw["justification"],
        suggested_action=raw["suggested_action"],
        confidence_score=confidence,
        osint_context=osint_data
    )
    return {"triage_result": result}

# Optionnel : nœud d'évaluation sans ML (juste un log)
def assess_node(state: AgentState) -> dict:
    result = state.get("triage_result")
    if result:
        logger.info(f"Évaluation : sévérité={result.severity.value}, confiance={result.confidence_score:.2f}")
    return {} 