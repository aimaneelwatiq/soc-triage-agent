# dashboard.py
# Tableau de bord SOC Intelligent - Streamlit (sans Plotly)

import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import time

st.set_page_config(
    page_title="SOC Intelligent Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Constantes ---
API_BASE_URL = "http://localhost:8000"
HEALTH_ENDPOINT = f"{API_BASE_URL}/health"
HISTORY_ENDPOINT = f"{API_BASE_URL}/history"
TRIAGE_ENDPOINT = f"{API_BASE_URL}/triage"
FEEDBACK_ENDPOINT = f"{API_BASE_URL}/feedback"

# --- Fonctions API ---
@st.cache_data(ttl=10)
def get_api_status():
    try:
        r = requests.get(HEALTH_ENDPOINT, timeout=3)
        if r.status_code == 200:
            return True, r.json()
        else:
            return False, {"error": f"Code {r.status_code}"}
    except Exception as e:
        return False, {"error": str(e)}

@st.cache_data(ttl=30)
def fetch_alerts(limit=100, after_id=0):
    try:
        params = {"limit": limit, "after_id": after_id}
        r = requests.get(HISTORY_ENDPOINT, params=params, timeout=5)
        if r.status_code == 200:
            return r.json()
        else:
            st.error(f"Erreur API /history : {r.status_code}")
            return []
    except Exception as e:
        st.error(f"Impossible de contacter l'API : {e}")
        return []

def submit_alert(alert_data):
    try:
        r = requests.post(TRIAGE_ENDPOINT, json=alert_data, timeout=10)
        if r.status_code == 200:
            return True, r.json()
        else:
            return False, f"Erreur {r.status_code}: {r.text}"
    except Exception as e:
        return False, str(e)

def send_feedback(alert_id, verdict, comment=""):
    try:
        payload = {"alert_id": alert_id, "verdict": verdict, "comment": comment}
        r = requests.post(FEEDBACK_ENDPOINT, json=payload, timeout=5)
        if r.status_code == 200:
            return True, r.json()
        else:
            return False, f"Erreur {r.status_code}"
    except Exception as e:
        return False, str(e)

# --- Sidebar ---
with st.sidebar:
    st.title("🛡️ SOC Intelligent")
    st.markdown("---")

    api_ok, api_info = get_api_status()
    if api_ok:
        st.success("✅ API connectée")
        with st.expander("Détails"):
            st.json(api_info)
    else:
        st.error("❌ API hors ligne")
        st.info("Vérifiez que l'API est lancée avec :\n`uvicorn app.api.main:app --host 0.0.0.0 --port 8000`")
        st.stop()

    st.markdown("---")
    st.subheader("Filtres")

    if "filters" not in st.session_state:
        st.session_state.filters = {"severity": [], "search": ""}

    severity_options = ["Critical", "High", "Medium", "Low", "Informational"]
    selected_severities = st.multiselect(
        "Sévérité",
        options=severity_options,
        default=st.session_state.filters["severity"],
        key="severity_filter"
    )
    st.session_state.filters["severity"] = selected_severities

    search_term = st.text_input(
        "Rechercher (host / IP / type)",
        value=st.session_state.filters["search"],
        key="search_filter"
    )
    st.session_state.filters["search"] = search_term

    st.markdown("---")
    if st.button("🔄 Rafraîchir les données"):
        st.cache_data.clear()
        st.rerun()

# --- Corps principal ---
st.title("📊 SOC Console")

alerts_data = fetch_alerts(limit=200)

if not alerts_data:
    st.warning("Aucune alerte récupérée. Soumettez une alerte pour commencer.")
    alerts_df = pd.DataFrame()
else:
    rows = []
    for item in alerts_data:
        alert = item.get("alert", {})
        result = item.get("result", {})
        row = {
            "id": item.get("id"),
            "timestamp": item.get("timestamp"),
            "event_type": alert.get("event_type", "N/A"),
            "source_ip": alert.get("source_ip", "N/A"),
            "username": alert.get("username", "N/A"),
            "hostname": alert.get("hostname", "N/A"),
            "rule_description": alert.get("rule_description", "N/A"),
            "severity": result.get("severity", "Unknown"),
            "confidence_score": result.get("confidence_score", 0.0),
            "justification": result.get("justification", ""),
            "suggested_action": result.get("suggested_action", ""),
            "feedback_verdict": item.get("feedback", {}).get("verdict", None),
            "feedback_comment": item.get("feedback", {}).get("comment", ""),
        }
        rows.append(row)
    alerts_df = pd.DataFrame(rows)

if not alerts_df.empty:
    df_filtered = alerts_df.copy()
    if st.session_state.filters["severity"]:
        df_filtered = df_filtered[df_filtered["severity"].isin(st.session_state.filters["severity"])]
    search = st.session_state.filters["search"].strip().lower()
    if search:
        mask = (
            df_filtered["event_type"].str.lower().str.contains(search, na=False) |
            df_filtered["hostname"].str.lower().str.contains(search, na=False) |
            df_filtered["source_ip"].str.lower().str.contains(search, na=False) |
            df_filtered["username"].str.lower().str.contains(search, na=False)
        )
        df_filtered = df_filtered[mask]

    # Métriques
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Alertes totales", len(df_filtered))
    with col2:
        critical = len(df_filtered[df_filtered["severity"] == "Critical"])
        st.metric("⚠️ Critical", critical)
    with col3:
        high = len(df_filtered[df_filtered["severity"] == "High"])
        st.metric("🔴 High", high)
    with col4:
        avg_conf = df_filtered["confidence_score"].mean() if not df_filtered.empty else 0
        st.metric("Confiance moyenne", f"{avg_conf:.2f}")

    # Graphiques (sans Plotly)
    col_charts = st.columns(2)
    with col_charts[0]:
        # Répartition par sévérité
        severity_counts = df_filtered["severity"].value_counts()
        # Convertir en DataFrame pour st.bar_chart
        severity_df = severity_counts.reset_index()
        severity_df.columns = ["Sévérité", "Nombre"]
        st.subheader("Répartition des sévérités")
        st.bar_chart(severity_df.set_index("Sévérité"))

    with col_charts[1]:
        # Distribution des scores de confiance (CORRIGÉE)
        # Créer des bins avec labels en chaînes
        bins = [0, 0.25, 0.5, 0.75, 1.0]
        labels = ["0-0.25", "0.25-0.5", "0.5-0.75", "0.75-1.0"]
        df_filtered["confidence_bin"] = pd.cut(
            df_filtered["confidence_score"],
            bins=bins,
            labels=labels,
            include_lowest=True
        )
        conf_counts = df_filtered["confidence_bin"].value_counts().sort_index()
        # Convertir en DataFrame pour st.bar_chart
        conf_df = conf_counts.reset_index()
        conf_df.columns = ["Intervalle", "Nombre"]
        # L'intervalle est déjà une chaîne (grâce aux labels)
        st.subheader("Distribution du score de confiance")
        st.bar_chart(conf_df.set_index("Intervalle"))

    # Tableau des alertes
    st.subheader("📋 Détail des alertes")
    display_cols = ["id", "timestamp", "severity", "event_type", "source_ip", "username",
                    "hostname", "confidence_score", "suggested_action", "feedback_verdict"]
    available_cols = [c for c in display_cols if c in df_filtered.columns]
    st.dataframe(
        df_filtered[available_cols],
        column_config={
            "id": "ID",
            "timestamp": "Horodatage",
            "severity": st.column_config.SelectboxColumn("Sévérité", options=severity_options),
            "event_type": "Type",
            "source_ip": "IP Source",
            "username": "Utilisateur",
            "hostname": "Hôte",
            "confidence_score": st.column_config.NumberColumn("Confiance", format="%.2f"),
            "suggested_action": "Action suggérée",
            "feedback_verdict": "Feedback"
        },
        use_container_width=True,
        height=400
    )

    # Zone de détails et feedback
    st.subheader("🔍 Détails d'une alerte")
    if not df_filtered.empty:
        selected_id = st.selectbox("Choisir un ID d'alerte", options=df_filtered["id"].unique(), key="detail_select")
        row = df_filtered[df_filtered["id"] == selected_id].iloc[0]
        with st.expander(f"Alerte #{selected_id} - {row['event_type']}", expanded=True):
            col_detail = st.columns(2)
            with col_detail[0]:
                st.markdown(f"**Sévérité :** {row['severity']}")
                st.markdown(f"**Confiance :** {row['confidence_score']:.2f}")
                st.markdown(f"**IP Source :** {row['source_ip']}")
                st.markdown(f"**Hôte :** {row['hostname']}")
                st.markdown(f"**Utilisateur :** {row['username']}")
            with col_detail[1]:
                st.markdown(f"**Justification :**\n{row['justification']}")
                st.markdown(f"**Action suggérée :**\n{row['suggested_action']}")
                if row['feedback_verdict']:
                    st.info(f"Feedback : {row['feedback_verdict']} - {row['feedback_comment']}")

        # Formulaire de feedback
        with st.form(key="feedback_form"):
            st.subheader("Donner un feedback")
            verdict = st.selectbox("Verdict", options=["validated", "rejected", "commented"], key="verdict_sel")
            comment = st.text_area("Commentaire (optionnel)", key="comment_sel")
            submitted = st.form_submit_button("Envoyer le feedback")
            if submitted:
                ok, msg = send_feedback(selected_id, verdict, comment)
                if ok:
                    st.success("Feedback enregistré !")
                    st.cache_data.clear()
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"Erreur : {msg}")

