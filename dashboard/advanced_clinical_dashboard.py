"""
Advanced Clinical Dashboard - Complete Clinical Decision Support System
Multiple ambulances, clinical scores, AI predictions, and resource management
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
from utils.aparavi_redactor import AparaviRedactor
from ai_modules.clinical_scoring import ClinicalScorer
from ai_modules.ai_triage import AITriagePredictor

# Page configuration
st.set_page_config(
    page_title="Advanced Clinical Dashboard",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .ambulance-selector {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 15px;
        border-radius: 10px;
        margin: 5px 0;
        cursor: pointer;
        transition: transform 0.2s;
    }
    .ambulance-selector:hover {
        transform: scale(1.02);
    }
    .critical-badge {
        background-color: #ff4444;
        color: white;
        padding: 5px 10px;
        border-radius: 5px;
        font-weight: bold;
    }
    .emergent-badge {
        background-color: #ff9800;
        color: white;
        padding: 5px 10px;
        border-radius: 5px;
        font-weight: bold;
    }
    .score-card {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #2196F3;
        margin: 10px 0;
    }
    .resource-available {
        color: #4CAF50;
        font-weight: bold;
    }
    .resource-limited {
        color: #ff9800;
        font-weight: bold;
    }
    .resource-critical {
        color: #ff4444;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize with multiple ambulances"""
    if 'patients' not in st.session_state:
        st.session_state.patients = {}
    
    if 'selected_patient' not in st.session_state:
        st.session_state.selected_patient = "P-2024-001"
    
    if 'aparavi_redactor' not in st.session_state:
        st.session_state.aparavi_redactor = AparaviRedactor()
    
    if 'scorer' not in st.session_state:
        st.session_state.scorer = ClinicalScorer()
    
    if 'predictor' not in st.session_state:
        st.session_state.predictor = AITriagePredictor()
    
    if 'next_patient_num' not in st.session_state:
        st.session_state.next_patient_num = 4
    
    if 'next_amb_num' not in st.session_state:
        st.session_state.next_amb_num = 4
    
    if 'hospital_resources' not in st.session_state:
        st.session_state.hospital_resources = {
            'icu_beds': {'total': 12, 'available': 8},
            'ct_scanner': {'total': 2, 'available': 1},
            'mri_scanner': {'total': 1, 'available': 1},
            'or_rooms': {'total': 6, 'available': 4},
            'blood_units_o_neg': {'available': 25},
            'blood_units_o_pos': {'available': 30},
            'ventilators': {'total': 15, 'available': 10}
        }
    
    # Initialize multiple patients
    patients_data = [
        ('P-2024-001', 'AMB-001', 58, 'Female', 'Chest Pain', 'critical', 'mi_patient', 8),
        ('P-2024-002', 'AMB-002', 72, 'Male', 'Stroke Symptoms', 'critical', 'mi_patient', 10),
        ('P-2024-003', 'AMB-003', 45, 'Male', 'Trauma - MVA', 'deteriorating', 'trauma', 6),
    ]
    
    for pid, amb_id, age, gender, complaint, condition, scenario, initial_eta in patients_data:
        if pid not in st.session_state.patients:
            st.session_state.patients[pid] = {
                'patient_id': pid,
                'ambulance_id': amb_id,
                'patient_info': {
                    'age': age,
                    'gender': gender,
                    'chief_complaint': complaint,
                    'scenario': scenario,
                    'allergies': ['NKDA'],
                    'medications': ['Aspirin 81mg', 'Lisinopril 10mg'] if pid == 'P-2024-001' else []
                },
                'telemetry_history': [],
                'voice_notes': [],
                'current_alerts': [],
                'telemetry_sim': TelemetrySimulator(patient_condition=condition),
                'voice_sim': EMTVoiceSimulator(scenario=scenario),
                'clinical_scores': {},
                'severity': {},
                'predictions': {},
                'active_alerts': [],
                'activated_protocols': {},
                'initial_eta': initial_eta,
                'elapsed_time': 0,
                'status': 'EN_ROUTE',  # EN_ROUTE, ARRIVED, COMPLETED
                'handoff_summary': None
            }


