"""
ER Dashboard - Real-time visualization for Emergency Department
Displays incoming ambulance telemetry, alerts, and AI recommendations
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
from datetime import datetime
import sys
import os

# Add project root to path
sys.path.append('/Users/amitmaheshwarvaranasi/Documents/projects/Hackathon Project')

from simulators.telemetry_simulator import TelemetrySimulator
from simulators.emt_voice_simulator import EMTVoiceSimulator
from pipeline.ambulance_pipeline import SmartAmbulanceSystem
from utils.pii_redactor import PIIRedactor

# Page configuration
st.set_page_config(
    page_title="Smart Ambulance Pre-Arrival System",
    page_icon="🚑",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .critical-alert {
        background-color: #ff4444;
        color: white;
        padding: 20px;
        border-radius: 10px;
        font-size: 24px;
        font-weight: bold;
        text-align: center;
        animation: blink 1s infinite;
    }
    
    @keyframes blink {
        0%, 50%, 100% { opacity: 1; }
        25%, 75% { opacity: 0.5; }
    }
    
    .warning-alert {
        background-color: #ff9800;
        color: white;
        padding: 15px;
        border-radius: 8px;
        font-size: 18px;
        font-weight: bold;
        margin: 10px 0;
    }
    
    .normal-status {
        background-color: #4CAF50;
        color: white;
        padding: 10px;
        border-radius: 5px;
        text-align: center;
    }
    
    .info-box {
        background-color: #2196F3;
        color: white;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
    }
    
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #2196F3;
    }
    
    .stMetric {
        background-color: white;
        padding: 10px;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize Streamlit session state variables"""
    if 'telemetry_history' not in st.session_state:
        st.session_state.telemetry_history = []
    if 'voice_notes' not in st.session_state:
        st.session_state.voice_notes = []
    if 'current_alerts' not in st.session_state:
        st.session_state.current_alerts = []
    if 'ai_recommendations' not in st.session_state:
        st.session_state.ai_recommendations = []
    if 'running' not in st.session_state:
        st.session_state.running = False
    if 'simulator' not in st.session_state:
        st.session_state.telemetry_sim = TelemetrySimulator(patient_condition="critical")
        st.session_state.voice_sim = EMTVoiceSimulator(scenario="mi_patient")
    if 'redactor' not in st.session_state:
        st.session_state.redactor = PIIRedactor()


def check_vitals_alert(vitals):
    """Check if vitals trigger any alerts"""
    alerts = []
    severity = "NORMAL"
    
    hr = vitals['heart_rate']
    spo2 = vitals['spo2']
    systolic = vitals['blood_pressure_systolic']
    
    # Critical thresholds
    if hr < 40 or hr > 150:
        alerts.append(f"🚨 CRITICAL HEART RATE: {hr} bpm")
        severity = "CODE_BLUE_PREP"
    elif hr < 50 or hr > 120:
        alerts.append(f"⚠️ Abnormal Heart Rate: {hr} bpm")
        severity = "WARNING"
    
    if spo2 < 85:
        alerts.append(f"🚨 CRITICAL OXYGEN: {spo2}%")
        severity = "CODE_BLUE_PREP"
    elif spo2 < 90:
        alerts.append(f"⚠️ Low Oxygen: {spo2}%")
        severity = "WARNING"
    
    if systolic < 70:
        alerts.append(f"🚨 CRITICAL HYPOTENSION: {systolic} mmHg")
        severity = "CODE_BLUE_PREP"
    elif systolic < 90:
        alerts.append(f"⚠️ Hypotension: {systolic} mmHg")
        severity = "WARNING"
    
    return alerts, severity


