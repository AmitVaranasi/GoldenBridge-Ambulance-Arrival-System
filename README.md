# Golden Bridge Ambulance Pre-Arrival System

HIPAA-aware clinical command platform that streams ambulance telemetry and EMT updates to the ED before arrival — with AI scoring, protocol activation, multi-agent consensus, and clinician review when agents disagree.

Built for hackathon/demo use with **Pathway** (streaming scaffold), **Streamlit** (operations UI), and optional **OpenAI RAG** (pipeline module).

---

## Problem

- ER teams lack context until the gurney arrives
- Vitals and treatments are lost in verbal handoffs
- No standardized, auditable pre-arrival triage
- Resources (ICU, CT, OR) are allocated reactively
- Competing AI signals must not auto-merge without oversight in healthcare

---

## Solution

| Capability | Description |
|------------|-------------|
| Live telemetry | Simulated HR, SpO2, BP every ~2s |
| Multi-ambulance fleet | Track many units; register new arrivals |
| 8 clinical scores | Severity, shock index, STEMI, qSOFA, RTS, NIHSS, airway, deterioration |
| Alerts & predictions | STEMI, stroke, trauma, sepsis, arrest risk + intervention forecast |
| Protocol activation | STEMI, stroke, trauma, sepsis, airway, code blue checklists |
| Hospital capacity | ICU, CT, MRI, OR, blood, ventilators — updates on arrival |
| EMS treatments | Medications and interventions by chief complaint |
| Handoff summary | Auto-generated when ETA reaches zero |
| PHI redaction | Aparavi-style redaction on EMT notes in dashboard |
| **Multi-agent consensus** | Diagnostic, severity, and protocol agents reconciled with audit trace |
| **Human-in-the-loop** | Clinician confirmation when agents conflict — no silent override |

---

## Architecture

```
Telemetry + voice simulators
        │
        ▼
ClinicalScorer (8 scores)
        │
        ▼
AITriagePredictor (severity, alerts, predictions, protocols)
        │
        ▼
ConsensusEngine (Diagnostic + Severity + Protocol agents)
        │
        ├── AUTO / SEVERITY_OVERRIDE / HITL_PENDING / CLINICIAN_CONFIRMED
        │
        ▼
Streamlit Clinical Command Dashboard
```

### Technology stack

| Layer | Technology |
|-------|------------|
| Dashboard | Streamlit 1.x, Plotly, Pandas |
| Clinical logic | Python rule engines (`clinical_scoring`, `ai_triage`) |
| Consensus / HITL | `ai_modules/consensus.py` |
| UI theme | `dashboard/ui_theme.py` |
| PHI (demo) | `utils/aparavi_redactor.py` (pattern-based; API-ready) |
| PHI (pipeline) | `utils/pii_redactor.py` (Presidio, optional) |
| Streaming (optional) | Pathway 0.13 + OpenAI RAG in `pipeline/ambulance_pipeline.py` |

---

## Quick start

```bash
git clone https://github.com/AmitVaranasi/HIPAA-Compliant-Medical-Triage-AI-System.git
cd HIPAA-Compliant-Medical-Triage-AI-System
pip install -r requirements.txt
pip install streamlit plotly pandas
streamlit run dashboard/advanced_clinical_dashboard.py
```

Open **http://localhost:8501**

See [QUICKSTART.md](QUICKSTART.md) for demo script and troubleshooting.

---

## Dashboard (main app)

**File:** `dashboard/advanced_clinical_dashboard.py`

### Sidebar

- **Fleet** — select patient, register incoming unit, en route / arrived counts
- **Hospital capacity** — progress bars for ICU, CT, OR, vents, blood
- **HITL queue** — count of patients needing clinician review
- System status — AI scoring, consensus layer, PII shield

### Main panel

- Patient hero + ETA + consensus-adjusted severity
- Live vitals metrics + trend charts
- Active clinical alerts
- **Multi-agent consensus** — three agent outputs, conflicts, reasoning trace
- **Human-in-the-loop** — confirm severity-led, diagnostic-led, or escalate
- Clinical intelligence metrics (8 scores)
- Tabs: Protocols & AI · Pre-hospital care · EMS comms (redacted)

---

## Multi-agent consensus

Three logical agents run after each triage update:

