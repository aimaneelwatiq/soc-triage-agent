import logging
import requests
from typing import Dict, Any, Optional
from app.models.alert import Alert
from app.core.config import settings
from app.utils.json_parser import extract_json
from app.utils.retry import retry_on_exception

logger = logging.getLogger(__name__)

# ---- Règles heuristiques (fallback) ----
def heuristic_classify(alert: Alert, osint_data: Optional[dict] = None) -> Dict[str, Any]:
    event = alert.event_type.lower()
    if "kerberos" in event or "as-rep" in event:
        return {
            "severity": "High",
            "justification": "Attaque Kerberos détectée (AS-REP Roasting).",
            "confidence_score": 0.6,
            "suggested_action": "Vérifier les tickets Kerberos et révoquer si nécessaire."
        }
    if "bruteforce" in event or "failed login" in event:
        abuse_score = 0
        if osint_data and "abuseipdb" in osint_data:
            abuse_score = osint_data["abuseipdb"].get("score", 0)
        if abuse_score > 80:
            return {
                "severity": "Critical",
                "justification": f"Bruteforce avec score AbuseIPDB {abuse_score} > 80.",
                "confidence_score": 0.7,
                "suggested_action": "Bloquer l'IP source immédiatement."
            }
        return {
            "severity": "Medium",
            "justification": "Tentative de bruteforce, surveiller.",
            "confidence_score": 0.5,
            "suggested_action": "Analyser les logs d'authentification."
        }
    if "malware" in event:
        return {
            "severity": "High",
            "justification": "Alerte malware détectée.",
            "confidence_score": 0.7,
            "suggested_action": "Isoler la machine affectée."
        }
    return {
        "severity": "Informational",
        "justification": "Alerte non classée par les règles heuristiques.",
        "confidence_score": 0.3,
        "suggested_action": "Vérifier manuellement."
    }

@retry_on_exception((requests.RequestException, ValueError), max_retries=3)
def _call_ollama(payload: dict) -> dict:
    response = requests.post(
        f"{settings.OLLAMA_BASE_URL}/api/chat",
        json=payload,
        timeout=180
    )
    response.raise_for_status()
    return response.json()

def classify_alert(alert: Alert, osint_data: Optional[dict] = None) -> Dict[str, Any]:
    # Contexte OSINT (inchangé)
    osint_context = "Aucune donnée OSINT disponible."
    if osint_data:
        abuse = osint_data.get("abuseipdb", {})
        vt = osint_data.get("virustotal", {})
        if "error" not in abuse and abuse.get("score", 0) > 0:
            osint_context = f"""
🔍 Données OSINT :
- AbuseIPDB Score : {abuse.get('score', 0)}/100
- AbuseIPDB Pays : {abuse.get('country', 'Inconnu')}
- Nombre de rapports : {abuse.get('total_reports', 0)}
- VirusTotal Détections : {vt.get('malicious_count', 0)} moteurs.
"""

    # Prompt enrichi (MITRE)
    system_prompt = """Tu es un expert SOC. Attribue une sévérité selon les règles impératives :
- Si AbuseIPDB score > 80 ET bruteforce → CRITICAL.
- Si VirusTotal détections > 0 → HIGH ou CRITICAL.
- Kerberos (AS-REP, Kerberoasting) → au moins HIGH.
- Malware → au moins HIGH.
- Sinon, utilise ton jugement.

Réponds UNIQUEMENT en JSON : {"severity": "Critical|High|Medium|Low|Informational", "justification": "...", "confidence_score": 0.0-1.0, "suggested_action": "..."}.
"""

    user_prompt = f"""Alerte :
- Type : {alert.event_type}
- Règle : {alert.rule_description or 'Non spécifiée'}
- Cible : {alert.hostname or 'Inconnue'}
- Utilisateur : {alert.username or 'Inconnu'}
- IP Source : {alert.source_ip or 'Inconnue'}

{osint_context}

Log brut : {alert.raw_log[:300]}

Donne ta classification finale en JSON strict."""

    payload = {
        "model": settings.MODEL_NAME,
        "messages": [{"role": "system", "content": system_prompt},
                     {"role": "user", "content": user_prompt}],
        "stream": False,
        "temperature": settings.TEMPERATURE,
        "max_tokens": settings.MAX_TOKENS
    }

    try:
        llm_response = _call_ollama(payload)
        parsed = extract_json(llm_response["message"]["content"])
        required = ["severity", "justification", "confidence_score", "suggested_action"]
        if not all(k in parsed for k in required):
            raise ValueError("Clés manquantes")
        return parsed
    except Exception as e:
        logger.error(f"Erreur LLM : {e}. Passage au fallback heuristique.")
        return heuristic_classify(alert, osint_data)