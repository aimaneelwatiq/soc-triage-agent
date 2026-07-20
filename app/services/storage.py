import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from app.models.alert import Alert
from app.models.triage import TriageResult

DB_PATH = "alerts.db"

def init_db():
    """Crée les tables si elles n'existent pas."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS triages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            alert_json TEXT NOT NULL,
            result_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alert_id INTEGER NOT NULL,
            verdict TEXT NOT NULL,
            comment TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (alert_id) REFERENCES triages(id)
        )
    """)
    
    conn.commit()
    conn.close()

def save_triage(alert: Alert, result: TriageResult) -> int:
    """Sauvegarde une alerte et retourne son ID."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    alert_json = alert.model_dump_json()
    result_json = result.model_dump_json()
    
    cursor.execute("""
        INSERT INTO triages (timestamp, alert_json, result_json, created_at)
        VALUES (?, ?, ?, ?)
    """, (alert.timestamp.isoformat(), alert_json, result_json, datetime.now().isoformat()))
    
    alert_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return alert_id

def save_feedback(alert_id: int, verdict: str, comment: str = ""):
    """Sauvegarde le feedback d'un analyste."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO feedback (alert_id, verdict, comment, created_at)
        VALUES (?, ?, ?, ?)
    """, (alert_id, verdict, comment, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_recent_alerts(limit: int = 50) -> List[Dict[str, Any]]:
    """Récupère les derniers triages avec leurs feedbacks."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            t.id, t.timestamp, t.alert_json, t.result_json, t.created_at,
            f.verdict as feedback_verdict, f.comment as feedback_comment
        FROM triages t
        LEFT JOIN feedback f ON t.id = f.alert_id
        ORDER BY t.id DESC
        LIMIT ?
    """, (limit,))
    
    rows = cursor.fetchall()
    conn.close()
    
    results = []
    for row in rows:
        item = {
            "id": row["id"],
            "timestamp": row["timestamp"],
            "alert": json.loads(row["alert_json"]),
            "result": json.loads(row["result_json"]),
            "created_at": row["created_at"]
        }
        if row["feedback_verdict"]:
            item["feedback"] = {
                "verdict": row["feedback_verdict"],
                "comment": row["feedback_comment"]
            }
        results.append(item)
    return results

def get_alert_by_id(alert_id: int) -> Optional[Dict[str, Any]]:
    """Récupère une alerte spécifique par son ID (utile pour debug/vérification)."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            t.id, t.timestamp, t.alert_json, t.result_json, t.created_at,
            f.verdict as feedback_verdict, f.comment as feedback_comment
        FROM triages t
        LEFT JOIN feedback f ON t.id = f.alert_id
        WHERE t.id = ?
    """, (alert_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row is None:
        return None
    
    item = {
        "id": row["id"],
        "timestamp": row["timestamp"],
        "alert": json.loads(row["alert_json"]),
        "result": json.loads(row["result_json"]),
        "created_at": row["created_at"]
    }
    if row["feedback_verdict"]:
        item["feedback"] = {
            "verdict": row["feedback_verdict"],
            "comment": row["feedback_comment"]
        }
    return item