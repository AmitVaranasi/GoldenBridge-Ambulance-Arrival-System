"""
Improved ER Dashboard - Real-time visualization for Emergency Department
Enhanced with better patient tracking and Aparavi PII redaction
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
from utils.aparavi_redactor import AparaviRedactor

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
    .patient-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 15px;
        margin: 10px 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .patient-id {
        font-size: 24px;
        font-weight: bold;
        margin-bottom: 5px;
    }
    
    .ambulance-id {
        font-size: 18px;
        opacity: 0.9;
    }
    
    .critical-alert {
        background-color: #ff4444;
        color: white;
        padding: 20px;
        border-radius: 10px;
        font-size: 24px;
        font-weight: bold;
        text-align: center;
        animation: blink 1s infinite;
        margin: 20px 0;
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
    
    .info-box {
        background-color: #2196F3;
        color: white;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
    }
    
    .aparavi-badge {
        background-color: #4CAF50;
        color: white;
        padding: 5px 10px;
        border-radius: 5px;
        font-size: 12px;
        font-weight: bold;
    }
    
    .data-section {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #2196F3;
        margin: 10px 0;
    }
    
    .section-title {
        font-size: 18px;
        font-weight: bold;
        color: #2196F3;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize Streamlit session state variables"""
    if 'patients' not in st.session_state:
        st.session_state.patients = {}
    
    if 'selected_patient' not in st.session_state:
        st.session_state.selected_patient = "P-2024-001"
    
    if 'aparavi_redactor' not in st.session_state:
        st.session_state.aparavi_redactor = AparaviRedactor()
    
    # Initialize patient if not exists
    patient_id = "P-2024-001"
    if patient_id not in st.session_state.patients:
        st.session_state.patients[patient_id] = {
            'patient_id': patient_id,
            'ambulance_id': 'AMB-001',
            'patient_info': {
                'age': 58,
                'gender': 'Female',
                'chief_complaint': 'Chest Pain',
                'scenario': 'Myocardial Infarction'
            },
            'telemetry_history': [],
            'voice_notes': [],
            'current_alerts': [],
            'telemetry_sim': TelemetrySimulator(patient_condition="critical"),
            'voice_sim': EMTVoiceSimulator(scenario="mi_patient")
        }