def add_new_ambulance():
    """Add a new ambulance to the system"""
    import random
    
    scenarios = [
        ('Chest Pain - Possible MI', 'critical', 'mi_patient'),
        ('Stroke Symptoms', 'critical', 'mi_patient'),
        ('Trauma - MVA', 'deteriorating', 'trauma'),
        ('Sepsis Suspected', 'critical', 'mi_patient'),
        ('Respiratory Distress', 'deteriorating', 'mi_patient')
    ]
    
    complaint, condition, scenario = random.choice(scenarios)
    
    pid = f"P-2024-{st.session_state.next_patient_num:03d}"
    amb_id = f"AMB-{st.session_state.next_amb_num:03d}"
    age = random.randint(35, 85)
    gender = random.choice(['Male', 'Female'])
    initial_eta = random.randint(5, 12)
    
    st.session_state.patients[pid] = {
        'patient_id': pid,
        'ambulance_id': amb_id,
        'patient_info': {
            'age': age,
            'gender': gender,
            'chief_complaint': complaint,
            'scenario': scenario,
            'allergies': ['NKDA'],
            'medications': []
        },
        'telemetry_history': [],
        'voice_notes': [],
        'current_alerts': [],
        'telemetry_sim': TelemetrySimulator(patient_condition=condition),
        'voice_sim': EMTVoiceSimulator(scenario=scenario),
        'clinical_scores': {},
        'severity': {},
        'predictions': {},
        'active_alerts': [],
        'activated_protocols': {},
        'initial_eta': initial_eta,
        'elapsed_time': 0,
        'status': 'EN_ROUTE',
        'handoff_summary': None
    }
    
    st.session_state.next_patient_num += 1
    st.session_state.next_amb_num += 1
    st.session_state.selected_patient = pid


