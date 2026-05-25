# Quick Start Guide — Golden Bridge Pre-Arrival System

## Prerequisites

- Python 3.8+
- pip

## Install

```bash
cd HIPAA-Compliant-Medical-Triage-AI-System
pip install -r requirements.txt
```

**Dashboard essentials** (if not already installed):

```bash
pip install streamlit plotly pandas
```

Optional for Presidio-based tests in `test_system.py`:

```bash
pip install presidio-analyzer presidio-anonymizer
python -m spacy download en_core_web_lg
```

Optional for full Pathway + OpenAI RAG pipeline:

```bash
# Pathway may require a supported platform; dashboard demo works without it
export OPENAI_API_KEY=sk-your-key-here   # Windows: set OPENAI_API_KEY=...
```

## Run the dashboard (recommended)

```bash
streamlit run dashboard/advanced_clinical_dashboard.py
```

Open **http://localhost:8501**

### What you will see

- **Fleet sidebar** — multiple ambulances, hospital capacity bars
- **Live vitals** — HR, SpO2, BP with trend charts
- **Clinical intelligence** — 8 scores + severity level
- **Multi-agent consensus** — diagnostic, severity, and protocol agents
- **Human-in-the-loop** — review panel when agents disagree
- **EMS comms tab** — redacted EMT field notes (Aparavi-style)
- **Protocols & AI tab** — activated checklists and intervention forecasts

## Demo flow (5 minutes)

1. Select **P-2024-001** (Chest Pain) — STEMI pathway, alerts, protocols
2. Watch **Multi-agent consensus** — conflicts may trigger **clinician review**
3. Open **Reasoning trace** in the consensus section
4. Click **Confirm severity-led** or **Confirm diagnostic-led** to clear HITL
5. Switch to **P-2024-002** (Stroke) — different pathway and scores
6. Use **Register incoming unit** to add another ambulance
7. Wait for **ETA → 0** — handoff summary and resource updates

## Test components

```bash
python test_system.py
python ai_modules/consensus.py
python ai_modules/clinical_scoring.py
python ai_modules/ai_triage.py
python utils/aparavi_redactor.py
```

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `ModuleNotFoundError: plotly` | `pip install plotly` |
| Port 8501 in use | `streamlit run ... --server.port 8502` |
| Faint metric text | Ensure `.streamlit/config.toml` exists (light theme) |
| Presidio import error | Skip `utils/pii_redactor.py` tests or install Presidio + spaCy |

## Other dashboards (legacy)

```bash
streamlit run dashboard/improved_er_dashboard.py
streamlit run dashboard/er_dashboard.py
```

Use **advanced_clinical_dashboard.py** for presentations.

## Documentation

- [README.md](README.md) — full overview
- [docs/CONSENSUS_LAYER.md](docs/CONSENSUS_LAYER.md) — multi-agent consensus & HITL
- [ADVANCED_FEATURES.md](ADVANCED_FEATURES.md) — technical feature reference
- [IMPROVEMENTS.md](IMPROVEMENTS.md) — changelog-style improvements