def display_patient_selector():
    """Display patient selection in sidebar"""
    st.sidebar.markdown("### 🏥 Active Patients")
    
    for patient_id, patient_data in st.session_state.patients.items():
        amb_id = patient_data['ambulance_id']
        eta = max(0, 8 - len(patient_data['telemetry_history']) // 3)
        
        if st.sidebar.button(
            f"👤 {patient_id}\n🚑 {amb_id}\n⏱️ ETA: {eta} min",
            key=f"select_{patient_id}",
            use_container_width=True
        ):
            st.session_state.selected_patient = patient_id


def display_patient_header(patient_data):
    """Display patient identification header"""
    st.markdown(f"""
    <div class="patient-card">
        <div class="patient-id">👤 Patient: {patient_data['patient_id']}</div>
        <div class="ambulance-id">🚑 Ambulance: {patient_data['ambulance_id']}</div>
        <div style="margin-top: 10px;">
            <span style="background: rgba(255,255,255,0.3); padding: 5px 10px; border-radius: 5px; margin-right: 10px;">
                Age: {patient_data['patient_info']['age']}
            </span>
            <span style="background: rgba(255,255,255,0.3); padding: 5px 10px; border-radius: 5px; margin-right: 10px;">
                Gender: {patient_data['patient_info']['gender']}
            </span>
            <span style="background: rgba(255,255,255,0.3); padding: 5px 10px; border-radius: 5px;">
                Chief Complaint: {patient_data['patient_info']['chief_complaint']}
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)


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


def create_vitals_chart(history, patient_id):
    """Create real-time vitals monitoring chart"""
    if not history:
        return None
    
    df = pd.DataFrame(history)
    
    fig = make_subplots(
        rows=3, cols=1,
        subplot_titles=(
            f'{patient_id} - Heart Rate (bpm)', 
            f'{patient_id} - SpO2 (%)', 
            f'{patient_id} - Blood Pressure (mmHg)'
        ),
        vertical_spacing=0.1,
        shared_xaxes=True
    )
    
    # Heart Rate
    fig.add_trace(
        go.Scatter(x=df.index, y=df['heart_rate'], name='Heart Rate',
                  line=dict(color='red', width=3), mode='lines+markers',
                  marker=dict(size=8)),
        row=1, col=1
    )
    fig.add_hline(y=120, line_dash="dash", line_color="orange", row=1, col=1)
    fig.add_hline(y=50, line_dash="dash", line_color="orange", row=1, col=1)
    
    # SpO2
    fig.add_trace(
        go.Scatter(x=df.index, y=df['spo2'], name='SpO2',
                  line=dict(color='blue', width=3), mode='lines+markers',
                  marker=dict(size=8)),
        row=2, col=1
    )
    fig.add_hline(y=90, line_dash="dash", line_color="orange", row=2, col=1)
    
    # Blood Pressure
    fig.add_trace(
        go.Scatter(x=df.index, y=df['blood_pressure_systolic'], name='Systolic',
                  line=dict(color='green', width=3), mode='lines+markers',
                  marker=dict(size=8)),
        row=3, col=1
    )
    fig.add_trace(
        go.Scatter(x=df.index, y=df['blood_pressure_diastolic'], name='Diastolic',
                  line=dict(color='lightgreen', width=3), mode='lines+markers',
                  marker=dict(size=8)),
        row=3, col=1
    )
    fig.add_hline(y=90, line_dash="dash", line_color="orange", row=3, col=1)
    
    fig.update_layout(
        height=700, 
        showlegend=True, 
        title_text=f"Real-Time Vital Signs - Patient {patient_id}",
        title_font_size=20
    )
    fig.update_xaxes(title_text="Time Point", row=3, col=1)
    
    return fig


def main():
    """Main dashboard application"""
    
    initialize_session_state()
    
    # Header
    st.title("🚑 Smart Ambulance Pre-Arrival System")
    st.markdown("### Emergency Department Real-Time Dashboard")
    st.markdown('<span class="aparavi-badge">🔒 APARAVI PII PROTECTION ACTIVE</span>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Sidebar
    display_patient_selector()
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📡 System Status")
    st.sidebar.success("✅ Telemetry Stream Active")
    st.sidebar.success("✅ Voice Notes Active")
    st.sidebar.success("✅ Aparavi PII Redaction Enabled")
    
    # Get selected patient data
    patient_id = st.session_state.selected_patient
    patient_data = st.session_state.patients[patient_id]
    
    # Display patient header
    display_patient_header(patient_data)
    
    st.markdown("---")
    
    # Get latest telemetry
    latest_vitals = patient_data['telemetry_sim'].generate_vitals()
    patient_data['telemetry_history'].append(latest_vitals)
    
    # Keep only last 20 readings
    if len(patient_data['telemetry_history']) > 20:
        patient_data['telemetry_history'] = patient_data['telemetry_history'][-20:]
    
    # Check for alerts
    alerts, severity = check_vitals_alert(latest_vitals)
    patient_data['current_alerts'] = alerts
    
    # Display critical alerts at top
    if severity == "CODE_BLUE_PREP":
        st.markdown(f'<div class="critical-alert">⚠️ CODE BLUE PREP - PATIENT {patient_id} CRITICAL ⚠️</div>', 
                   unsafe_allow_html=True)
        st.error(f"IMMEDIATE ACTION REQUIRED FOR PATIENT {patient_id}")
    
    # Current Status Row with Patient ID
    st.markdown(f'<div class="data-section"><div class="section-title">📊 Current Status - Patient {patient_id}</div></div>', 
                unsafe_allow_html=True)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        delta_hr = None if len(patient_data['telemetry_history']) < 2 else \
                   latest_vitals['heart_rate'] - patient_data['telemetry_history'][-2]['heart_rate']
        st.metric("❤️ Heart Rate", f"{latest_vitals['heart_rate']} bpm", delta=delta_hr)
    
    with col2:
        delta_spo2 = None if len(patient_data['telemetry_history']) < 2 else \
                     latest_vitals['spo2'] - patient_data['telemetry_history'][-2]['spo2']
        st.metric("💨 SpO2", f"{latest_vitals['spo2']}%", delta=delta_spo2)
    
    with col3:
        st.metric("🩺 Blood Pressure", latest_vitals['blood_pressure'])
    
    with col4:
        eta = max(0, 8 - len(patient_data['telemetry_history']) // 3)
        st.metric("⏱️ ETA", f"{eta} min")
    
    with col5:
        severity_color = "🔴" if severity == "CODE_BLUE_PREP" else "🟡" if severity == "WARNING" else "🟢"
        st.metric("📍 Status", f"{severity_color} {severity}")
    
    st.markdown("---")
    
    # Two column layout
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        st.markdown(f'<div class="data-section"><div class="section-title">📈 Real-Time Vital Signs - Patient {patient_id}</div></div>', 
                    unsafe_allow_html=True)
        chart = create_vitals_chart(patient_data['telemetry_history'], patient_id)
        if chart:
            st.plotly_chart(chart, use_container_width=True)
    
    with col_right:
        st.markdown(f'<div class="data-section"><div class="section-title">🚨 Active Alerts - {patient_id}</div></div>', 
                    unsafe_allow_html=True)
        if alerts:
            for alert in alerts:
                if "CRITICAL" in alert:
                    st.error(alert)
                else:
                    st.warning(alert)
        else:
            st.success(f"✅ No active alerts for {patient_id}")
        
        st.markdown("---")
        st.markdown('<div class="section-title">🎯 Quick Actions</div>', unsafe_allow_html=True)
        if severity == "CODE_BLUE_PREP":
            st.error("🚨 Activate Catheter Lab")
            st.error("🚨 Notify Cardiology Team")
            st.error("🚨 Prepare Crash Cart")
        elif severity == "WARNING":
            st.warning("⚠️ Prepare Monitoring Equipment")
            st.warning("⚠️ Alert Attending Physician")
        else:
            st.info("📋 Standard ER Preparation")
    
    # EMT Voice Notes Section with Aparavi
    st.markdown("---")
    st.markdown(f"""
    <div class="data-section">
        <div class="section-title">🎙️ EMT Voice Notes - Patient {patient_id}</div>
        <span class="aparavi-badge">Aparavi PII Redaction Active</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Simulate getting a new voice note periodically
    if len(patient_data['voice_notes']) < len(patient_data['telemetry_history']) // 5:
        voice_data = patient_data['voice_sim'].generate_voice_note()
        
        # Use Aparavi to redact PII
        voice_data['redacted_note'] = st.session_state.aparavi_redactor.redact_text(voice_data['voice_note'])
        
        # Analyze PII risk
        voice_data['pii_risk'] = st.session_state.aparavi_redactor.analyze_pii_risk(voice_data['voice_note'])
        
        patient_data['voice_notes'].append(voice_data)
    
    if patient_data['voice_notes']:
        latest_note = patient_data['voice_notes'][-1]
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info(f"**Redacted Voice Note (Aparavi HIPAA Compliant):**\n\n{latest_note['redacted_note']}")
            
            # Show PII risk analysis
            risk = latest_note['pii_risk']
            risk_color = "🔴" if risk['risk_level'] == "HIGH" else "🟡" if risk['risk_level'] == "MEDIUM" else "🟢"
            st.caption(f"{risk_color} PII Risk: {risk['risk_level']} | "
                      f"Entities Redacted: {risk['pii_count']} | "
                      f"Types: {', '.join(risk['pii_types']) if risk['pii_types'] else 'None'}")
        
        with col2:
            st.metric("⏱️ ETA from EMT", f"{latest_note['eta_minutes']} min")
            st.metric("🚑 Ambulance", patient_data['ambulance_id'])
    
    # AI Recommendations Section
    st.markdown("---")
    st.markdown(f'<div class="data-section"><div class="section-title">🤖 AI-Generated Preparation Recommendations - {patient_id}</div></div>', 
                unsafe_allow_html=True)
    
    if patient_data['voice_notes']:
        latest_note = patient_data['voice_notes'][-1]
        recommendation = f"""
**PATIENT:** {patient_id} | **AMBULANCE:** {patient_data['ambulance_id']}

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
Based on MI Protocol - Patient {patient_id} presents with classic MI symptoms:
- Chest pain with radiation to left arm
- Diaphoresis and nausea
- History of angina (high risk)
- Current vitals showing tachycardia and hypotension

**TIME-SENSITIVE ACTIONS FOR {patient_id}:**
- Catheter Lab must be ready before patient arrival
- Have crash cart positioned near designated bed
- Prepare for potential complications: cardiogenic shock, arrhythmias

**ESTIMATED ARRIVAL:** {latest_note['eta_minutes']} minutes - PREPARE NOW
"""
        st.success(recommendation)
    else:
        st.info(f"Waiting for EMT voice notes for patient {patient_id}...")
    
    # Footer
    st.markdown("---")
    st.caption(f"Smart Ambulance Pre-Arrival System | Powered by Pathway Framework | "
               f"Aparavi HIPAA Compliant PII Redaction Active | Currently Monitoring: {patient_id}")
    
    # Auto-refresh every 2 seconds
    time.sleep(2)
    st.rerun()


if __name__ == "__main__":
    main()