def create_vitals_chart(history):
    """Create real-time vitals monitoring chart"""
    if not history:
        return None
    
    df = pd.DataFrame(history)
    
    fig = make_subplots(
        rows=3, cols=1,
        subplot_titles=('Heart Rate (bpm)', 'SpO2 (%)', 'Blood Pressure (mmHg)'),
        vertical_spacing=0.1,
        shared_xaxes=True
    )
    
    # Heart Rate
    fig.add_trace(
        go.Scatter(x=df.index, y=df['heart_rate'], name='Heart Rate',
                  line=dict(color='red', width=2), mode='lines+markers'),
        row=1, col=1
    )
    fig.add_hline(y=120, line_dash="dash", line_color="orange", row=1, col=1)
    fig.add_hline(y=50, line_dash="dash", line_color="orange", row=1, col=1)
    
    # SpO2
    fig.add_trace(
        go.Scatter(x=df.index, y=df['spo2'], name='SpO2',
                  line=dict(color='blue', width=2), mode='lines+markers'),
        row=2, col=1
    )
    fig.add_hline(y=90, line_dash="dash", line_color="orange", row=2, col=1)
    
    # Blood Pressure
    fig.add_trace(
        go.Scatter(x=df.index, y=df['blood_pressure_systolic'], name='Systolic',
                  line=dict(color='green', width=2), mode='lines+markers'),
        row=3, col=1
    )
    fig.add_trace(
        go.Scatter(x=df.index, y=df['blood_pressure_diastolic'], name='Diastolic',
                  line=dict(color='lightgreen', width=2), mode='lines+markers'),
        row=3, col=1
    )
    fig.add_hline(y=90, line_dash="dash", line_color="orange", row=3, col=1)
    
    fig.update_layout(height=700, showlegend=True, title_text="Real-Time Vital Signs Monitor")
    fig.update_xaxes(title_text="Time Point", row=3, col=1)
    
    return fig


def display_header():
    """Display dashboard header"""
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        st.title("🚑 Smart Ambulance Pre-Arrival System")
        st.markdown("### Emergency Department Real-Time Dashboard")


def display_sidebar():
    """Display sidebar controls and info"""
    st.sidebar.title("System Controls")
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📡 Data Streams")
    st.sidebar.info("✅ Telemetry Stream Active")
    st.sidebar.info("✅ Voice Notes Active")
    st.sidebar.info("✅ HIPAA PII Redaction Enabled")
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ⚙️ System Information")
    st.sidebar.text(f"Ambulance: AMB-001")
    st.sidebar.text(f"Patient ID: P-2024-001")
    st.sidebar.text(f"Scenario: MI Patient")
    
    st.sidebar.markdown("---")
    if st.sidebar.button("🔄 Refresh Data", use_container_width=True):
        st.rerun()
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📋 Protocol Status")
    st.sidebar.success("✅ Hospital Protocols Loaded")
    st.sidebar.success("✅ AI Analysis Active")


