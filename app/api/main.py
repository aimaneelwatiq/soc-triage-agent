from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.models.alert import Alert
from app.models.triage import TriageResult, TriageResponse
from app.agent.graph import build_triage_graph
from app.services.storage import init_db, save_triage, save_feedback, get_recent_alerts, DB_PATH
from app.core.logging import setup_logging
from app.core.config import settings  # ← Import remonté en haut du fichier
import logging
import requests
import sqlite3

# === PATCH : Désactivation du debug LangChain (compatible toutes versions) ===
try:
    from langchain.globals import set_debug
    set_debug(False)
except ImportError:
    # Fallback pour les anciennes versions
    import langchain
    langchain.debug = False

# ============================================================
# 1. Initialisation du logging
# ============================================================
setup_logging()
logger = logging.getLogger(__name__)

# ============================================================
# 2. Création de l'application FastAPI
# ============================================================
app = FastAPI(
    title="SOC Triage Agent API",
    description="Agent IA pour le triage automatique des alertes de sécurité.",
    version="1.1.0"
)

# CORRECTION #10 : CORS - allow_credentials=False avec origins="*"
# La spec CORS interdit credentials=True avec origins="*"
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,  # ← CORRIGÉ : False au lieu de True
    allow_methods=["*"],
    allow_headers=["*"],
)

triage_graph = build_triage_graph()

# ============================================================
# 3. Événements de démarrage
# ============================================================
@app.on_event("startup")
def startup_event():
    init_db()
    logger.info("✅ Base de données initialisée (alerts.db).")

# ============================================================
# 4. Endpoints
# ============================================================
@app.get("/")
def root():
    return {"message": "SOC Triage Agent API is running. Use POST /triage to submit an alert."}

@app.get("/health")
def health_check():
    """
    Health check détaillé : vérifie la disponibilité d'Ollama et de la base de données.
    """
    status = {"status": "healthy", "model": "phi4-mini"}
    
    # CORRECTION #1 & #2 : settings est maintenant importé globalement
    # Vérifier Ollama
    try:
        # CORRECTION #7 : Timeout augmenté à 5s pour éviter les faux positifs
        resp = requests.get(f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=5)
        if resp.status_code == 200:
            status["ollama"] = "reachable"
        else:
            status["ollama"] = "unreachable"
            status["status"] = "degraded"
    except Exception:
        status["ollama"] = "unreachable"
        status["status"] = "degraded"
        logger.warning("Ollama est injoignable")
    
    # CORRECTION #5 & #6 : Gestionnaire de contexte + requête universelle
    try:
        with sqlite3.connect(DB_PATH) as conn:  # ← CORRIGÉ : 'with' garantit la fermeture
            conn.execute("SELECT 1")  # ← CORRIGÉ : Requête universelle (pas besoin de la table)
            status["database"] = "ok"
    except Exception as e:
        status["database"] = "error"
        status["status"] = "degraded"
        logger.error(f"Erreur base de données : {e}")
    
    return status

@app.get("/history")
def get_history(limit: int = 50, after_id: int = 0):
    all_alerts = get_recent_alerts(limit)
    return [a for a in all_alerts if a["id"] > after_id]

@app.post("/feedback")
def add_feedback(alert_id: int, verdict: str, comment: str = ""):
    if verdict not in ["validated", "rejected", "commented"]:
        raise HTTPException(status_code=400, detail="Verdict must be 'validated', 'rejected' or 'commented'")
    try:
        save_feedback(alert_id, verdict, comment)
        logger.info(f"Feedback enregistré pour l'alerte #{alert_id} : {verdict}")
        return {"status": "success", "message": "Feedback enregistré."}
    except Exception as e:
        logger.error(f"Erreur lors de l'enregistrement du feedback : {e}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'enregistrement : {e}")

@app.post("/triage", response_model=TriageResponse)
def triage_alert(alert: Alert):
    """
    IMPORTANT : fonction volontairement en `def` (pas `async def`).
    Elle contient des appels bloquants (Ollama, AbuseIPDB, VirusTotal, SQLite).
    En `async def`, ces appels gèlent TOUTE la boucle d'événements FastAPI,
    empêchant /history de répondre tant qu'un triage tourne — c'est ce qui
    causait le gel du dashboard. En `def` simple, FastAPI exécute la fonction
    dans un thread séparé, laissant l'API répondre aux autres requêtes en
    parallèle.
    """
    logger.info(f"Nouvelle alerte reçue : {alert.event_type} depuis {alert.source_ip}")
    try:
        initial_state = {"alert": alert, "osint_data": None, "triage_result": None}
        final_state = triage_graph.invoke(initial_state)
        result = final_state.get("triage_result")

        if result is None:
            logger.error("L'agent n'a pas produit de résultat.")
            raise HTTPException(status_code=500, detail="L'agent n'a pas produit de résultat.")

        alert_id = save_triage(alert, result)
        logger.info(f"Alerte #{alert_id} triée avec sévérité {result.severity.value}")
        return TriageResponse(id=alert_id, **result.model_dump())

    except HTTPException:
        raise
    except Exception as e:
        # CORRECTION #3 & #4 : Logger l'erreur complète, renvoyer un message générique
        logger.error(f"Erreur lors du triage : {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail="Une erreur interne est survenue lors du triage. Consultez les logs pour plus de détails."
        )