def display_ambulance_selector():
    """Display ambulance selector in sidebar"""
    st.sidebar.markdown("### 🚑 Incoming Ambulances")
    
    # Add new ambulance button
    if st.sidebar.button("➕ Add New Ambulance", use_container_width=True, type="secondary"):
        add_new_ambulance()
        st.rerun()
    
    st.sidebar.markdown("---")
    
    # Display active ambulances
    en_route_count = sum(1 for p in st.session_state.patients.values() if p['status'] == 'EN_ROUTE')
    arrived_count = sum(1 for p in st.session_state.patients.values() if p['status'] == 'ARRIVED')
    
    st.sidebar.info(f"🚑 En Route: {en_route_count} | ✅ Arrived: {arrived_count}")
    
    for patient_id, patient_data in st.session_state.patients.items():
        amb_id = patient_data['ambulance_id']
        status = patient_data['status']
        
        # Calculate ETA
        eta = max(0, patient_data['initial_eta'] - patient_data['elapsed_time'] // 3)
        
        # Get severity for color
        severity = patient_data.get('severity', {})
        level = severity.get('level', 'UNKNOWN')
        color = severity.get('color', '🔵')
        
        # Status indicator
        if status == 'ARRIVED':
            status_icon = "✅"
            status_text = "ARRIVED"
        elif status == 'EN_ROUTE':
            status_icon = color
            status_text = f"ETA: {eta} min"
        else:
            status_icon = "✔️"
            status_text = "COMPLETED"
        
        is_selected = (patient_id == st.session_state.selected_patient)
        button_type = "primary" if is_selected else "secondary"
        
        if st.sidebar.button(
            f"{status_icon} {patient_id}\n🚑 {amb_id}\n⏱️ {status_text}\n{level}",
            key=f"select_{patient_id}",
            use_container_width=True,
            type=button_type
        ):
            st.session_state.selected_patient = patient_id


def display_hospital_resources():
    """Display hospital resource availability"""
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🏥 Hospital Resources")
    
    resources = st.session_state.hospital_resources
    
    # ICU Beds
    icu_avail = resources['icu_beds']['available']
    icu_total = resources['icu_beds']['total']
    icu_percent = (icu_avail / icu_total) * 100
    
    if icu_percent > 50:
        icu_class = "resource-available"
    elif icu_percent > 20:
        icu_class = "resource-limited"
    else:
        icu_class = "resource-critical"
    
    st.sidebar.markdown(f'<p class="{icu_class}">🛏️ ICU Beds: {icu_avail}/{icu_total}</p>', unsafe_allow_html=True)
    
    # CT Scanner
    ct_avail = resources['ct_scanner']['available']
    ct_total = resources['ct_scanner']['total']
    ct_status = "✅ Available" if ct_avail > 0 else "❌ In Use"
    st.sidebar.text(f"🔬 CT Scanner: {ct_avail}/{ct_total} {ct_status}")
    
    # MRI Scanner
    mri_avail = resources['mri_scanner']['available']
    mri_total = resources['mri_scanner']['total']
    mri_status = "✅ Available" if mri_avail > 0 else "❌ In Use"
    st.sidebar.text(f"🧲 MRI: {mri_avail}/{mri_total} {mri_status}")
    
    # OR Rooms
    or_avail = resources['or_rooms']['available']
    or_total = resources['or_rooms']['total']
    st.sidebar.text(f"🔪 OR Rooms: {or_avail}/{or_total}")
    
    # Blood Units
    st.sidebar.text(f"🩸 O- Blood: {resources['blood_units_o_neg']['available']} units")
    st.sidebar.text(f"🩸 O+ Blood: {resources['blood_units_o_pos']['available']} units")
    
    # Ventilators
    vent_avail = resources['ventilators']['available']
    vent_total = resources['ventilators']['total']
    st.sidebar.text(f"💨 Ventilators: {vent_avail}/{vent_total}")


def calculate_clinical_scores(patient_data):
    """Calculate all clinical scores for a patient"""
    scorer = st.session_state.scorer
    
    if not patient_data['telemetry_history']:
        return
    
    latest_vitals = patient_data['telemetry_history'][-1]
    
    # Add GCS and respiratory rate for scoring
    latest_vitals['gcs'] = 13
    latest_vitals['respiratory_rate'] = 24
    latest_vitals['temperature'] = 37.8
    
    # Symptoms based on scenario
    symptoms = {
        'chest_pain': patient_data['patient_info']['chief_complaint'] == 'Chest Pain',
        'st_elevation': patient_data['patient_info']['chief_complaint'] == 'Chest Pain',
        'diaphoresis': True,
        'nausea': True,
        'stroke_suspected': 'Stroke' in patient_data['patient_info']['chief_complaint'],
        'airway_obstruction': False
    }
    
    # Calculate all scores
    scores = {
        'trauma_score': scorer.calculate_trauma_score(latest_vitals),
        'qsofa': scorer.calculate_qsofa(latest_vitals),
        'stemi_checklist': scorer.calculate_stemi_checklist(symptoms),
        'shock_index': scorer.calculate_shock_index(latest_vitals),
        'airway_risk': scorer.calculate_airway_risk(latest_vitals, symptoms),
        'nihss': scorer.calculate_nihss(symptoms),
        'deterioration': scorer.calculate_deterioration_index(patient_data['telemetry_history'])
    }
    
    patient_data['clinical_scores'] = scores
    
    # Get AI predictions
    predictor = st.session_state.predictor
    
    severity = predictor.predict_severity(latest_vitals, symptoms, scores)
    patient_data['severity'] = severity
    
    active_alerts = predictor.predict_active_alerts(latest_vitals, symptoms, scores)
    patient_data['active_alerts'] = active_alerts
    
    predictions = predictor.predict_interventions(latest_vitals, symptoms, scores)
    patient_data['predictions'] = predictions
    
    protocols = predictor.activate_protocols(active_alerts, predictions['predictions'])
    patient_data['activated_protocols'] = protocols


def display_clinical_scores(patient_data):
    """Display clinical scores in UI"""
    st.markdown("### 📊 Clinical Scores & AI Analysis")
    
    scores = patient_data.get('clinical_scores', {})
    
    if not scores:
        st.info("Calculating clinical scores...")
        return
    
    # Display scores in columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🎯 AI Severity Score", 
                 f"{patient_data['severity']['score']}/100",
                 delta=patient_data['severity']['level'])
    
    with col2:
        shock = scores['shock_index']
        st.metric("⚡ Shock Index", 
                 f"{shock['value']}",
                 delta=shock['interpretation'])
    
    with col3:
        stemi = scores['stemi_checklist']
        st.metric("❤️ STEMI Score", 
                 f"{stemi['score']}",
                 delta=stemi['interpretation'])
    
    with col4:
        qsofa = scores['qsofa']
        st.metric("🦠 qSOFA (Sepsis)", 
                 f"{qsofa['score']}/3",
                 delta=qsofa['interpretation'])
    
    # Second row of scores
    col5, col6, col7, col8 = st.columns(4)
    
    with col5:
        trauma = scores['trauma_score']
        st.metric("🚗 Trauma Score", 
                 f"{trauma['score']}/7.84",
                 delta=trauma['interpretation'])
    
    with col6:
        nihss = scores['nihss']
        st.metric("🧠 NIHSS (Stroke)", 
                 f"{nihss['score']}/42",
                 delta=nihss['interpretation'])
    
    with col7:
        airway = scores['airway_risk']
        st.metric("🫁 Airway Risk", 
                 f"{airway['score']}",
                 delta=airway['interpretation'])
    
    with col8:
        deterioration = scores['deterioration']
        st.metric("📉 Deterioration Index", 
                 f"{deterioration['score']}",
                 delta=deterioration['interpretation'])


