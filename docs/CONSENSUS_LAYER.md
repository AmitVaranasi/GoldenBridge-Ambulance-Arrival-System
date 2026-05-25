# Multi-Agent Consensus Layer

## Overview

Golden Bridge reconciles three logical agents before the ED sees a final triage picture:

| Agent | Role |
|-------|------|
| **DiagnosticAgent** | Primary pathway (STEMI, stroke, trauma, sepsis, etc.) from alerts + predictions |
| **SeverityAgent** | Acuity score and level (CRITICAL → NON-EMERGENT) |
| **ProtocolAgent** | Which hospital protocols should be active |

Implementation: `ai_modules/consensus.py`  
Dashboard integration: `calculate_clinical_scores()` → `run_consensus()` → UI panels in `advanced_clinical_dashboard.py`

## Resolution policy

1. **No conflicts** → `AUTO` — all agent outputs pass through unchanged.
2. **Conflicts + CRITICAL/EMERGENT severity** → `SEVERITY_OVERRIDE` — severity agent may raise acuity to the pathway floor, but **HITL is still required** if diagnostic and severity disagree.
3. **Other conflicts** → `HITL_PENDING` — no silent auto-merge; clinician must confirm.
4. **After clinician button** → `CLINICIAN_CONFIRMED` — choice logged in reasoning trace.

## Human-in-the-loop (dashboard)

When `requires_hitl` is true, the dashboard shows:

- Conflict list with agent attribution
- Expandable **reasoning trace** (audit log)
- Three actions: **Confirm severity-led**, **Confirm diagnostic-led**, **Escalate to attending**

Sidebar shows count of patients awaiting review.

## Run tests

```bash
python ai_modules/consensus.py
python test_system.py
```
