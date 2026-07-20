import requests
import json
import time
import random
from datetime import datetime
from ipaddress import ip_address, ip_network

# Configuration
API_URL = "http://localhost:8000/triage"
HEALTH_URL = "http://localhost:8000/health"

# --- Générateurs d'IP aléatoires ---
def random_private_ip():
    """Retourne une IP privée aléatoire (192.168.x.x / 10.x.x.x)."""
    networks = ["192.168.", "10."]
    prefix = random.choice(networks)
    if prefix == "192.168.":
        return f"192.168.{random.randint(1,254)}.{random.randint(1,254)}"
    else:
        return f"10.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"

def random_public_ip():
    """Retourne une IP publique aléatoire (ne respecte pas les plages exactes)."""
    return f"{random.randint(1,223)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"

# --- Modèles d'alertes (plus diversifiés) ---
ALERT_TEMPLATES = [
    {
        "event_type": "SSH Bruteforce",
        "rule_id": "5712",
        "rule_description": "Multiple failed SSH logins from same source",
        "source_ip": None,  # sera généré
        "destination_ip": None,
        "username": "root",
        "hostname": "WEB_SERVER",
        "raw_log": "Failed password for {username} from {source_ip} port 22 ssh2"
    },
    {
        "event_type": "RDP Bruteforce",
        "rule_id": "5713",
        "rule_description": "Multiple failed RDP logins",
        "source_ip": None,
        "destination_ip": None,
        "username": "Administrator",
        "hostname": "DC01",
        "raw_log": "Event ID 4625: An account failed to log on. Source IP: {source_ip}, Account: {username}"
    },
    {
        "event_type": "Malware Detection",
        "rule_id": "8711",
        "rule_description": "Malware detected on endpoint",
        "source_ip": None,
        "destination_ip": None,
        "username": "jdoe",
        "hostname": "WORKSTATION-02",
        "raw_log": "C:\\Users\\{username}\\Downloads\\malware_{random}.exe has been detected as Trojan.Generic.2024 by Windows Defender."
    },
    {
        "event_type": "Kerberos AS-REP Roasting",
        "rule_id": "5710",
        "rule_description": "AS-REP Roasting attack detected",
        "source_ip": None,
        "destination_ip": None,
        "username": "svc_account",
        "hostname": "DC01",
        "raw_log": "Event ID 4768: Kerberos TGT request for account {username} without pre-authentication from IP {source_ip}."
    },
    {
        "event_type": "Outbound C2 Connection",
        "rule_id": "10002",
        "rule_description": "Connection to threat intelligence blacklist",
        "source_ip": None,
        "destination_ip": None,
        "username": "apache",
        "hostname": "APP_SERVER",
        "raw_log": "Firewall allowed outbound TCP from {source_ip}:{src_port} to {destination_ip}:4443 (Known C2 infrastructure)."
    },
    {
        "event_type": "Phishing Email Detected",
        "rule_id": "9999",
        "rule_description": "Email containing malicious URL detected",
        "source_ip": None,
        "destination_ip": None,
        "username": "user@company.com",
        "hostname": "MAIL_GATEWAY",
        "raw_log": "Email with subject 'Invoice' from {source_ip} contained URL to known phishing domain."
    },
    {
        "event_type": "Exfiltration Attempt",
        "rule_id": "10010",
        "rule_description": "Large data transfer to external IP",
        "source_ip": None,
        "destination_ip": None,
        "username": "db_user",
        "hostname": "DB_SERVER",
        "raw_log": "Outbound data transfer of 5.2 GB from {source_ip} to {destination_ip} on port 443."
    },
    {
        "event_type": "DNS Tunneling",
        "rule_id": "10015",
        "rule_description": "Suspicious DNS queries detected",
        "source_ip": None,
        "destination_ip": None,
        "username": None,
        "hostname": "DNS_SERVER",
        "raw_log": "DNS query for subdomain {random_subdomain}.malware-domain.com from {source_ip}."
    }
]

def generate_alert(template, index):
    """Génère une alerte en remplaçant les placeholders."""
    alert = template.copy()
    
    # Générer les IP
    source_ip = random_public_ip() if random.random() < 0.7 else random_private_ip()
    dest_ip = random_private_ip()
    alert["source_ip"] = source_ip
    alert["destination_ip"] = dest_ip
    
    # Remplacer les placeholders dans raw_log
    replacements = {
        "{source_ip}": source_ip,
        "{destination_ip}": dest_ip,
        "{username}": alert.get("username", "unknown"),
        "{random}": str(random.randint(1000, 9999)),
        "{src_port}": str(random.randint(1024, 65535)),
        "{random_subdomain}": ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=8))
    }
    for placeholder, value in replacements.items():
        if placeholder in alert["raw_log"]:
            alert["raw_log"] = alert["raw_log"].replace(placeholder, value)
    
    # Timestamp ISO
    alert["timestamp"] = datetime.now().isoformat() + "Z"
    # Ajout d'un identifiant de simulation
    alert["_sim_id"] = index
    return alert

def send_alert(alert):
    """Envoie une alerte à l'API avec affichage."""
    try:
        response = requests.post(API_URL, json=alert, timeout=120)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Alerte #{alert['_sim_id']} | {alert['event_type']}")
            print(f"   → Sévérité: {result.get('severity')} | Confiance: {result.get('confidence_score')}")
            print(f"   → Action suggérée: {result.get('suggested_action', 'N/A')[:60]}...")
        else:
            print(f"⚠️ Erreur {response.status_code} pour l'alerte #{alert['_sim_id']}")
            print(f"   Réponse: {response.text[:100]}")
    except Exception as e:
        print(f"❌ Échec de l'envoi: {e}")

def main():
    print("=" * 70)
    print("🔄 SIMULATEUR DE FLUX D'ALERTES SOC (WAZUH → AGENT)")
    print("=" * 70)
    print(f"📡 Envoi vers {API_URL}")
    print("Appuyez sur Ctrl+C pour arrêter.\n")
    
    # Vérifier la disponibilité de l'API
    try:
        health = requests.get(HEALTH_URL, timeout=3)
        if health.status_code == 200:
            print("✅ API disponible.")
        else:
            print("⚠️ L'API répond mais le statut est inattendu. Continuons quand même.")
    except:
        print("❌ Impossible de contacter l'API. Vérifiez qu'elle tourne (uvicorn).")
        return

    # Paramètres de simulation
    try:
        nb_alerts = input("Nombre d'alertes à envoyer (0 pour infini) : ")
        nb_alerts = int(nb_alerts)
    except:
        nb_alerts = 0
    
    if nb_alerts == 0:
        print("🔄 Mode infini (Ctrl+C pour arrêter).")
    else:
        print(f"🔄 Envoi de {nb_alerts} alertes.")

    index = 1
    try:
        while True:
            if nb_alerts > 0 and index > nb_alerts:
                break
            template = random.choice(ALERT_TEMPLATES)
            alert = generate_alert(template, index)
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Alerte #{index}: {alert['event_type']}")
            send_alert(alert)
            index += 1
            if nb_alerts == 0:
                delay = random.randint(3, 10)
                print(f"⏳ Prochaine alerte dans {delay} secondes...")
                time.sleep(delay)
            else:
                if index <= nb_alerts:
                    delay = random.randint(2, 5)
                    print(f"⏳ Prochaine alerte dans {delay} secondes...")
                    time.sleep(delay)
    except KeyboardInterrupt:
        print("\n⏹️ Simulation arrêtée par l'utilisateur.")
    print(f"📊 Total d'alertes envoyées : {index - 1}")

if __name__ == "__main__":
    main()