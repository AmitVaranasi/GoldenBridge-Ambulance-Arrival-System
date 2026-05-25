"""
Golden Bridge — Advanced Clinical Command Dashboard
Multi-ambulance monitoring, AI clinical scores, and resource management.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
from datetime import datetime
import sys
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from simulators.telemetry_simulator import TelemetrySimulator
from simulators.emt_voice_simulator import EMTVoiceSimulator
from utils.aparavi_redactor import AparaviRedactor
from ai_modules.clinical_scoring import ClinicalScorer
from ai_modules.ai_triage import AITriagePredictor
from ai_modules.consensus import ConsensusEngine
from ui_theme import (
    inject_global_css,
    brand_header,
    patient_hero,
    handoff_html,
    resource_bar,
    sidebar_fleet_hint,
    apply_plotly_theme,
    show_html,
    ALERT_STYLES,
)

st.set_page_config(
    page_title="Golden Bridge | Clinical Command",
    page_icon="🚑",
    layout="wide",
    initial_sidebar_state="expanded",
)

show_html(inject_global_css())


def section_title(text: str):
    st.markdown(f"##### {text}")


def initialize_session_state():
    if "patients" not in st.session_state:
        st.session_state.patients = {}
    if "selected_patient" not in st.session_state:
        st.session_state.selected_patient = "P-2024-001"
    if "aparavi_redactor" not in st.session_state:
        st.session_state.aparavi_redactor = AparaviRedactor()
    if "scorer" not in st.session_state:
        st.session_state.scorer = ClinicalScorer()
    if "predictor" not in st.session_state:
        st.session_state.predictor = AITriagePredictor()
    if "next_patient_num" not in st.session_state:
        st.session_state.next_patient_num = 4
    if "next_amb_num" not in st.session_state:
        st.session_state.next_amb_num = 4
    if "voice_tick" not in st.session_state:
        st.session_state.voice_tick = 0
    if "hitl_acks" not in st.session_state:
        st.session_state.hitl_acks = {}
    if "hospital_resources" not in st.session_state:
        st.session_state.hospital_resources = {
            "icu_beds": {"total": 12, "available": 8},
            "ct_scanner": {"total": 2, "available": 1},
            "mri_scanner": {"total": 1, "available": 1},
            "or_rooms": {"total": 6, "available": 4},
            "blood_units_o_neg": {"available": 25},
            "blood_units_o_pos": {"available": 30},
            "ventilators": {"total": 15, "available": 10},
        }

    patients_data = [
        ("P-2024-001", "AMB-001", 58, "Female", "Chest Pain", "critical", "mi_patient", 8),
        ("P-2024-002", "AMB-002", 72, "Male", "Stroke Symptoms", "critical", "mi_patient", 10),
        ("P-2024-003", "AMB-003", 45, "Male", "Trauma - MVA", "deteriorating", "trauma", 6),
    ]
    for pid, amb_id, age, gender, complaint, condition, scenario, initial_eta in patients_data:
        if pid not in st.session_state.patients:
            st.session_state.patients[pid] = _new_patient_record(
                pid, amb_id, age, gender, complaint, condition, scenario, initial_eta
            )


def _new_patient_record(pid, amb_id, age, gender, complaint, condition, scenario, initial_eta):
    return {
        "patient_id": pid,
        "ambulance_id": amb_id,
        "patient_info": {
            "age": age,
            "gender": gender,
            "chief_complaint": complaint,
            "scenario": scenario,
            "allergies": ["NKDA"],
            "medications": ["Aspirin 81mg", "Lisinopril 10mg"] if pid == "P-2024-001" else [],
        },
        "telemetry_history": [],
        "voice_notes": [],
        "telemetry_sim": TelemetrySimulator(patient_condition=condition),
        "voice_sim": EMTVoiceSimulator(scenario=scenario),
        "clinical_scores": {},
        "severity": {},
        "predictions": {},
        "active_alerts": [],
        "activated_protocols": {},
        "initial_eta": initial_eta,
        "elapsed_time": 0,
        "status": "EN_ROUTE",
        "handoff_summary": None,
        "ems_treatments": None,
        "last_voice_index": -1,
        "consensus": None,
    }


def add_new_ambulance():
    import random

    scenarios = [
        ("Chest Pain - Possible MI", "critical", "mi_patient"),
        ("Stroke Symptoms", "critical", "mi_patient"),
        ("Trauma - MVA", "deteriorating", "trauma"),
        ("Sepsis Suspected", "critical", "mi_patient"),
        ("Respiratory Distress", "deteriorating", "mi_patient"),
    ]
    complaint, condition, scenario = random.choice(scenarios)
    pid = f"P-2024-{st.session_state.next_patient_num:03d}"
    amb_id = f"AMB-{st.session_state.next_amb_num:03d}"
    st.session_state.patients[pid] = _new_patient_record(
        pid, amb_id, random.randint(35, 85), random.choice(["Male", "Female"]),
        complaint, condition, scenario, random.randint(5, 12),
    )
    st.session_state.next_patient_num += 1
    st.session_state.next_amb_num += 1
    st.session_state.selected_patient = pid


def display_ambulance_selector():
    st.sidebar.markdown("### Fleet")
    if st.sidebar.button("Register incoming unit", use_container_width=True, type="primary"):
        add_new_ambulance()
        st.rerun()

    en_route = sum(1 for p in st.session_state.patients.values() if p["status"] == "EN_ROUTE")
    arrived = sum(1 for p in st.session_state.patients.values() if p["status"] == "ARRIVED")
    hitl_pending = sum(
        1 for p in st.session_state.patients.values()
        if p.get("consensus", {}) and p["consensus"].get("requires_hitl")
        and p["consensus"].get("resolution_mode") != "CLINICIAN_CONFIRMED"
    )
    st.sidebar.markdown(f"**En route:** {en_route}  ·  **Arrived:** {arrived}")
    if hitl_pending:
        st.sidebar.warning(f"**{hitl_pending}** need clinician review")

    for patient_id, patient_data in st.session_state.patients.items():
        eta = max(0, patient_data["initial_eta"] - patient_data["elapsed_time"] // 3)
        level = patient_data.get("severity", {}).get("level", "UNKNOWN")
        selected = patient_id == st.session_state.selected_patient
        with st.sidebar.container():
            st.sidebar.html(
                sidebar_fleet_hint(
                    patient_id, patient_data["ambulance_id"], eta, level,
                    patient_data["status"], selected,
                )
            )
            if st.sidebar.button(
                "View",
                key=f"select_{patient_id}",
                use_container_width=True,
                type="primary" if selected else "secondary",
            ):
                st.session_state.selected_patient = patient_id


def display_hospital_resources():
    st.sidebar.markdown("### Hospital capacity")
    r = st.session_state.hospital_resources
    html = "".join([
        resource_bar("ICU beds", r["icu_beds"]["available"], r["icu_beds"]["total"]),
        resource_bar("CT scanner", r["ct_scanner"]["available"], r["ct_scanner"]["total"]),
        resource_bar("MRI", r["mri_scanner"]["available"], r["mri_scanner"]["total"]),
        resource_bar("OR rooms", r["or_rooms"]["available"], r["or_rooms"]["total"]),
        resource_bar("Ventilators", r["ventilators"]["available"], r["ventilators"]["total"]),
        resource_bar("O− blood units", r["blood_units_o_neg"]["available"]),
        resource_bar("O+ blood units", r["blood_units_o_pos"]["available"]),
    ])
    st.sidebar.html(html)


def maybe_append_voice_note(patient_data):
    if patient_data["status"] != "EN_ROUTE":
        return
    st.session_state.voice_tick += 1
    if st.session_state.voice_tick % 4 != 0:
        return
    note = patient_data["voice_sim"].generate_voice_note()
    idx = patient_data["voice_sim"].current_note_index - 1
    if idx <= patient_data["last_voice_index"]:
        return
    patient_data["last_voice_index"] = idx
    redacted = st.session_state.aparavi_redactor.redact_text(note["voice_note"])
    patient_data["voice_notes"].append({
        "timestamp": note["timestamp"],
        "redacted": redacted,
        "eta_minutes": note.get("eta_minutes"),
    })
    if len(patient_data["voice_notes"]) > 8:
        patient_data["voice_notes"] = patient_data["voice_notes"][-8:]


def calculate_clinical_scores(patient_data):
    scorer = st.session_state.scorer
    if not patient_data["telemetry_history"]:
        return
    latest_vitals = patient_data["telemetry_history"][-1].copy()
    latest_vitals["gcs"] = 13
    latest_vitals["respiratory_rate"] = 24
    latest_vitals["temperature"] = 37.8
    complaint = patient_data["patient_info"]["chief_complaint"]
    symptoms = {
        "chest_pain": complaint == "Chest Pain",
        "st_elevation": complaint == "Chest Pain",
        "diaphoresis": True,
        "nausea": True,
        "stroke_suspected": "Stroke" in complaint,
        "airway_obstruction": False,
    }
    scores = {
        "trauma_score": scorer.calculate_trauma_score(latest_vitals),
        "qsofa": scorer.calculate_qsofa(latest_vitals),
        "stemi_checklist": scorer.calculate_stemi_checklist(symptoms),
        "shock_index": scorer.calculate_shock_index(latest_vitals),
        "airway_risk": scorer.calculate_airway_risk(latest_vitals, symptoms),
        "nihss": scorer.calculate_nihss(symptoms),
        "deterioration": scorer.calculate_deterioration_index(patient_data["telemetry_history"]),
    }
    patient_data["clinical_scores"] = scores
    predictor = st.session_state.predictor
    patient_data["severity"] = predictor.predict_severity(latest_vitals, symptoms, scores)
    patient_data["active_alerts"] = predictor.predict_active_alerts(latest_vitals, symptoms, scores)
    patient_data["predictions"] = predictor.predict_interventions(latest_vitals, symptoms, scores)
    patient_data["activated_protocols"] = predictor.activate_protocols(
        patient_data["active_alerts"], patient_data["predictions"]["predictions"],
    )
    run_consensus(patient_data)


def run_consensus(patient_data):
    """Multi-agent consensus + HITL gate after triage agents finish."""
    if not patient_data.get("severity"):
        patient_data["consensus"] = None
        return
    ack = st.session_state.hitl_acks.get(patient_data["patient_id"])
    patient_data["consensus"] = ConsensusEngine.reconcile(
        patient_id=patient_data["patient_id"],
        chief_complaint=patient_data["patient_info"]["chief_complaint"],
        severity=patient_data["severity"],
        alerts=patient_data.get("active_alerts", []),
        predictions=patient_data.get("predictions", {}),
        protocols=patient_data.get("activated_protocols", {}),
        scores=patient_data.get("clinical_scores", {}),
        clinician_ack=ack,
    )


def effective_severity(patient_data) -> dict:
    """Severity shown in UI — consensus final_severity when present."""
    consensus = patient_data.get("consensus") or {}
    return consensus.get("final_severity") or patient_data.get("severity", {})


def display_consensus_panel(patient_data):
    """Multi-agent consensus status, conflicts, and reasoning trace."""
    consensus = patient_data.get("consensus")
    if not consensus:
        return

    section_title("Multi-agent consensus")
    mode = consensus.get("resolution_mode", "AUTO")
    mode_labels = {
        "AUTO": ("✅ Auto-resolved", "success"),
        "SEVERITY_OVERRIDE": ("⚡ Severity override + review required", "warning"),
        "HITL_PENDING": ("👤 Clinician review required", "error"),
        "CLINICIAN_CONFIRMED": ("✔️ Clinician confirmed", "success"),
    }
    label, kind = mode_labels.get(mode, (mode, "info"))
    if kind == "success":
        st.success(label)
    elif kind == "warning":
        st.warning(label)
    elif kind == "error":
        st.error(label)
    else:
        st.info(label)

    agents = consensus.get("agents", {})
    ac1, ac2, ac3 = st.columns(3)
    with ac1:
        d = agents.get("diagnostic", {})
        st.markdown("**Diagnostic agent**")
        st.caption(f"Pathway: **{d.get('primary_pathway', '—')}**")
        st.caption(f"Confidence: {int(d.get('confidence', 0) * 100)}%")
        st.caption(d.get("rationale", ""))
    with ac2:
        s = agents.get("severity", {})
        st.markdown("**Severity agent**")
        st.caption(f"**{s.get('level', '—')}** · {s.get('score', 0)}/100")
    with ac3:
        p = agents.get("protocol", {})
        st.markdown("**Protocol agent**")
        st.caption(f"{p.get('protocol_count', 0)} protocol(s) active")

    conflicts = consensus.get("conflicts", [])
    if conflicts:
        st.markdown("**Detected conflicts**")
        for c in conflicts:
            sev_icon = "🔴" if c.get("severity") == "high" else "🟡"
            st.markdown(
                f"{sev_icon} **{c.get('type', 'CONFLICT')}** — {c.get('message', '')}  \n"
                f"_Agents: {', '.join(c.get('agents', []))}_"
            )

    with st.expander("Reasoning trace (audit log)", expanded=consensus.get("requires_hitl", False)):
        for step in consensus.get("reasoning_trace", []):
            st.markdown(f"`{step.get('time', '')}` **{step.get('step', '')}** — {step.get('detail', '')}")


def display_hitl_review(patient_data):
    """Human-in-the-loop controls when agents disagree."""
    consensus = patient_data.get("consensus")
    if not consensus or not consensus.get("requires_hitl"):
        return
    if consensus.get("resolution_mode") == "CLINICIAN_CONFIRMED":
        return

    pid = patient_data["patient_id"]
    st.error("**Human-in-the-loop review required** — agents produced conflicting outputs. "
             "Confirm how the ED should proceed; the system will not auto-resolve silently.")

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Confirm severity-led plan", key=f"hitl_sev_{pid}", use_container_width=True):
            st.session_state.hitl_acks[pid] = {
                "choice": "severity",
                "role": "ED clinician",
                "at": datetime.now().isoformat(),
            }
            st.rerun()
    with c2:
        if st.button("Confirm diagnostic-led plan", key=f"hitl_dx_{pid}", use_container_width=True):
            st.session_state.hitl_acks[pid] = {
                "choice": "diagnostic",
                "role": "ED clinician",
                "at": datetime.now().isoformat(),
            }
            st.rerun()
    with c3:
        if st.button("Escalate to attending", key=f"hitl_att_{pid}", use_container_width=True):
            st.session_state.hitl_acks[pid] = {
                "choice": "diagnostic",
                "role": "Attending physician",
                "at": datetime.now().isoformat(),
            }
            st.rerun()


def ensure_ems_treatments(patient_data):
    if patient_data.get("ems_treatments"):
        return
    complaint = patient_data["patient_info"]["chief_complaint"]
    if "Chest Pain" in complaint:
        patient_data["ems_treatments"] = {
            "medications": [
                {"name": "Aspirin", "dose": "325mg PO", "time": "On scene"},
                {"name": "Nitroglycerin", "dose": "0.4mg SL ×2", "time": "5 min ago"},
                {"name": "Morphine", "dose": "4mg IV", "time": "3 min ago"},
            ],
            "interventions": [
                {"name": "Oxygen", "details": "4 L/min nasal cannula"},
                {"name": "IV access", "details": "18G right AC"},
                {"name": "12-lead ECG", "details": "ST elevations noted"},
                {"name": "Cardiac monitor", "details": "Continuous telemetry"},
            ],
            "cpr": False, "defibrillation": False, "iv_fluids": "250 mL NS",
        }
    elif "Stroke" in complaint:
        patient_data["ems_treatments"] = {
            "medications": [],
            "interventions": [
                {"name": "Oxygen", "details": "2 L/min nasal cannula"},
                {"name": "IV access", "details": "20G left hand"},
                {"name": "Blood glucose", "details": "112 mg/dL"},
                {"name": "FAST assessment", "details": "Positive — left-sided weakness"},
            ],
            "cpr": False, "defibrillation": False, "iv_fluids": "NS @ KVO",
        }
    elif "Trauma" in complaint:
        patient_data["ems_treatments"] = {
            "medications": [{"name": "Fentanyl", "dose": "50 mcg IV", "time": "2 min ago"}],
            "interventions": [
                {"name": "C-spine immobilization", "details": "Collar + backboard"},
                {"name": "IV access", "details": "Two 16G bilateral AC"},
                {"name": "Oxygen", "details": "15 L NRB mask"},
                {"name": "Hemorrhage control", "details": "Pressure dressing — left leg"},
            ],
            "cpr": False, "defibrillation": False, "iv_fluids": "1000 mL NS rapid infusion",
        }
    else:
        patient_data["ems_treatments"] = {
            "medications": [],
            "interventions": [
                {"name": "Oxygen", "details": "2–4 L/min nasal cannula"},
                {"name": "IV access", "details": "18G established"},
            ],
            "cpr": False, "defibrillation": False, "iv_fluids": "NS @ 100 mL/hr",
        }


def build_vitals_chart(patient_data):
    if not patient_data["telemetry_history"]:
        return None
    df = pd.DataFrame(patient_data["telemetry_history"])
    fig = make_subplots(
        rows=3, cols=1,
        subplot_titles=("Heart rate (bpm)", "SpO₂ (%)", "Systolic BP (mmHg)"),
        vertical_spacing=0.08,
    )
    fig.add_trace(
        go.Scatter(x=df.index, y=df["heart_rate"], line=dict(color="#DC2626", width=2.5),
                   fill="tozeroy", fillcolor="rgba(220,38,38,0.08)"), row=1, col=1,
    )
    fig.add_trace(
        go.Scatter(x=df.index, y=df["spo2"], line=dict(color="#0E7490", width=2.5),
                   fill="tozeroy", fillcolor="rgba(14,116,144,0.08)"), row=2, col=1,
    )
    fig.add_hrect(y0=92, y1=100, line_width=0, fillcolor="rgba(5,150,105,0.12)", row=2, col=1)
    fig.add_trace(
        go.Scatter(x=df.index, y=df["blood_pressure_systolic"], line=dict(color="#155E75", width=2.5),
                   fill="tozeroy", fillcolor="rgba(21,94,117,0.08)"), row=3, col=1,
    )
    fig.update_layout(height=480, showlegend=False)
    apply_plotly_theme(fig)
    return fig


def display_live_vitals(vitals):
    c1, c2, c3 = st.columns(3)
    hr = vitals["heart_rate"]
    spo2 = vitals["spo2"]
    with c1:
        st.metric("Heart rate", f"{hr} bpm", delta="Tachycardia" if hr > 120 else None)
    with c2:
        st.metric("SpO₂", f"{spo2}%", delta="Low" if spo2 < 94 else None)
    with c3:
        st.metric("Blood pressure", vitals["blood_pressure"])


def display_eta_severity(eta, status, severity):
    with st.container(border=True):
        if status == "ARRIVED":
            st.metric("Status", "Arrived")
        else:
            st.metric("ETA to ED", f"{eta} min")
        st.metric(
            "AI severity",
            f"{severity.get('score', 0)}/100",
            delta=severity.get("level", "—"),
        )


def display_clinical_scores(patient_data):
    scores = patient_data.get("clinical_scores", {})
    if not scores:
        st.info("Calculating clinical scores…")
        return
    severity = effective_severity(patient_data)
    row1 = st.columns(4)
    metrics_r1 = [
        ("AI severity", f"{severity.get('score', 0)}/100", severity.get("level", "")),
        ("Shock index", str(scores["shock_index"]["value"]), scores["shock_index"]["interpretation"]),
        ("STEMI score", str(scores["stemi_checklist"]["score"]), scores["stemi_checklist"]["interpretation"]),
        ("qSOFA", f"{scores['qsofa']['score']}/3", scores["qsofa"]["interpretation"]),
    ]
    for col, (label, val, delta) in zip(row1, metrics_r1):
        with col:
            st.metric(label, val, delta=delta if delta else None)

    row2 = st.columns(4)
    metrics_r2 = [
        ("Trauma (RTS)", str(scores["trauma_score"]["score"]), scores["trauma_score"]["interpretation"]),
        ("NIHSS", f"{scores['nihss']['score']}/42", scores["nihss"]["interpretation"]),
        ("Airway risk", str(scores["airway_risk"]["score"]), scores["airway_risk"]["interpretation"]),
        ("Deterioration", str(scores["deterioration"]["score"]), scores["deterioration"]["interpretation"]),
    ]
    for col, (label, val, delta) in zip(row2, metrics_r2):
        with col:
            st.metric(label, val, delta=delta if delta else None)


def display_alerts(alerts):
    if not alerts:
        return
    section_title("Active clinical alerts")
    cols = st.columns(min(len(alerts), 4))
    for i, alert in enumerate(alerts):
        meta = ALERT_STYLES.get(alert, {"title": alert, "sub": ""})
        with cols[i % len(cols)]:
            if alert in ("STEMI", "CARDIAC_ARREST_RISK"):
                st.error(f"**{meta['title']}**\n\n{meta['sub']}")
            elif alert == "SEPSIS":
                st.warning(f"**{meta['title']}**\n\n{meta['sub']}")
            else:
                st.warning(f"**{meta['title']}**\n\n{meta['sub']}")


def display_protocols(protocols):
    if not protocols:
        st.caption("No protocols activated.")
        return
    for name, actions in protocols.items():
        with st.expander(name.replace("_", " ").title(), expanded=True):
            for action in actions:
                st.markdown(f"- {action}")


def display_predictions(predictions, confidence):
    labels = {
        "cardiac_arrest_imminent": ("Cardiac arrest risk", "cardiac_arrest"),
        "needs_intubation": ("Intubation likely", "intubation"),
        "needs_icu": ("ICU admission", "icu"),
        "needs_or": ("OR required", "or"),
        "likely_stroke": ("Stroke pathway", "stroke"),
        "likely_stemi": ("STEMI pathway", "stemi"),
        "likely_sepsis": ("Sepsis pathway", "sepsis"),
    }
    active = [(labels[k][0], confidence.get(labels[k][1], 0.75)) for k, v in predictions.items() if v]
    if not active:
        st.caption("No high-confidence interventions predicted.")
        return
    cols = st.columns(min(3, len(active)))
    for i, (name, conf) in enumerate(active):
        with cols[i % len(cols)]:
            st.info(f"**{name}** · {int(conf * 100)}% confidence")


def display_ems_treatments(patient_data, info):
    t = patient_data["ems_treatments"]
    mcol, icol = st.columns(2)
    with mcol:
        st.markdown("**Medications**")
        if t["medications"]:
            for m in t["medications"]:
                st.success(f"**{m['name']}** — {m['dose']} ({m['time']})")
        else:
            st.caption("None documented")
    with icol:
        st.markdown("**Interventions**")
        for i in t["interventions"]:
            st.info(f"**{i['name']}** — {i['details']}")
    c1, c2, c3 = st.columns(3)
    c1.metric("CPR", "Performed" if t["cpr"] else "Not required")
    c2.metric("Defibrillation", "Given" if t["defibrillation"] else "Not required")
    c3.metric("IV fluids", t["iv_fluids"])
    st.caption(
        f"Allergies: {', '.join(info['allergies'])} · "
        f"Home meds: {', '.join(info['medications']) if info['medications'] else 'None listed'}"
    )


def display_voice_feed(patient_data):
    notes = patient_data.get("voice_notes", [])
    if not notes:
        st.caption("Awaiting EMT field updates…")
        return
    for n in reversed(notes[-5:]):
        ts = n["timestamp"][:19].replace("T", " ")
        with st.container(border=True):
            st.caption(f"{ts} · ETA {n.get('eta_minutes', '?')} min · PHI redacted")
            st.write(n["redacted"])


def update_hospital_resources(patient_data):
    resources = st.session_state.hospital_resources
    predictions = patient_data.get("predictions", {}).get("predictions", {})
    if predictions.get("needs_icu") and resources["icu_beds"]["available"] > 0:
        resources["icu_beds"]["available"] -= 1
    if predictions.get("needs_intubation") and resources["ventilators"]["available"] > 0:
        resources["ventilators"]["available"] -= 1
    if predictions.get("needs_or") and resources["or_rooms"]["available"] > 0:
        resources["or_rooms"]["available"] -= 1
    active_alerts = patient_data.get("active_alerts", [])
    if ("STROKE" in active_alerts or "TRAUMA" in active_alerts) and resources["ct_scanner"]["available"] > 0:
        resources["ct_scanner"]["available"] -= 1
    if "TRAUMA" in active_alerts and resources["blood_units_o_neg"]["available"] >= 2:
        resources["blood_units_o_neg"]["available"] -= 2


def main():
    initialize_session_state()
    display_ambulance_selector()
    display_hospital_resources()

    st.sidebar.markdown("---")
    st.sidebar.markdown("### System")
    st.sidebar.success("AI scoring active")
    st.sidebar.success("Consensus layer active")
    st.sidebar.success("Aparavi PII shield")

    en_route = sum(1 for p in st.session_state.patients.values() if p["status"] == "EN_ROUTE")
    show_html(brand_header(len(st.session_state.patients), en_route, datetime.now().strftime("%H:%M:%S")))

    patient_id = st.session_state.selected_patient
    patient_data = st.session_state.patients[patient_id]

    if patient_data["status"] == "EN_ROUTE":
        patient_data["telemetry_history"].append(patient_data["telemetry_sim"].generate_vitals())
        patient_data["elapsed_time"] += 1
        if len(patient_data["telemetry_history"]) > 20:
            patient_data["telemetry_history"] = patient_data["telemetry_history"][-20:]
        maybe_append_voice_note(patient_data)
        eta = max(0, patient_data["initial_eta"] - patient_data["elapsed_time"] // 3)
        if eta == 0:
            patient_data["status"] = "ARRIVED"
            patient_data["handoff_summary"] = st.session_state.predictor.generate_handoff_summary(patient_data)
            update_hospital_resources(patient_data)

    calculate_clinical_scores(patient_data)
    ensure_ems_treatments(patient_data)

    severity = effective_severity(patient_data)
    status = patient_data["status"]
    eta = max(0, patient_data["initial_eta"] - patient_data["elapsed_time"] // 3)
    info = patient_data["patient_info"]

    display_hitl_review(patient_data)
    display_consensus_panel(patient_data)

    col_hero, col_eta = st.columns([3, 1])
    with col_hero:
        show_html(patient_hero(
            patient_data["patient_id"], patient_data["ambulance_id"],
            info["age"], info["gender"], info["chief_complaint"],
            status, eta, severity.get("level", "UNKNOWN"),
        ))
    with col_eta:
        display_eta_severity(eta, status, severity)

    if patient_data["telemetry_history"]:
        display_live_vitals(patient_data["telemetry_history"][-1])

    display_alerts(patient_data.get("active_alerts", []))

    if status == "ARRIVED" and patient_data.get("handoff_summary"):
        section_title("ED handoff summary")
        show_html(handoff_html(patient_data["handoff_summary"]))

    section_title("Clinical intelligence")
    display_clinical_scores(patient_data)

    tab_clinical, tab_ems, tab_feed = st.tabs(["Protocols & AI", "Pre-hospital care", "EMS comms (redacted)"])
    with tab_clinical:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Activated protocols**")
            display_protocols(patient_data.get("activated_protocols", {}))
        with c2:
            st.markdown("**AI intervention forecast**")
            preds = patient_data.get("predictions", {}).get("predictions", {})
            conf = patient_data.get("predictions", {}).get("confidence_scores", {})
            display_predictions(preds, conf)
    with tab_ems:
        display_ems_treatments(patient_data, info)
    with tab_feed:
        st.caption("PHI redacted in transit via Aparavi before display in the ED.")
        display_voice_feed(patient_data)

    section_title("Vital trends")
    fig = build_vitals_chart(patient_data)
    if fig:
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Collecting telemetry from ambulance monitor…")

    st.caption(
        f"Golden Bridge Pre-Arrival System · {len(st.session_state.patients)} units · "
        f"Auto-refresh 2s"
    )
    time.sleep(2)
    st.rerun()


if __name__ == "__main__":
    main()
