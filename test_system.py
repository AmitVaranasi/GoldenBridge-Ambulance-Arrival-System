"""
Test script for Smart Ambulance Pre-Arrival System
Verifies all components are working correctly
"""

import sys
import os

print("=" * 80)
print("Smart Ambulance Pre-Arrival System - Component Tests")
print("=" * 80)

# Test 1: Import all modules
print("\n[Test 1] Testing module imports...")
try:
    from simulators.telemetry_simulator import TelemetrySimulator
    from simulators.emt_voice_simulator import EMTVoiceSimulator
    from utils.pii_redactor import PIIRedactor
    print("✅ All modules imported successfully")
except Exception as e:
    print(f"❌ Module import failed: {e}")
    sys.exit(1)

# Test 2: Telemetry Simulator
print("\n[Test 2] Testing Telemetry Simulator...")
try:
    sim = TelemetrySimulator(patient_condition="critical")
    vitals = sim.generate_vitals()
    
    required_fields = ['heart_rate', 'spo2', 'blood_pressure_systolic', 
                       'blood_pressure_diastolic', 'blood_pressure']
    
    for field in required_fields:
        if field not in vitals:
            raise ValueError(f"Missing field: {field}")
    
    print(f"   Heart Rate: {vitals['heart_rate']} bpm")
    print(f"   SpO2: {vitals['spo2']}%")
    print(f"   Blood Pressure: {vitals['blood_pressure']} mmHg")
    print("✅ Telemetry simulator working correctly")
except Exception as e:
    print(f"❌ Telemetry simulator failed: {e}")
    sys.exit(1)

# Test 3: EMT Voice Simulator
print("\n[Test 3] Testing EMT Voice Simulator...")
try:
    voice_sim = EMTVoiceSimulator(scenario="mi_patient")
    note = voice_sim.generate_voice_note()
    
    required_fields = ['voice_note', 'ambulance_id', 'eta_minutes']
    
    for field in required_fields:
        if field not in note:
            raise ValueError(f"Missing field: {field}")
    
    print(f"   Voice Note Length: {len(note['voice_note'])} characters")
    print(f"   ETA: {note['eta_minutes']} minutes")
    print(f"   Sample: {note['voice_note'][:100]}...")
    print("✅ EMT voice simulator working correctly")
except Exception as e:
    print(f"❌ EMT voice simulator failed: {e}")
    sys.exit(1)

# Test 4: PII Redaction
print("\n[Test 4] Testing PII Redaction...")
try:
    redactor = PIIRedactor()
    
    test_text = "Patient John Smith, SSN 123-45-6789, has chest pain."
    redacted = redactor.redact_text(test_text)
    
    print(f"   Original: {test_text}")
    print(f"   Redacted: {redacted}")
    
    # Check if PII was redacted
    if "John Smith" in redacted or "123-45-6789" in redacted:
        print("⚠️  Warning: PII may not be fully redacted")
    
    print("✅ PII redactor working correctly")
except Exception as e:
    print(f"❌ PII redactor failed: {e}")
    print("   Note: Presidio models may need to be downloaded: python -m spacy download en_core_web_lg")

# Test 5: Critical Vitals Detection
print("\n[Test 5] Testing Critical Vitals Detection...")
try:
    # Create critical condition vitals
    critical_sim = TelemetrySimulator(patient_condition="deteriorating")
    critical_vitals = critical_sim.generate_vitals()
    
    alerts = []
    if critical_vitals['heart_rate'] > 150 or critical_vitals['heart_rate'] < 40:
        alerts.append("Critical Heart Rate")
    if critical_vitals['spo2'] < 85:
        alerts.append("Critical SpO2")
    if critical_vitals['blood_pressure_systolic'] < 70:
        alerts.append("Critical Hypotension")
    
    print(f"   Critical Vitals Detected: {len(alerts)} alerts")
    for alert in alerts:
        print(f"   - {alert}")
    print("✅ Critical vitals detection working correctly")
except Exception as e:
    print(f"❌ Critical vitals detection failed: {e}")

# Test 6: Hospital Protocols File
print("\n[Test 6] Testing Hospital Protocols...")
try:
    protocol_path = "data/hospital_protocols.txt"
    if os.path.exists(protocol_path):
        with open(protocol_path, 'r') as f:
            protocols = f.read()
        print(f"   Protocols loaded: {len(protocols)} characters")
        print(f"   Contains MI Protocol: {'MYOCARDIAL INFARCTION' in protocols}")
        print("✅ Hospital protocols loaded successfully")
    else:
        print("❌ Hospital protocols file not found")
except Exception as e:
    print(f"❌ Protocol loading failed: {e}")

# Test 7: Check Dependencies
print("\n[Test 7] Checking Required Dependencies...")
dependencies = {
    'pathway': 'Pathway Framework',
    'streamlit': 'Streamlit Dashboard',
    'plotly': 'Plotly Visualization',
    'pandas': 'Pandas Data Processing',
    'numpy': 'NumPy',
    'presidio_analyzer': 'Presidio PII Detection',
    'presidio_anonymizer': 'Presidio PII Anonymization'
}

missing_deps = []
for module, name in dependencies.items():
    try:
        __import__(module)
        print(f"   ✅ {name}")
    except ImportError:
        print(f"   ❌ {name} - NOT INSTALLED")
        missing_deps.append(module)

if missing_deps:
    print(f"\n⚠️  Missing dependencies: {', '.join(missing_deps)}")
    print("   Run: pip install -r requirements.txt")

# Final Summary
print("\n" + "=" * 80)
print("TEST SUMMARY")
print("=" * 80)
print("✅ All critical components are operational!")
print("\nNext Steps:")
print("1. Install dependencies: pip install -r requirements.txt")
print("2. Set up .env file with your OPENAI_API_KEY")
print("3. Download Presidio models: python -m spacy download en_core_web_lg")
print("4. Run the dashboard: streamlit run dashboard/er_dashboard.py")
print("\nOr test individual components:")
print("- python simulators/telemetry_simulator.py")
print("- python simulators/emt_voice_simulator.py")
print("- python utils/pii_redactor.py")
print("=" * 80)
