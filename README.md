<div align="center">

<img src="docs/images/logo.svg" alt="SOC Triage Agent" width="120">

# 🔒 SOC Triage Agent

**AI-Powered Security Alert Triage for Modern SOCs**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2%2B-1C3C3C?logo=langchain&logoColor=white)](https://langchain.com)
[![Ollama](https://img.shields.io/badge/Ollama-Local%20LLM-FF6F00?logo=ollama&logoColor=white)](https://ollama.com)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-Passing-brightgreen?logo=pytest&logoColor=white)]()

</div>

---

## 📖 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Architecture](#-architecture)
- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [API Endpoints](#-api-endpoints)
- [Screenshots](#-screenshots)
- [Tech Stack](#-tech-stack)
- [Roadmap](#-roadmap)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🎯 Overview

**SOC Triage Agent** is an intelligent, open-source security operations center (SOC) assistant that automates the triage of security alerts using **local LLMs** and **OSINT enrichment**. Built for privacy-conscious organizations, it processes alerts from SIEMs like Wazuh, enriches them with threat intelligence, and classifies severity — all without sending sensitive data to external APIs.

<div align="center">

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌─────────────┐
│   Alert     │────▶│   Enrich     │────▶│  Classify   │────▶│   Assess    │
│  (Wazuh)    │     │  (OSINT)     │     │   (LLM)     │     │  (Result)   │
└─────────────┘     └──────────────┘     └─────────────┘     └─────────────┘
```

</div>

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🤖 **Local LLM Classification** | Uses Ollama with `phi4-mini` — no data leaves your network |
| 🔍 **OSINT Enrichment** | Auto-queries AbuseIPDB & VirusTotal for IP reputation |
| 🛡️ **Heuristic Fallback** | Rule-based fallback when LLM is unavailable (MITRE ATT&CK aligned) |
| ⚡ **Smart Caching** | 5-minute TTL cache for OSINT lookups to reduce API costs |
| 🔄 **Retry with Backoff** | Automatic retry on LLM failures (3 attempts, exponential backoff) |
| 📊 **Feedback Loop** | Analysts can validate/reject triage results for continuous improvement |
| 🏥 **Health Monitoring** | Built-in `/health` endpoint checks Ollama & database status |
| 📱 **REST API** | Full FastAPI backend with auto-generated OpenAPI docs |
| 🎨 **Dashboard** | Interactive web dashboard for real-time alert monitoring |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FASTAPI API LAYER                              │
│  ┌─────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │
│  │  GET /  │  │ /health  │  │ /triage  │  │ /history │  │ /feedback    │  │
│  └─────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           LANGGRAPH AGENT WORKFLOW                          │
│                                                                             │
│   ┌─────────┐    ┌──────────┐    ┌───────────┐    ┌──────────┐            │
│   │  START  │───▶│  enrich  │───▶│  classify │───▶│  assess  │───▶ END   │
│   └─────────┘    └──────────┘    └───────────┘    └──────────┘            │
│                        │                │                                   │
│                        ▼                ▼                                   │
│               ┌─────────────┐   ┌──────────────┐                           │
│               │ AbuseIPDB   │   │ Ollama LLM   │                           │
│               │ VirusTotal  │   │ Heuristic FB │                           │
│               └─────────────┘   └──────────────┘                           │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DATA LAYER                                     │
│                                                                             │
│   ┌──────────────┐              ┌─────────────────┐                        │
│   │   SQLite     │              │   OSINT Cache   │                        │
│   │  (alerts.db) │              │   (in-memory)   │                        │
│   │  • triages   │              │   TTL: 5 min    │                        │
│   │  • feedback  │              │   Max: 1000 IPs │                        │
│   └──────────────┘              └─────────────────┘                        │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Project Structure

```
soc-triage-agent/
├── app/
│   ├── agent/              # LangGraph workflow orchestration
│   │   ├── graph.py        # StateGraph definition
│   │   ├── nodes.py        # Node logic (enrich, classify, assess)
│   │   └── state.py        # AgentState TypedDict
│   │
│   ├── api/                # FastAPI application
│   │   └── main.py         # Endpoints & middleware
│   │
│   ├── core/               # Configuration & logging
│   │   ├── config.py       # Environment settings
│   │   └── logging.py      # Logging configuration
│   │
│   ├── integrations/       # External API clients
│   │   ├── abuseipdb.py    # AbuseIPDB reputation checks
│   │   ├── virustotal.py   # VirusTotal analysis
│   │   └── wazuh_client.py # Wazuh SIEM integration (WIP)
│   │
│   ├── models/             # Pydantic data models
│   │   ├── alert.py        # Alert schema (SIEM input)
│   │   └── triage.py       # TriageResult & SeverityLevel
│   │
│   ├── services/           # Business logic
│   │   ├── classification.py   # LLM + heuristic classification
│   │   ├── enrichment.py       # OSINT aggregation & caching
│   │   ├── storage.py          # SQLite persistence
│   │   └── suggestion.py       # Action suggestions (WIP)
│   │
│   └── utils/              # Utilities
│       ├── json_parser.py  # Robust JSON extraction from LLM
│       └── retry.py        # Retry decorator with backoff
│
├── tests/                  # Test suite
│   ├── unit/               # Unit tests
│   └── integration/        # Integration tests
│
├── docs/                   # Documentation & assets
├── dashboard.py            # Interactive web dashboard
├── alerts.db               # SQLite database
├── .env                    # Environment variables
├── requirements.txt        # Python dependencies
└── README.md               # You are here!
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com) installed locally
- `phi4-mini` model pulled: `ollama pull phi4-mini`

### 1. Clone & Setup

```bash
git clone https://github.com/aimaneelwatiq/soc-triage-agent.git
cd soc-triage-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your API keys (optional for OSINT features)
```

### 3. Start the API

```bash
uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Test It

```bash
curl -X POST http://localhost:8000/triage \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "SSH Bruteforce",
    "timestamp": "2026-07-20T10:00:00Z",
    "source_ip": "192.0.2.1",
    "raw_log": "Failed password for root from 192.0.2.1",
    "rule_description": "Multiple SSH login failures"
  }'
```

**Response:**
```json
{
  "id": 1,
  "severity": "High",
  "justification": "SSH bruteforce detected with high confidence...",
  "suggested_action": "Block source IP and review authentication logs",
  "confidence_score": 0.85,
  "osint_context": {
    "abuseipdb": {"score": 92, "country": "CN", "total_reports": 150},
    "virustotal": {"malicious_count": 8, "reputation": -100}
  }
}
```

---

## 🔧 Installation

### Full Setup (with OSINT features)

```bash
# 1. Clone repository
git clone https://github.com/aimaneelwatiq/soc-triage-agent.git
cd soc-triage-agent

# 2. Create environment
python -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure
# Get free API keys:
# • AbuseIPDB: https://www.abuseipdb.com/api.html
# • VirusTotal: https://www.virustotal.com/gui/join-us
# Add them to .env

# 5. Initialize database
python -c "from app.services.storage import init_db; init_db()"

# 6. Start services
# Terminal 1: Ollama
ollama serve

# Terminal 2: API
uvicorn app.api.main:app --reload

# Terminal 3: Dashboard (optional)
streamlit run dashboard.py
```

### Docker (Coming Soon)

```bash
docker-compose up -d
```

---

## ⚙️ Configuration

Create a `.env` file in the project root:

```env
# ─── Ollama LLM ───
OLLAMA_BASE_URL=http://localhost:11434
MODEL_NAME=phi4-mini
TEMPERATURE=0.1
MAX_TOKENS=800

# ─── OSINT APIs (Optional) ───
VT_API_KEY=your_virustotal_api_key
ABUSEIPDB_API_KEY=your_abuseipdb_api_key

# ─── Application ───
LOG_LEVEL=INFO
DB_PATH=alerts.db
CACHE_TTL=300
```

---

## 📡 API Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `GET` | `/` | API info & status | No |
| `GET` | `/health` | Health check (Ollama + DB) | No |
| `POST` | `/triage` | Submit alert for triage | No |
| `GET` | `/history` | Get recent triages | No |
| `POST` | `/feedback` | Submit analyst feedback | No |

### Interactive API Docs

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 📸 Screenshots

<div align="center">

| Dashboard | API Docs | Alert Detail |
|-----------|----------|--------------|
| <img src="docs/images/dashboard-preview.png" width="280"> | <img src="docs/images/swagger-preview.png" width="280"> | <img src="docs/images/alert-detail.png" width="280"> |

</div>

---

## 🛠️ Tech Stack

<div align="center">

| Category | Technology |
|----------|------------|
| **Backend** | ![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white) ![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white) |
| **AI/ML** | ![LangGraph](https://img.shields.io/badge/LangGraph-1C3C3C?logo=langchain&logoColor=white) ![Ollama](https://img.shields.io/badge/Ollama-FF6F00?logo=ollama&logoColor=white) |
| **Database** | ![SQLite](https://img.shields.io/badge/SQLite-003B57?logo=sqlite&logoColor=white) |
| **OSINT** | AbuseIPDB API, VirusTotal API |
| **Testing** | ![Pytest](https://img.shields.io/badge/Pytest-0A9EDC?logo=pytest&logoColor=white) |
| **Dashboard** | Streamlit |

</div>

---

## 🗺️ Roadmap

- [x] Core triage pipeline (LangGraph)
- [x] OSINT enrichment (AbuseIPDB + VirusTotal)
- [x] Heuristic fallback classification
- [x] SQLite persistence & feedback loop
- [x] REST API with FastAPI
- [x] Interactive dashboard
- [x] Health monitoring endpoint
- [ ] Wazuh SIEM auto-ingestion
- [ ] ML-based severity prediction
- [ ] PostgreSQL support
- [ ] JWT authentication
- [ ] Rate limiting
- [ ] Docker deployment
- [ ] CI/CD pipeline
- [ ] Prometheus metrics

---

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) first.

```bash
# Fork & clone
git clone https://github.com/aimaneelwatiq/soc-triage-agent.git

# Create branch
git checkout -b feature/amazing-feature

# Commit
git commit -m "Add amazing feature"

# Push
git push origin feature/amazing-feature

# Open Pull Request
```

---

## 📄 License

Distributed under the MIT License. See [LICENSE](LICENSE) for more information.

---

<div align="center">

**Made with ❤️ for the security community**

[⭐ Star this repo](https://github.com/aimaneelwatiq/soc-triage-agent) if you find it useful!

</div>