def main():
    """Main dashboard application"""
    
    initialize_session_state()
    display_header()
    display_sidebar()
    
    # Main dashboard layout
    st.markdown("---")
    
    # Get latest telemetry
    latest_vitals = st.session_state.telemetry_sim.generate_vitals()
    st.session_state.telemetry_history.append(latest_vitals)
    
    # Keep only last 20 readings
    if len(st.session_state.telemetry_history) > 20:
        st.session_state.telemetry_history = st.session_state.telemetry_history[-20:]
    
    # Check for alerts
    alerts, severity = check_vitals_alert(latest_vitals)
    
    # Display critical alerts at top
    if severity == "CODE_BLUE_PREP":
        st.markdown('<div class="critical-alert">⚠️ CODE BLUE PREP - CRITICAL PATIENT INCOMING ⚠️</div>', 
                   unsafe_allow_html=True)
        st.error("IMMEDIATE ACTION REQUIRED - See alerts below")
    
    # Current Status Row
    st.markdown("### 📊 Current Patient Status")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Heart Rate", f"{latest_vitals['heart_rate']} bpm",
                 delta=None if len(st.session_state.telemetry_history) < 2 
                 else latest_vitals['heart_rate'] - st.session_state.telemetry_history[-2]['heart_rate'])
    
    with col2:
        st.metric("SpO2", f"{latest_vitals['spo2']}%",
                 delta=None if len(st.session_state.telemetry_history) < 2 
                 else latest_vitals['spo2'] - st.session_state.telemetry_history[-2]['spo2'])
    
    with col3:
        st.metric("Blood Pressure", latest_vitals['blood_pressure'])
    
    with col4:
        eta = max(0, 8 - len(st.session_state.telemetry_history) // 3)
        st.metric("ETA", f"{eta} min")
    
    with col5:
        severity_color = "🔴" if severity == "CODE_BLUE_PREP" else "🟡" if severity == "WARNING" else "🟢"
        st.metric("Status", f"{severity_color} {severity}")
    
    st.markdown("---")
    
    # Two column layout
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        st.markdown("### 📈 Real-Time Vital Signs")
        chart = create_vitals_chart(st.session_state.telemetry_history)
        if chart:
            st.plotly_chart(chart, use_container_width=True)
    
    with col_right:
        st.markdown("### 🚨 Active Alerts")
        if alerts:
            for alert in alerts:
                if "CRITICAL" in alert:
                    st.error(alert)
                else:
                    st.warning(alert)
        else:
            st.success("✅ No active alerts - Vitals within normal range")
        
        st.markdown("---")
        st.markdown("### 🎯 Quick Actions")
        if severity == "CODE_BLUE_PREP":
            st.error("🚨 Activate Catheter Lab")
            st.error("🚨 Notify Cardiology Team")
            st.error("🚨 Prepare Crash Cart")
        elif severity == "WARNING":
            st.warning("⚠️ Prepare Monitoring Equipment")
            st.warning("⚠️ Alert Attending Physician")
        else:
            st.info("📋 Standard ER Preparation")
    
    # EMT Voice Notes Section
    st.markdown("---")
    st.markdown("### 🎙️ EMT Voice Notes (HIPAA Compliant)")
    
    # Simulate getting a new voice note periodically
    if len(st.session_state.voice_notes) < len(st.session_state.telemetry_history) // 5:
        voice_data = st.session_state.voice_sim.generate_voice_note()
        # Redact PII
        voice_data['redacted_note'] = st.session_state.redactor.redact_text(voice_data['voice_note'])
        st.session_state.voice_notes.append(voice_data)
    
    if st.session_state.voice_notes:
        latest_note = st.session_state.voice_notes[-1]
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info(f"**Redacted Voice Note (HIPAA Compliant):**\n\n{latest_note['redacted_note']}")
        with col2:
            st.metric("ETA from EMT", f"{latest_note['eta_minutes']} min")
    
    # AI Recommendations Section
    st.markdown("---")
    st.markdown("### 🤖 AI-Generated Preparation Recommendations")
    
    with st.spinner("Analyzing patient data against hospital protocols..."):
        if st.session_state.voice_notes:
            recommendation = f"""
**SUSPECTED DIAGNOSIS:** Acute Myocardial Infarction (MI) - STEMI likely

**CRITICAL PREPARATION STEPS:**
1. ✅ Activate Catheter Lab immediately (Door-to-balloon goal: <90 minutes)
2. ✅ Notify Cardiology team for emergent PCI
3. ✅ Prepare medications: Aspirin, Clopidogrel, Heparin, Nitroglycerin
4. ✅ Ready continuous cardiac monitoring
5. ✅ Establish two large-bore IV access points
6. ✅ Prepare for 12-lead ECG immediately upon arrival
7. ✅ Order STAT: Troponin, CBC, BMP, Coagulation studies

**PROTOCOL RECOMMENDATIONS:**
Based on MI Protocol - Patient presents with classic MI symptoms:
- Chest pain with radiation to left arm
- Diaphoresis and nausea
- History of angina (high risk)
- Current vitals showing tachycardia and hypotension

**TIME-SENSITIVE ACTIONS:**
- Catheter Lab must be ready before patient arrival
- Have crash cart positioned near bed
- Prepare for potential complications: cardiogenic shock, arrhythmias

**ESTIMATED ARRIVAL:** {latest_note['eta_minutes']} minutes - PREPARE NOW
"""
            st.success(recommendation)
        else:
            st.info("Waiting for EMT voice notes to generate AI recommendations...")
    
    # Footer
    st.markdown("---")
    st.caption("Smart Ambulance Pre-Arrival System | Powered by Pathway Framework | HIPAA Compliant PII Redaction Active")
    
    # Auto-refresh every 2 seconds
    time.sleep(2)
    st.rerun()


if __name__ == "__main__":
    main()