def display_active_alerts(patient_data):
    """Display active clinical alerts"""
    alerts = patient_data.get('active_alerts', [])
    
    if alerts:
        st.markdown("### 🚨 Active Alerts")
        alert_cols = st.columns(len(alerts))
        
        for i, alert in enumerate(alerts):
            with alert_cols[i]:
                if alert == 'STEMI':
                    st.error(f"❤️ **{alert}**\nActivate Cath Lab")
                elif alert == 'STROKE':
                    st.error(f"🧠 **{alert}**\nActivate Stroke Team")
                elif alert == 'TRAUMA':
                    st.error(f"🚗 **{alert}**\nActivate Trauma Team")
                elif alert == 'SEPSIS':
                    st.error(f"🦠 **{alert}**\nSepsis Protocol")
                elif alert == 'CARDIAC_ARREST_RISK':
                    st.error(f"⚠️ **ARREST RISK**\nCode Blue Prep")


def display_activated_protocols(patient_data):
    """Display activated protocols with action items"""
    protocols = patient_data.get('activated_protocols', {})
    
    if protocols:
        st.markdown("### 🔔 Activated Protocols")
        
        for protocol_name, actions in protocols.items():
            with st.expander(f"📋 {protocol_name.replace('_', ' ')}", expanded=True):
                for action in actions:
                    st.write(f"- {action}")


def display_ai_predictions(patient_data):
    """Display AI intervention predictions"""
    predictions = patient_data.get('predictions', {}).get('predictions', {})
    confidence = patient_data.get('predictions', {}).get('confidence_scores', {})
    
    if any(predictions.values()):
        st.markdown("### 🤖 AI Predictions")
        
        pred_items = []
        for key, value in predictions.items():
            if value:
                pred_name = key.replace('_', ' ').title()
                conf = confidence.get(key.replace('needs_', '').replace('likely_', ''), 0.75)
                pred_items.append(f"✅ **{pred_name}** ({conf*100:.0f}% confidence)")
        
        if pred_items:
            cols = st.columns(min(3, len(pred_items)))
            for i, pred in enumerate(pred_items):
                with cols[i % len(cols)]:
                    st.info(pred)


