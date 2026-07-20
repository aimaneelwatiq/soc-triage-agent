import ipaddress
import time
from app.integrations import abuseipdb, virustotal
from app.models.alert import Alert

_cache = {}
CACHE_TTL = 300  # 5 minutes

def _is_private_ip(ip: str) -> bool:
    try:
        return ipaddress.ip_address(ip).is_private
    except ValueError:
        return False

def enrich_alert(alert: Alert) -> dict:
    result = {}
    source_ip = str(alert.source_ip) if alert.source_ip else None

    if not source_ip:
        result["note"] = "Aucune IP source, enrichissement ignoré."
        return result

    if _is_private_ip(source_ip):
        result["note"] = f"IP {source_ip} privée, pas d'enrichissement OSINT."
        return result

    # Cache
    now = time.time()
    if source_ip in _cache and (now - _cache[source_ip]["timestamp"]) < CACHE_TTL:
        return _cache[source_ip]["data"]

    abuse_data = abuseipdb.check_ip_abuse(source_ip)
    vt_data = virustotal.check_ip_vt(source_ip)
    result = {"abuseipdb": abuse_data, "virustotal": vt_data}

    _cache[source_ip] = {"data": result, "timestamp": now}
    return result