# --- Soumettre une nouvelle alerte ---
st.markdown("---")
with st.expander("➕ Soumettre une nouvelle alerte (test)"):
    with st.form(key="submit_alert_form"):
        col_form = st.columns(2)
        with col_form[0]:
            event_type = st.text_input("Type d'événement", value="SSH_Failed_Login")
            source_ip = st.text_input("IP Source", value="8.8.8.8")
            username = st.text_input("Nom d'utilisateur", value="admin")
            hostname = st.text_input("Hôte", value="server01")
        with col_form[1]:
            timestamp = st.text_input("Timestamp (ISO)", value=datetime.now().isoformat())
            raw_log = st.text_area("Log brut", value="Failed password for admin from 8.8.8.8 port 22")
            rule_id = st.text_input("Rule ID", value="1001")
            rule_description = st.text_input("Règle", value="SSH Failed Login")
        submit_btn = st.form_submit_button("🚀 Soumettre l'alerte")
        if submit_btn:
            alert_payload = {
                "event_type": event_type,
                "timestamp": timestamp,
                "source_ip": source_ip,
                "destination_ip": None,
                "username": username,
                "hostname": hostname,
                "raw_log": raw_log,
                "rule_id": rule_id,
                "rule_description": rule_description,
                "extra": {}
            }
            ok, result = submit_alert(alert_payload)
            if ok:
                st.success(f"Alerte soumise avec succès ! ID : {result.get('id')}")
                st.cache_data.clear()
                time.sleep(1)
                st.rerun()
            else:
                st.error(f"Erreur : {result}")

st.markdown("---")
st.caption("SOC Intelligent Dashboard - v1.0 - Soutenance")