def update_hospital_resources(patient_data):
    """Update hospital resources when patient arrives"""
    resources = st.session_state.hospital_resources
    predictions = patient_data.get('predictions', {}).get('predictions', {})
    
    # Consume ICU bed if needed
    if predictions.get('needs_icu') and resources['icu_beds']['available'] > 0:
        resources['icu_beds']['available'] -= 1
    
    # Consume ventilator if needed
    if predictions.get('needs_intubation') and resources['ventilators']['available'] > 0:
        resources['ventilators']['available'] -= 1
    
    # Consume OR if needed
    if predictions.get('needs_or') and resources['or_rooms']['available'] > 0:
        resources['or_rooms']['available'] -= 1
    
    # Consume CT scanner temporarily
    active_alerts = patient_data.get('active_alerts', [])
    if ('STROKE' in active_alerts or 'TRAUMA' in active_alerts) and resources['ct_scanner']['available'] > 0:
        resources['ct_scanner']['available'] -= 1
    
    # Consume blood for trauma
    if 'TRAUMA' in active_alerts:
        if resources['blood_units_o_neg']['available'] >= 2:
            resources['blood_units_o_neg']['available'] -= 2


def main():
    """Main dashboard application"""
    
    initialize_session_state()
    
    # Header
    st.title("🏥 Advanced Clinical Decision Support Dashboard")
    st.markdown("**Multi-Ambulance Monitoring | AI Clinical Scores | Resource Management**")
    
    # Sidebar
    display_ambulance_selector()
    display_hospital_resources()
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📡 System Status")
    st.sidebar.success(f"✅ {len(st.session_state.patients)} Ambulances Tracked")
    st.sidebar.success("✅ Aparavi PII Protection")
    st.sidebar.success("✅ AI Scoring Active")
    
    # Get selected patient data
    patient_id = st.session_state.selected_patient
    patient_data = st.session_state.patients[patient_id]
    
    st.markdown("---")
    
    # Update telemetry only if en route
    if patient_data['status'] == 'EN_ROUTE':
        latest_vitals = patient_data['telemetry_sim'].generate_vitals()
        patient_data['telemetry_history'].append(latest_vitals)
        patient_data['elapsed_time'] += 1
        
        if len(patient_data['telemetry_history']) > 20:
            patient_data['telemetry_history'] = patient_data['telemetry_history'][-20:]
        
        # Check if ETA reached 0
        eta = max(0, patient_data['initial_eta'] - patient_data['elapsed_time'] // 3)
        if eta == 0 and patient_data['status'] == 'EN_ROUTE':
            patient_data['status'] = 'ARRIVED'
            # Generate handoff summary
            predictor = st.session_state.predictor
            patient_data['handoff_summary'] = predictor.generate_handoff_summary(patient_data)
            # Update hospital resources
            update_hospital_resources(patient_data)
    
    # Calculate clinical scores
    calculate_clinical_scores(patient_data)
    
    # Display patient header
    severity = patient_data.get('severity', {})
    status = patient_data['status']
    eta = max(0, patient_data['initial_eta'] - patient_data['elapsed_time'] // 3)
    
    col_h1, col_h2 = st.columns([3, 1])
    
    with col_h1:
        status_color = "#4CAF50" if status == 'ARRIVED' else "#667eea"
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, {status_color} 0%, #764ba2 100%); 
             color: white; padding: 20px; border-radius: 15px;">
            <h2>👤 Patient: {patient_data['patient_id']} | 🚑 {patient_data['ambulance_id']}</h2>
            <p style="font-size: 18px;">
                Age: {patient_data['patient_info']['age']} | 
                Gender: {patient_data['patient_info']['gender']} | 
                Chief Complaint: {patient_data['patient_info']['chief_complaint']}
            </p>
            <p style="font-size: 16px; margin-top: 10px;">
                Status: {'✅ ARRIVED' if status == 'ARRIVED' else f'🚑 EN ROUTE - ETA {eta} min'}
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col_h2:
        if status == 'EN_ROUTE':
            st.metric("⏱️ ETA", f"{eta} min")
        else:
            st.success("✅ ARRIVED")
        st.metric(f"{severity.get('color', '🔵')} Severity", 
                 severity.get('level', 'Unknown'))
    
    # Display handoff summary if arrived
    if status == 'ARRIVED' and patient_data.get('handoff_summary'):
        st.markdown("---")
        st.markdown("### 📋 AI-Generated Handoff Summary")
        st.success(patient_data['handoff_summary'])
    
    # Display active alerts
    display_active_alerts(patient_data)
    
    st.markdown("---")
    
    # Display clinical scores
    display_clinical_scores(patient_data)
    
    st.markdown("---")
    
    # Display AI predictions
    display_ai_predictions(patient_data)
    
    st.markdown("---")
    
    # Display activated protocols
    display_activated_protocols(patient_data)
    
    st.markdown("---")
    
    # EMS Treatment section
    st.markdown("---")
    st.markdown("### 💊 EMS Treatments Given")
    
    # Generate EMS treatments based on patient condition
    if 'ems_treatments' not in patient_data or not patient_data['ems_treatments']:
        # Initialize EMS treatments based on condition
        chief_complaint = patient_data['patient_info']['chief_complaint']
        
        if 'Chest Pain' in chief_complaint:
            patient_data['ems_treatments'] = {
                'medications': [
                    {'name': 'Aspirin', 'dose': '325mg PO', 'time': 'On scene'},
                    {'name': 'Nitroglycerin', 'dose': '0.4mg SL x2', 'time': '5 min ago'},
                    {'name': 'Morphine', 'dose': '4mg IV', 'time': '3 min ago'}
                ],
                'interventions': [
                    {'name': 'Oxygen', 'details': '4L via nasal cannula'},
                    {'name': 'IV Access', 'details': '18G in right AC'},
                    {'name': 'ECG', 'details': '12-lead obtained, ST elevations noted'},
                    {'name': 'Cardiac Monitor', 'details': 'Continuous monitoring'}
                ],
                'cpr': False,
                'defibrillation': False,
                'iv_fluids': '250ml NS'
            }
        elif 'Stroke' in chief_complaint:
            patient_data['ems_treatments'] = {
                'medications': [],
                'interventions': [
                    {'name': 'Oxygen', 'details': '2L via nasal cannula'},
                    {'name': 'IV Access', 'details': '20G in left hand'},
                    {'name': 'Blood Glucose', 'details': 'Check: 112 mg/dL'},
                    {'name': 'Stroke Assessment', 'details': 'FAST positive - left sided weakness'}
                ],
                'cpr': False,
                'defibrillation': False,
                'iv_fluids': 'NS @ KVO'
            }
        elif 'Trauma' in chief_complaint:
            patient_data['ems_treatments'] = {
                'medications': [
                    {'name': 'Fentanyl', 'dose': '50mcg IV', 'time': '2 min ago'}
                ],
                'interventions': [
                    {'name': 'C-Spine Immobilization', 'details': 'Cervical collar + backboard'},
                    {'name': 'IV Access', 'details': 'Two 16G IVs bilateral AC'},
                    {'name': 'Oxygen', 'details': '15L via non-rebreather'},
                    {'name': 'Bleeding Control', 'details': 'Pressure dressing to left leg'},
                    {'name': 'Splinting', 'details': 'Left femur traction splint'}
                ],
                'cpr': False,
                'defibrillation': False,
                'iv_fluids': '1000ml NS rapid infusion'
            }
        else:
            patient_data['ems_treatments'] = {
                'medications': [],
                'interventions': [
                    {'name': 'Oxygen', 'details': '2-4L via nasal cannula'},
                    {'name': 'IV Access', 'details': '18G IV established'}
                ],
                'cpr': False,
                'defibrillation': False,
                'iv_fluids': 'NS @ 100ml/hr'
            }
    
    # Display EMS treatments
    col_med, col_int = st.columns(2)
    
    with col_med:
        st.markdown("#### 💉 Medications")
        if patient_data['ems_treatments']['medications']:
            for med in patient_data['ems_treatments']['medications']:
                st.success(f"✅ **{med['name']}** - {med['dose']}\n\n_{med['time']}_")
        else:
            st.info("No medications administered")
    
    with col_int:
        st.markdown("#### 🏥 Interventions")
        for intervention in patient_data['ems_treatments']['interventions']:
            st.info(f"✅ **{intervention['name']}**\n\n{intervention['details']}")
    
    # Critical interventions
    col_crit1, col_crit2, col_crit3 = st.columns(3)
    with col_crit1:
        if patient_data['ems_treatments']['cpr']:
            st.error("⚠️ **CPR Performed**")
        else:
            st.success("✅ No CPR needed")
    
    with col_crit2:
        if patient_data['ems_treatments']['defibrillation']:
            st.error("⚠️ **Defibrillation Given**")
        else:
            st.success("✅ No Defibrillation")
    
    with col_crit3:
        st.info(f"💧 **IV Fluids**\n\n{patient_data['ems_treatments']['iv_fluids']}")
    
    # Vitals and details
    st.markdown("---")
    col_main, col_side = st.columns([2, 1])
    
    with col_main:
        st.markdown(f"### 📈 Vital Signs Trends - {patient_id}")
        
        if patient_data['telemetry_history']:
            df = pd.DataFrame(patient_data['telemetry_history'])
            
            fig = make_subplots(
                rows=3, cols=1,
                subplot_titles=('Heart Rate', 'SpO2', 'Blood Pressure'),
                vertical_spacing=0.1
            )
            
            fig.add_trace(go.Scatter(x=df.index, y=df['heart_rate'], 
                                    name='HR', line=dict(color='red', width=3)), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['spo2'], 
                                    name='SpO2', line=dict(color='blue', width=3)), row=2, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['blood_pressure_systolic'], 
                                    name='Systolic', line=dict(color='green', width=3)), row=3, col=1)
            
            fig.update_layout(height=600, showlegend=True)
            st.plotly_chart(fig, use_container_width=True)
    
    with col_side:
        st.markdown("### 📋 Patient Details")
        st.text(f"Allergies: {', '.join(patient_data['patient_info']['allergies'])}")
        st.text(f"Medications: {', '.join(patient_data['patient_info']['medications']) if patient_data['patient_info']['medications'] else 'None listed'}")
        
        st.markdown("### 📊 Current Vitals")
        # Get latest vitals safely
        if patient_data['telemetry_history']:
            current_vitals = patient_data['telemetry_history'][-1]
            st.metric("HR", f"{current_vitals['heart_rate']} bpm")
            st.metric("SpO2", f"{current_vitals['spo2']}%")
            st.metric("BP", current_vitals['blood_pressure'])
        else:
            st.info("No vitals data yet")
    
    # Footer
    st.markdown("---")
    st.caption(f"🏥 Advanced Clinical Dashboard | Monitoring {len(st.session_state.patients)} Ambulances | "
               f"AI-Powered Clinical Decision Support | Aparavi HIPAA Compliant")
    
    # Auto-refresh
    time.sleep(2)
    st.rerun()


if __name__ == "__main__":
    main()
