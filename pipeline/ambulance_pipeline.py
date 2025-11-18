"""
Smart Ambulance Pre-Arrival System - Main Pathway Pipeline
Processes real-time telemetry and voice data streams
Implements alerting, RAG-based protocol analysis, and HIPAA-compliant PII redaction
"""

import pathway as pw
from pathway.xpacks.llm import embedders, llms, prompts
from pathway.xpacks.llm.question_answering import BaseRAGQuestionAnswerer
from pathway.xpacks.llm.vector_store import VectorStoreServer
import os
from typing import Dict, Any, Optional
from datetime import datetime
import json


class SmartAmbulanceSystem:
    """Main system for processing ambulance pre-arrival data"""
    
    def __init__(self, openai_api_key: str):
        self.openai_api_key = openai_api_key
        
        # Initialize LLM and embeddings
        self.llm = llms.OpenAIChat(
            api_key=openai_api_key,
            model="gpt-4",
            temperature=0.3,
            max_tokens=500
        )
        
        self.embedder = embedders.OpenAIEmbedder(
            api_key=openai_api_key,
            model="text-embedding-3-small"
        )
        
        # Load hospital protocols for RAG
        self.protocols_path = "/Users/amitmaheshwarvaranasi/Documents/projects/Hackathon Project/data/hospital_protocols.txt"
        
    def check_critical_vitals(self, vitals_row) -> Dict[str, Any]:
        """
        Check if vital signs exceed critical thresholds
        Returns alert information if critical
        """
        heart_rate = vitals_row.heart_rate
        spo2 = vitals_row.spo2
        systolic_bp = vitals_row.blood_pressure_systolic
        
        alerts = []
        severity = "NORMAL"
        
        # Critical thresholds
        if heart_rate < 40 or heart_rate > 150:
            alerts.append(f"CRITICAL HEART RATE: {heart_rate} bpm")
            severity = "CODE_BLUE_PREP"
        elif heart_rate < 50 or heart_rate > 120:
            alerts.append(f"Abnormal Heart Rate: {heart_rate} bpm")
            severity = "WARNING"
        
        if spo2 < 85:
            alerts.append(f"CRITICAL OXYGEN: {spo2}%")
            severity = "CODE_BLUE_PREP"
        elif spo2 < 90:
            alerts.append(f"Low Oxygen: {spo2}%")
            severity = "WARNING"
        
        if systolic_bp < 70:
            alerts.append(f"CRITICAL HYPOTENSION: {systolic_bp} mmHg")
            severity = "CODE_BLUE_PREP"
        elif systolic_bp < 90:
            alerts.append(f"Hypotension: {systolic_bp} mmHg")
            severity = "WARNING"
        
        return {
            "has_alert": len(alerts) > 0,
            "severity": severity,
            "alerts": alerts,
            "timestamp": vitals_row.timestamp,
            "heart_rate": heart_rate,
            "spo2": spo2,
            "blood_pressure": vitals_row.blood_pressure
        }
    
    def redact_pii_from_voice(self, voice_row) -> str:
        """Redact PII from voice notes for HIPAA compliance"""
        # Import here to avoid circular dependencies
        import sys
        sys.path.append('/Users/amitmaheshwarvaranasi/Documents/projects/Hackathon Project')
        from utils.pii_redactor import redact_pii
        
        return redact_pii(voice_row.voice_note)
    
    def analyze_with_rag(self, voice_note: str, vitals: str) -> str:
        """
        Use RAG to analyze EMT notes against hospital protocols
        Returns AI-generated recommendations
        """
        # Read protocol documents
        try:
            with open(self.protocols_path, 'r') as f:
                protocols = f.read()
        except Exception as e:
            protocols = "Unable to load protocols"
        
        # Create prompt for analysis
        prompt = f"""You are an emergency medicine AI assistant analyzing pre-arrival ambulance data.

HOSPITAL PROTOCOLS:
{protocols}

CURRENT PATIENT DATA:
EMT Voice Note: {voice_note}
Current Vitals: {vitals}

Based on the protocols and patient data, provide:
1. Suspected diagnosis or condition
2. Critical preparation steps for the ER team
3. Specific protocol recommendations
4. Estimated time-sensitive actions needed

Keep response concise, actionable, and organized. Focus on what the ER team needs to prepare IMMEDIATELY."""

        try:
            response = self.llm(prompt)
            return response
        except Exception as e:
            return f"Error generating AI analysis: {str(e)}"
    
    def create_telemetry_stream(self):
        """Create a telemetry data stream using Pathway connectors"""
        # In production, this would connect to actual data sources
        # For demo, we'll use a simulated connector
        
        class TelemetrySchema(pw.Schema):
            timestamp: str
            ambulance_id: str
            patient_id: str
            heart_rate: int
            spo2: int
            blood_pressure_systolic: int
            blood_pressure_diastolic: int
            blood_pressure: str
            condition: str
        
        # This will be replaced with actual streaming connector
        return None  # Placeholder
    
    def process_streams(self, telemetry_table, voice_table):
        """
        Main processing pipeline for both data streams
        
        Args:
            telemetry_table: Pathway table with telemetry data
            voice_table: Pathway table with voice notes
        """
        
        # Step 1: Monitor telemetry for critical vitals
        alerts = telemetry_table.select(
            **{
                'alert_info': pw.apply(self.check_critical_vitals, pw.this)
            }
        )
        
        # Step 2: Redact PII from voice notes
        redacted_voice = voice_table.select(
            timestamp=pw.this.timestamp,
            ambulance_id=pw.this.ambulance_id,
            eta_minutes=pw.this.eta_minutes,
            original_note=pw.this.voice_note,
            redacted_note=pw.apply(self.redact_pii_from_voice, pw.this)
        )
        
        # Step 3: Combine latest vitals with voice notes for RAG analysis
        # Join on ambulance_id to correlate data streams
        combined = redacted_voice.join(
            alerts,
            redacted_voice.ambulance_id == alerts.ambulance_id,
            how=pw.JoinMode.LEFT
        ).select(
            timestamp=redacted_voice.timestamp,
            ambulance_id=redacted_voice.ambulance_id,
            eta_minutes=redacted_voice.eta_minutes,
            voice_note=redacted_voice.redacted_note,
            vitals_info=alerts.alert_info
        )
        
        return alerts, redacted_voice, combined
    
    def generate_er_recommendation(self, combined_data) -> str:
        """Generate final ER preparation recommendation"""
        
        voice_note = combined_data.get('voice_note', '')
        vitals = combined_data.get('vitals_info', {})
        eta = combined_data.get('eta_minutes', 'Unknown')
        
        vitals_summary = f"HR: {vitals.get('heart_rate', 'N/A')} bpm, SpO2: {vitals.get('spo2', 'N/A')}%, BP: {vitals.get('blood_pressure', 'N/A')}"
        
        # Generate AI recommendation using RAG
        recommendation = self.analyze_with_rag(voice_note, vitals_summary)
        
        # Combine with alert severity
        severity = vitals.get('severity', 'NORMAL')
        
        output = {
            'timestamp': datetime.now().isoformat(),
            'eta_minutes': eta,
            'severity': severity,
            'alerts': vitals.get('alerts', []),
            'ai_recommendation': recommendation,
            'vitals_summary': vitals_summary
        }
        
        return output


def create_er_dashboard_output(alerts, recommendations):
    """Format output for ER dashboard display"""
    
    dashboard_data = {
        'critical_alerts': [],
        'warnings': [],
        'recommendations': [],
        'patient_status': 'MONITORING'
    }
    
    return dashboard_data


# Main execution function
def run_pipeline():
    """Run the Smart Ambulance Pipeline"""
    
    # Get API key from environment
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables")
    
    # Initialize system
    system = SmartAmbulanceSystem(openai_api_key=api_key)
    
    print("Smart Ambulance Pre-Arrival System - Pathway Pipeline")
    print("=" * 80)
    print("Initializing data streams...")
    print("Ready to receive telemetry and voice data from ambulances")
    print("=" * 80)
    
    return system


if __name__ == "__main__":
    run_pipeline()