1. **DiagnosticAgent** — primary pathway (STEMI, stroke, trauma, sepsis, …)
2. **SeverityAgent** — acuity score / level
3. **ProtocolAgent** — activated vs expected protocols

**Policy:**

- Aligned agents → `AUTO`
- Critical/emergent conflict → severity may override acuity floor, but **HITL still required** if diagnostic disagrees
- Other conflicts → `HITL_PENDING` until clinician confirms
- Confirmed choice → `CLINICIAN_CONFIRMED` with trace entry

Full detail: [docs/CONSENSUS_LAYER.md](docs/CONSENSUS_LAYER.md)

---

## Project structure

```
HIPAA-Compliant-Medical-Triage-AI-System/
├── dashboard/
│   ├── advanced_clinical_dashboard.py   # Main UI (use this)
│   ├── ui_theme.py                      # Clinical UI theme + Plotly styling
│   ├── improved_er_dashboard.py         # Legacy
│   └── er_dashboard.py                  # Legacy
├── ai_modules/
│   ├── clinical_scoring.py
│   ├── ai_triage.py
│   ├── consensus.py                     # Multi-agent consensus + HITL
│   └── __init__.py
├── simulators/
│   ├── telemetry_simulator.py
│   └── emt_voice_simulator.py
├── utils/
│   ├── aparavi_redactor.py              # Dashboard PHI redaction
│   └── pii_redactor.py                  # Presidio (pipeline / tests)
├── pipeline/
│   └── ambulance_pipeline.py            # Pathway + OpenAI RAG (optional)
├── data/
│   └── hospital_protocols.txt
├── docs/
│   └── CONSENSUS_LAYER.md
├── .streamlit/
│   └── config.toml                      # Light theme for readability
├── requirements.txt
├── test_system.py
├── README.md
├── QUICKSTART.md
├── ADVANCED_FEATURES.md
└── IMPROVEMENTS.md
```

---

## Testing

```bash
python test_system.py
python ai_modules/consensus.py
python ai_modules/clinical_scoring.py
python ai_modules/ai_triage.py
python utils/aparavi_redactor.py
```

---

## Data streams (simulated)

**Telemetry (~2s):** `heart_rate`, `spo2`, `blood_pressure_systolic`, `blood_pressure_diastolic`, `timestamp`

**Voice notes (~15s):** `voice_note` (redacted before ED display), `eta_minutes`, `ambulance_id`

---

## HIPAA / privacy (demo scope)

- Pattern-based PII redaction on EMT notes before display
- In-memory demo only — not a full HIPAA control set (no auth, audit DB, encryption at rest)
- Production would use Aparavi API + organizational BAA processes

---

## Hackathon alignment

| Requirement | Status |
|-------------|--------|
| Pathway framework | Scaffold in `pipeline/` + simulators |
| Pathway LLM xPack | RAG in pipeline (optional; needs API key) |
| Aparavi / PHI | `aparavi_redactor` in dashboard |
| Dual streams | Telemetry + voice simulators |
| Real-time UX | 2s dashboard refresh |
| Clinical AI | Scores, triage, consensus, HITL |

---

## Documentation

| Doc | Purpose |
|-----|---------|
| [README.md](README.md) | Overview (this file) |
| [QUICKSTART.md](QUICKSTART.md) | Run & demo in 5 minutes |
| [docs/CONSENSUS_LAYER.md](docs/CONSENSUS_LAYER.md) | Consensus & HITL design |
| [ADVANCED_FEATURES.md](ADVANCED_FEATURES.md) | Feature-level technical reference |
| [IMPROVEMENTS.md](IMPROVEMENTS.md) | Version history & enhancements |

---

## Quick reference

| Action | Command / location |
|--------|-------------------|
| Run dashboard | `streamlit run dashboard/advanced_clinical_dashboard.py` |
| Add ambulance | Sidebar → **Register incoming unit** |
| Switch patient | Sidebar → **View** on fleet card |
| Clinician review | Main panel when HITL banner appears |
| Reasoning trace | **Multi-agent consensus** → expander |
| Test consensus | `python ai_modules/consensus.py` |

---

**Version:** 3.0.0  
**Last updated:** May 2025  
**Repository:** https://github.com/AmitVaranasi/HIPAA-Compliant-Medical-Triage-AI-System
