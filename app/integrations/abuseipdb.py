import requests
from app.core.config import settings

def check_ip_abuse(ip: str) -> dict:
    if not settings.ABUSEIPDB_API_KEY:
        return {"error": "Clé API AbuseIPDB manquante"}
    if not ip:
        return {"error": "Aucune IP fournie"}
    
    url = "https://api.abuseipdb.com/api/v2/check"
    headers = {"Key": settings.ABUSEIPDB_API_KEY, "Accept": "application/json"}
    params = {"ipAddress": ip, "maxAgeInDays": 30}
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json().get("data", {})
        return {
            "score": data.get("abuseConfidenceScore", 0),
            "country": data.get("countryCode", "Unknown"),
            "total_reports": data.get("totalReports", 0),
            "last_reported_at": data.get("lastReportedAt", "Never")
        }
    except Exception as e:
        return {"error": f"Erreur AbuseIPDB : {str(e)}"}