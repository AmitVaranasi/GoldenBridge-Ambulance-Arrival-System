# Multi-Agent Consensus Layer

## Overview

Golden Bridge reconciles three logical agents before the ED sees a final triage picture. Agents can disagree; the system does **not** silently pick a winner without policy or clinician input.

| Agent | Module | Role |
|-------|--------|------|
| **DiagnosticAgent** | `consensus.py` | Primary pathway (STEMI, stroke, trauma, sepsis, arrest risk) from alerts + predictions + presentation |
| **SeverityAgent** | `consensus.py` | Acuity score and level (CRITICAL → NON-EMERGENT) |
| **ProtocolAgent** | `consensus.py` | Which hospital protocols should be active vs alerts |

**Pipeline:** `ClinicalScorer` → `AITriagePredictor` → `ConsensusEngine.reconcile()` → dashboard UI

## Resolution modes

| Mode | When | Behavior |
|------|------|----------|
| `AUTO` | No conflicts | Pass through agent outputs unchanged |
| `SEVERITY_OVERRIDE` | Conflicts + CRITICAL/EMERGENT | Severity may be raised to pathway floor; **HITL still required** if diagnostic disagrees |
| `HITL_PENDING` | Unresolved conflicts | Clinician must confirm; no silent auto-merge |
| `CLINICIAN_CONFIRMED` | After button click | Choice logged in reasoning trace |

## Conflict examples

- STEMI alert active but severity score below emergent threshold
- Diagnostic pathway implies higher acuity than severity agent reported
- Competing pathways (e.g. STEMI vs stroke) both above confidence threshold
- Protocol agent missing expected activation for an active alert
- Presentation mismatch (e.g. stroke pathway with non-stroke chief complaint)

## Human-in-the-loop (dashboard)

When `requires_hitl` is true:

1. Red **Human-in-the-loop review required** banner
2. **Detected conflicts** list with agent attribution
3. **Reasoning trace** expander (audit log)
4. Clinician actions:
   - **Confirm severity-led plan**
   - **Confirm diagnostic-led plan**
   - **Escalate to attending**

Sidebar shows **N need clinician review** for pending cases.

## API usage

```python
from ai_modules.consensus import ConsensusEngine

result = ConsensusEngine.reconcile(
    patient_id="P-2024-001",
    chief_complaint="Chest Pain",
    severity={"score": 65, "level": "EMERGENT", "contributing_factors": []},
    alerts=["STEMI"],
    predictions={"predictions": {"likely_stemi": True}, "confidence_scores": {"stemi": 0.9}},
    protocols={"STEMI_PROTOCOL": ["Activate cath lab"]},
    scores={},
    clinician_ack=None,  # or {"choice": "severity", "role": "ED clinician"}
)

print(result["resolution_mode"])
print(result["requires_hitl"])
print(result["final_severity"])
for step in result["reasoning_trace"]:
    print(step)
```

## Tests

```bash
python ai_modules/consensus.py
python test_system.py   # includes consensus test (Test 5)
```

## Related files

- `ai_modules/consensus.py` — agents + engine
- `dashboard/advanced_clinical_dashboard.py` — `run_consensus()`, HITL UI
- `ai_modules/ai_triage.py` — upstream triage outputs
