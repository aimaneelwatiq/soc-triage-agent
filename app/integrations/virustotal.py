import requests
from app.core.config import settings

def check_ip_vt(ip: str) -> dict:
    if not settings.VT_API_KEY:
        return {"error": "Clé API VirusTotal manquante"}
    if not ip:
        return {"error": "Aucune IP fournie"}
    
    url = f"https://www.virustotal.com/api/v3/ip_addresses/{ip}"
    headers = {"x-apikey": settings.VT_API_KEY}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 404:
            return {"malicious_count": 0, "reputation": 0, "error": None}
        response.raise_for_status()
        attrs = response.json().get("data", {}).get("attributes", {})
        stats = attrs.get("last_analysis_stats", {})
        return {
            "malicious_count": stats.get("malicious", 0) + stats.get("suspicious", 0),
            "reputation": attrs.get("reputation", 0),
            "country": attrs.get("country", "Unknown"),
            "error": None
        }
    except Exception as e:
        return {"error": f"Erreur VirusTotal : {str(e)}"}