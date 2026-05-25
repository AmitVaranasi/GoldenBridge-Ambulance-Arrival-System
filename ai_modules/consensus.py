"""
Multi-agent consensus layer for Golden Bridge triage.

Models three logical agents whose outputs may conflict:
  - DiagnosticAgent: primary clinical pathway from alerts + predictions
  - SeverityAgent: acuity score and level
  - ProtocolAgent: activated hospital protocols

Resolution policy (healthcare-safe):
  - Severity agent may override for CRITICAL / EMERGENT cases
  - Unresolved diagnostic vs severity conflicts → human-in-the-loop (HITL)
  - Full reasoning trace for audit transparency
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

# Minimum severity implied by a primary pathway (score, level)
_PATHWAY_SEVERITY_FLOOR = {
    "STEMI": (50, "EMERGENT"),
    "STROKE": (50, "EMERGENT"),
    "TRAUMA": (50, "EMERGENT"),
    "SEPSIS": (50, "EMERGENT"),
    "CARDIAC_ARREST_RISK": (75, "CRITICAL"),
    "GENERAL": (0, "NON-EMERGENT"),
}

_LEVEL_RANK = {
    "NON-EMERGENT": 0,
    "URGENT": 1,
    "EMERGENT": 2,
    "CRITICAL": 3,
}


def _level_from_score(score: int) -> str:
    if score >= 75:
        return "CRITICAL"
    if score >= 50:
        return "EMERGENT"
    if score >= 25:
        return "URGENT"
    return "NON-EMERGENT"


def _max_level(a: str, b: str) -> str:
    return a if _LEVEL_RANK[a] >= _LEVEL_RANK[b] else b


class DiagnosticAgent:
    """Infers primary clinical pathway from alerts, predictions, and presentation."""

    @staticmethod
    def analyze(
        alerts: List[str],
        predictions: Dict[str, bool],
        chief_complaint: str,
        scores: Dict[str, Any],
    ) -> Dict[str, Any]:
        candidates: List[Tuple[str, float, str]] = []

        if "STEMI" in alerts or predictions.get("likely_stemi"):
            conf = 0.9 if "STEMI" in alerts else 0.75
            candidates.append(("STEMI", conf, "STEMI alert / ACS prediction"))
        if "STROKE" in alerts or predictions.get("likely_stroke"):
            conf = 0.85 if "STROKE" in alerts else 0.7
            candidates.append(("STROKE", conf, "Stroke alert / NIHSS"))
        if "TRAUMA" in alerts:
            candidates.append(("TRAUMA", 0.8, "Trauma team criteria"))
        if "SEPSIS" in alerts or predictions.get("likely_sepsis"):
            conf = 0.75 if "SEPSIS" in alerts else 0.65
            candidates.append(("SEPSIS", conf, "qSOFA / sepsis prediction"))
        if "CARDIAC_ARREST_RISK" in alerts or predictions.get("cardiac_arrest_imminent"):
            candidates.append(("CARDIAC_ARREST_RISK", 0.85, "Arrest risk criteria"))

        if not candidates:
            return {
                "agent": "DiagnosticAgent",
                "primary_pathway": "GENERAL",
                "confidence": 0.5,
                "rationale": "No single high-acuity pathway flagged",
                "alternate_pathways": [],
            }

        candidates.sort(key=lambda x: x[1], reverse=True)
        primary, conf, rationale = candidates[0]
        alternates = [
            {"pathway": p, "confidence": c, "note": n}
            for p, c, n in candidates[1:]
            if c >= 0.65
        ]

        # Complaint vs pathway mismatch hints
        complaint_notes = []
        if primary == "STROKE" and "Stroke" not in chief_complaint and "stroke" not in chief_complaint.lower():
            complaint_notes.append("Primary stroke pathway despite non-stroke chief complaint")
        if primary == "STEMI" and "Chest" not in chief_complaint and "pain" not in chief_complaint.lower():
            complaint_notes.append("STEMI pathway without chest-pain presentation")

        return {
            "agent": "DiagnosticAgent",
            "primary_pathway": primary,
            "confidence": conf,
            "rationale": rationale,
            "alternate_pathways": alternates,
            "complaint_flags": complaint_notes,
        }


class SeverityAgent:
    """Wraps triage severity output."""

    @staticmethod
    def analyze(severity: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "agent": "SeverityAgent",
            "score": severity.get("score", 0),
            "level": severity.get("level", "UNKNOWN"),
            "priority": severity.get("priority", ""),
            "contributing_factors": severity.get("contributing_factors", []),
        }


class ProtocolAgent:
    """Wraps activated protocol list."""

    @staticmethod
    def analyze(protocols: Dict[str, List[str]], alerts: List[str]) -> Dict[str, Any]:
        expected = set()
        if "STEMI" in alerts:
            expected.add("STEMI_PROTOCOL")
        if "STROKE" in alerts:
            expected.add("STROKE_PROTOCOL")
        if "TRAUMA" in alerts:
            expected.add("TRAUMA_PROTOCOL")
        if "SEPSIS" in alerts:
            expected.add("SEPSIS_PROTOCOL")

        activated = set(protocols.keys())
        missing = expected - activated
        extra = activated - expected

        return {
            "agent": "ProtocolAgent",
            "activated_protocols": list(protocols.keys()),
            "protocol_count": len(protocols),
            "missing_expected": list(missing),
            "unexpected": list(extra),
        }


class ConsensusEngine:
    """
    Reconciles multi-agent outputs and decides AUTO vs override vs HITL.
    """

    @staticmethod
    def detect_conflicts(
        diagnostic: Dict[str, Any],
        severity: Dict[str, Any],
        protocol: Dict[str, Any],
        alerts: List[str],
        predictions: Dict[str, bool],
    ) -> List[Dict[str, Any]]:
        conflicts: List[Dict[str, Any]] = []
        sev_level = severity.get("level", "UNKNOWN")
        sev_score = severity.get("score", 0)
        pathway = diagnostic.get("primary_pathway", "GENERAL")
        floor_score, floor_level = _PATHWAY_SEVERITY_FLOOR.get(pathway, (0, "NON-EMERGENT"))

        # Diagnostic pathway implies higher acuity than severity agent reported
        if pathway != "GENERAL" and _LEVEL_RANK.get(sev_level, 0) < _LEVEL_RANK.get(floor_level, 0):
            conflicts.append({
                "id": "severity_below_pathway",
                "type": "DIAGNOSTIC_VS_SEVERITY",
                "message": (
                    f"Diagnostic agent prioritizes {pathway} "
                    f"(expects >={floor_level}), but severity agent rated {sev_level} ({sev_score}/100)."
                ),
                "agents": ["DiagnosticAgent", "SeverityAgent"],
                "severity": "high",
            })

        # Active alert not reflected in severity (e.g. STEMI + low score)
        if "STEMI" in alerts and sev_score < 50:
            conflicts.append({
                "id": "stemi_low_severity",
                "type": "ALERT_VS_SEVERITY",
                "message": "STEMI alert active while severity score is below emergent threshold.",
                "agents": ["DiagnosticAgent", "SeverityAgent"],
                "severity": "high",
            })

        if "STROKE" in alerts and not predictions.get("likely_stroke") and sev_score < 50:
            conflicts.append({
                "id": "stroke_prediction_split",
                "type": "ALERT_VS_PREDICTION",
                "message": "Stroke alert fired but stroke prediction confidence path disagrees or severity is low.",
                "agents": ["DiagnosticAgent", "SeverityAgent"],
                "severity": "medium",
            })

        # Competing high-acuity pathways
        alts = diagnostic.get("alternate_pathways", [])
        if alts and diagnostic.get("confidence", 0) >= 0.7:
            alt_path = alts[0].get("pathway")
            if alt_path != pathway:
                conflicts.append({
                    "id": "competing_pathways",
                    "type": "DIAGNOSTIC_INTERNAL",
                    "message": f"Competing pathways: {pathway} vs {alt_path} — both above confidence threshold.",
                    "agents": ["DiagnosticAgent"],
                    "severity": "medium",
                })

        # Protocol agent out of sync with alerts
        if protocol.get("missing_expected"):
            conflicts.append({
                "id": "protocol_gap",
                "type": "PROTOCOL_VS_ALERT",
                "message": f"Protocol agent missing expected activations: {protocol['missing_expected']}.",
                "agents": ["ProtocolAgent", "DiagnosticAgent"],
                "severity": "medium",
            })

        if diagnostic.get("complaint_flags"):
            for note in diagnostic["complaint_flags"]:
                conflicts.append({
                    "id": "complaint_mismatch",
                    "type": "DIAGNOSTIC_VS_PRESENTATION",
                    "message": note,
                    "agents": ["DiagnosticAgent"],
                    "severity": "medium",
                })

        return conflicts

    @staticmethod
    def reconcile(
        patient_id: str,
        chief_complaint: str,
        severity: Dict[str, Any],
        alerts: List[str],
        predictions: Dict[str, Any],
        protocols: Dict[str, List[str]],
        scores: Dict[str, Any],
        clinician_ack: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Run consensus and return unified decision package + reasoning trace.
        """
        preds = predictions.get("predictions", predictions)
        diagnostic = DiagnosticAgent.analyze(alerts, preds, chief_complaint, scores)
        sev_agent = SeverityAgent.analyze(severity)
        proto_agent = ProtocolAgent.analyze(protocols, alerts)

        conflicts = ConsensusEngine.detect_conflicts(
            diagnostic, sev_agent, proto_agent, alerts, preds
        )

        trace: List[Dict[str, str]] = []
        ts = datetime.now().strftime("%H:%M:%S")
        trace.append({
            "time": ts,
            "step": "DiagnosticAgent",
            "detail": f"Primary pathway: {diagnostic['primary_pathway']} ({int(diagnostic['confidence']*100)}% confidence)",
        })
        trace.append({
            "time": ts,
            "step": "SeverityAgent",
            "detail": f"Acuity: {sev_agent['level']} — score {sev_agent['score']}/100",
        })
        trace.append({
            "time": ts,
            "step": "ProtocolAgent",
            "detail": f"Activated {proto_agent['protocol_count']} protocol(s): {', '.join(proto_agent['activated_protocols']) or 'none'}",
        })

        high_conflicts = [c for c in conflicts if c.get("severity") == "high"]
        requires_hitl = len(high_conflicts) > 0 or len(conflicts) >= 2

        final_severity = dict(severity)
        resolution_mode = "AUTO"
        override_applied = False

        if clinician_ack:
            resolution_mode = "CLINICIAN_CONFIRMED"
            requires_hitl = False
            choice = clinician_ack.get("choice", "severity")
            if choice == "diagnostic":
                pathway = diagnostic["primary_pathway"]
                floor_score, floor_level = _PATHWAY_SEVERITY_FLOOR.get(pathway, (50, "EMERGENT"))
                final_severity["score"] = max(final_severity.get("score", 0), floor_score)
                final_severity["level"] = _max_level(final_severity.get("level", "URGENT"), floor_level)
            trace.append({
                "time": datetime.now().strftime("%H:%M:%S"),
                "step": "ClinicianReview",
                "detail": f"Confirmed by {clinician_ack.get('role', 'ED clinician')}: followed {choice}-led resolution.",
            })
        elif conflicts:
            sev_level = sev_agent["level"]
            can_override = sev_level in ("CRITICAL", "EMERGENT")

            if can_override and high_conflicts:
                pathway = diagnostic["primary_pathway"]
                floor_score, floor_level = _PATHWAY_SEVERITY_FLOOR.get(pathway, (50, "EMERGENT"))
                new_score = max(sev_agent["score"], floor_score)
                new_level = _max_level(sev_level, _level_from_score(new_score))
                new_level = _max_level(new_level, floor_level)

                final_severity["score"] = new_score
                final_severity["level"] = new_level
                override_applied = True
                resolution_mode = "SEVERITY_OVERRIDE"
                requires_hitl = True  # still need human sign-off when diagnostic disagrees

                trace.append({
                    "time": datetime.now().strftime("%H:%M:%S"),
                    "step": "ConsensusLayer",
                    "detail": (
                        f"Severity override applied ({sev_level} → {new_level}) for critical case; "
                        "HITL required because diagnostic agent still disagrees."
                    ),
                })
            else:
                resolution_mode = "HITL_PENDING"
                requires_hitl = True
                trace.append({
                    "time": datetime.now().strftime("%H:%M:%S"),
                    "step": "ConsensusLayer",
                    "detail": f"{len(conflicts)} conflict(s) detected — escalated to human-in-the-loop review.",
                })
        else:
            trace.append({
                "time": datetime.now().strftime("%H:%M:%S"),
                "step": "ConsensusLayer",
                "detail": "All agents aligned — auto-resolved without override.",
            })

        return {
            "patient_id": patient_id,
            "resolution_mode": resolution_mode,
            "requires_hitl": requires_hitl,
            "override_applied": override_applied,
            "conflicts": conflicts,
            "conflict_count": len(conflicts),
            "agents": {
                "diagnostic": diagnostic,
                "severity": sev_agent,
                "protocol": proto_agent,
            },
            "final_severity": final_severity,
            "reasoning_trace": trace,
            "evaluated_at": datetime.now().isoformat(),
        }


if __name__ == "__main__":
    sample_severity = {"score": 35, "level": "URGENT", "priority": "Within 30 min", "contributing_factors": []}
    sample_alerts = ["STEMI"]
    sample_preds = {
        "predictions": {"likely_stemi": True, "likely_stroke": False, "likely_sepsis": False},
        "confidence_scores": {"stemi": 0.9},
    }
    sample_protocols = {"STEMI_PROTOCOL": ["Activate cath lab"]}

    result = ConsensusEngine.reconcile(
        "P-TEST",
        "Chest Pain",
        sample_severity,
        sample_alerts,
        sample_preds,
        sample_protocols,
        {},
    )
    print("Mode:", result["resolution_mode"])
    print("HITL:", result["requires_hitl"])
    for c in result["conflicts"]:
        print(" -", c["message"])
    for t in result["reasoning_trace"]:
        print(f" [{t['time']}] {t['step']}: {t['detail']}")
