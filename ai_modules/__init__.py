"""
AI Modules for Smart Ambulance System
Clinical decision support and predictive analytics
"""

from .clinical_scoring import ClinicalScorer
from .ai_triage import AITriagePredictor
from .consensus import ConsensusEngine, DiagnosticAgent, SeverityAgent, ProtocolAgent

__all__ = [
    "ClinicalScorer",
    "AITriagePredictor",
    "ConsensusEngine",
    "DiagnosticAgent",
    "SeverityAgent",
    "ProtocolAgent",
]
