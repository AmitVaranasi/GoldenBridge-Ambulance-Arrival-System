"""
AI Triage and Prediction Module
Uses AI to predict patient outcomes and required interventions
"""

from typing import Dict, Any, List
from datetime import datetime
import random


class AITriagePredictor:
    """AI-powered triage and outcome prediction"""
    
    @staticmethod
    def predict_severity(vitals: Dict[str, Any], symptoms: Dict[str, Any], scores: Dict[str, Any]) -> Dict[str, Any]:
        """
        AI Predicted Severity Score (0-100)
        Higher = more critical
        """
        severity_score = 0
        factors = []
        
        # Vital signs analysis
        hr = vitals.get('heart_rate', 70)
        if hr > 120 or hr < 50:
            severity_score += 15
            factors.append('Abnormal Heart Rate')
        
        spo2 = vitals.get('spo2', 98)
        if spo2 < 90:
            severity_score += 20
            factors.append('Critical Hypoxia')
        elif spo2 < 94:
            severity_score += 10
            factors.append('Moderate Hypoxia')
        
        sbp = vitals.get('blood_pressure_systolic', 120)
        if sbp < 90:
            severity_score += 20
            factors.append('Hypotension/Shock')
        
        gcs = vitals.get('gcs', 15)
        if gcs < 9:
            severity_score += 25
            factors.append('Severely Altered Mental Status')
        elif gcs < 13:
            severity_score += 15
            factors.append('Altered Mental Status')
        
        # Symptom analysis
        if symptoms.get('chest_pain'):
            severity_score += 10
            factors.append('Chest Pain')
        
        if symptoms.get('st_elevation'):
            severity_score += 15
            factors.append('ST Elevation')
        
        # Score analysis
        shock_index = scores.get('shock_index', {}).get('value', 0.7)
        if shock_index > 1.0:
            severity_score += 15
            factors.append('Shock State')
        
        # Cap at 100
        severity_score = min(severity_score, 100)
        
        # Determine level
        if severity_score >= 75:
            level = "CRITICAL"
            priority = "Resuscitation"
            color = "🔴"
        elif severity_score >= 50:
            level = "EMERGENT"
            priority = "Immediate"
            color = "🟠"
        elif severity_score >= 25:
            level = "URGENT"
            priority = "Within 30 min"
            color = "🟡"
        else:
            level = "NON-EMERGENT"
            priority = "Standard"
            color = "🟢"
        
        return {
            'score': severity_score,
            'level': level,
            'priority': priority,
            'color': color,
            'contributing_factors': factors
        }
    
    @staticmethod
    def predict_active_alerts(vitals: Dict[str, Any], symptoms: Dict[str, Any], scores: Dict[str, Any]) -> List[str]:
        """
        Predict active clinical alerts
        Returns: List of active alerts (STEMI, Stroke, Trauma, Sepsis, Cardiac Arrest)
        """
        alerts = []
        
        # STEMI Alert
        stemi_score = scores.get('stemi_checklist', {}).get('score', 0)
        if stemi_score >= 3:
            alerts.append('STEMI')
        
        # Stroke Alert
        nihss = scores.get('nihss', {}).get('score', 0)
        if nihss > 7:
            alerts.append('STROKE')
        
        # Trauma Alert
        trauma_score = scores.get('trauma_score', {}).get('score', 7)
        if trauma_score < 5:
            alerts.append('TRAUMA')
        
        # Sepsis Alert
        qsofa = scores.get('qsofa', {}).get('score', 0)
        if qsofa >= 2:
            alerts.append('SEPSIS')
        
        # Cardiac Arrest Risk
        gcs = vitals.get('gcs', 15)
        sbp = vitals.get('blood_pressure_systolic', 120)
        spo2 = vitals.get('spo2', 98)
        
        if gcs < 5 and (sbp < 70 or spo2 < 80):
            alerts.append('CARDIAC_ARREST_RISK')
        
        return alerts
    
    @staticmethod
    def predict_interventions(vitals: Dict[str, Any], symptoms: Dict[str, Any], scores: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict what interventions the patient will need
        """
        predictions = {
            'cardiac_arrest_imminent': False,
            'needs_intubation': False,
            'needs_icu': False,
            'needs_or': False,
            'likely_stroke': False,
            'likely_stemi': False,
            'likely_sepsis': False
        }
        
        confidence_scores = {}
        
        # Cardiac arrest prediction
        gcs = vitals.get('gcs', 15)
        sbp = vitals.get('blood_pressure_systolic', 120)
        if gcs < 5 and sbp < 60:
            predictions['cardiac_arrest_imminent'] = True
            confidence_scores['cardiac_arrest'] = 0.85
        
        # Intubation prediction
        airway_risk = scores.get('airway_risk', {}).get('score', 0)
        if airway_risk >= 4 or gcs < 9:
            predictions['needs_intubation'] = True
            confidence_scores['intubation'] = 0.90
        
        # ICU prediction
        severity = scores.get('severity', {}).get('score', 0)
        if severity >= 60:
            predictions['needs_icu'] = True
            confidence_scores['icu'] = 0.80
        
        # OR prediction
        trauma_score = scores.get('trauma_score', {}).get('score', 7)
        if trauma_score < 4:
            predictions['needs_or'] = True
            confidence_scores['or'] = 0.75
        
        # Stroke prediction
        nihss = scores.get('nihss', {}).get('score', 0)
        if nihss > 7:
            predictions['likely_stroke'] = True
            confidence_scores['stroke'] = 0.85
        
        # STEMI prediction
        stemi_score = scores.get('stemi_checklist', {}).get('score', 0)
        if stemi_score >= 3:
            predictions['likely_stemi'] = True
            confidence_scores['stemi'] = 0.90
        
        # Sepsis prediction
        qsofa = scores.get('qsofa', {}).get('score', 0)
        if qsofa >= 2:
            predictions['likely_sepsis'] = True
            confidence_scores['sepsis'] = 0.75
        
        return {
            'predictions': predictions,
            'confidence_scores': confidence_scores
        }
    
    @staticmethod
    def generate_handoff_summary(patient_data: Dict[str, Any]) -> str:
        """
        AI-generated handoff summary for ED staff
        Extracts key points and flags missing info
        """
        summary_parts = []
        
        # Patient identification
        pid = patient_data.get('patient_id', 'Unknown')
        age = patient_data.get('patient_info', {}).get('age', '?')
        gender = patient_data.get('patient_info', {}).get('gender', '?')
        
        summary_parts.append(f"**PATIENT:** {pid} | {age}yo {gender}")
        
        # Chief complaint
        complaint = patient_data.get('patient_info', {}).get('chief_complaint', 'Not specified')
        summary_parts.append(f"**CHIEF COMPLAINT:** {complaint}")
        
        # Vitals summary
        if patient_data.get('telemetry_history'):
            latest = patient_data['telemetry_history'][-1]
            summary_parts.append(f"**VITALS:** HR {latest['heart_rate']}, BP {latest['blood_pressure']}, SpO2 {latest['spo2']}%")
        
        # Key findings
        if patient_data.get('active_alerts'):
            alerts_str = ', '.join(patient_data['active_alerts'])
            summary_parts.append(f"**ACTIVE ALERTS:** {alerts_str}")
        
        # Severity
        severity = patient_data.get('severity', {})
        if severity:
            summary_parts.append(f"**SEVERITY:** {severity.get('level', 'Unknown')} (Score: {severity.get('score', 0)})")
        
        # Predicted interventions
        predictions = patient_data.get('predictions', {}).get('predictions', {})
        predicted_needs = [k.replace('_', ' ').title() for k, v in predictions.items() if v]
        if predicted_needs:
            summary_parts.append(f"**PREDICTED NEEDS:** {', '.join(predicted_needs)}")
        
        # EMS treatments
        if patient_data.get('ems_treatments'):
            treatments = patient_data['ems_treatments']
            treatment_list = []
            
            # Get medications
            if treatments.get('medications'):
                meds = [m['name'] for m in treatments['medications']]
                treatment_list.extend(meds)
            
            # Get key interventions
            if treatments.get('interventions'):
                interventions = [i['name'] for i in treatments['interventions'][:3]]  # First 3
                treatment_list.extend(interventions)
            
            # Add critical interventions
            if treatments.get('cpr'):
                treatment_list.append('CPR')
            if treatments.get('defibrillation'):
                treatment_list.append('Defibrillation')
            
            if treatment_list:
                summary_parts.append(f"**EMS TREATMENTS:** {', '.join(treatment_list)}")
        
        # Missing info
        missing = []
        if not patient_data.get('patient_info', {}).get('allergies'):
            missing.append('Allergies')
        if not patient_data.get('patient_info', {}).get('medications'):
            missing.append('Medications')
        if missing:
            summary_parts.append(f"⚠️ **MISSING INFO:** {', '.join(missing)}")
        
        # ETA
        eta = patient_data.get('eta', '?')
        summary_parts.append(f"**ETA:** {eta} minutes")
        
        return '\n\n'.join(summary_parts)
    
    @staticmethod
    def activate_protocols(active_alerts: List[str], predictions: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Automatically determine which hospital protocols should be activated
        Returns dictionary of protocol activations with specific actions
        """
        activations = {}
        
        if 'STEMI' in active_alerts or predictions.get('likely_stemi'):
            activations['STEMI_PROTOCOL'] = [
                '🔴 ACTIVATE CATHETER LAB - Door-to-balloon <90 min',
                '📞 Page Interventional Cardiology',
                '💊 Prepare: Aspirin, Clopidogrel, Heparin, Nitroglycerin',
                '🔬 STAT Labs: Troponin, CBC, BMP, Coag panel',
                '🏥 Designate Cath Lab bed'
            ]
        
        if 'STROKE' in active_alerts or predictions.get('likely_stroke'):
            activations['STROKE_PROTOCOL'] = [
                '🔴 ACTIVATE STROKE TEAM',
                '🏥 Reserve CT Scanner immediately',
                '📞 Page Neurology',
                '⏱️ Document Last Known Well time',
                '💊 Prepare tPA if within window',
                '🔬 STAT Labs: CBC, Coag, Glucose'
            ]
        
        if 'TRAUMA' in active_alerts:
            activations['TRAUMA_PROTOCOL'] = [
                '🔴 ACTIVATE TRAUMA TEAM',
                '🏥 Prepare Trauma Bay',
                '📞 Page Surgery, Anesthesia',
                '🩸 Type & Cross, MTP if needed',
                '📍 CT scanner on standby',
                '🏥 Notify OR'
            ]
        
        if 'SEPSIS' in active_alerts or predictions.get('likely_sepsis'):
            activations['SEPSIS_PROTOCOL'] = [
                '🔴 INITIATE SEPSIS BUNDLE',
                '🩸 Blood cultures BEFORE antibiotics',
                '💊 Broad-spectrum antibiotics within 1 hour',
                '💧 Aggressive fluid resuscitation 30ml/kg',
                '🔬 STAT Lactate',
                '🏥 Consider ICU'
            ]
        
        if predictions.get('needs_intubation'):
            activations['AIRWAY_PREP'] = [
                '🔴 PREPARE FOR INTUBATION',
                '📞 Page Anesthesia',
                '🏥 RSI medications ready',
                '💨 Ventilator on standby',
                '🔧 Difficult airway cart available'
            ]
        
        if 'CARDIAC_ARREST_RISK' in active_alerts:
            activations['CODE_BLUE_PREP'] = [
                '🔴 CODE BLUE PREPARATION',
                '🏥 Crash cart at bedside',
                '💊 Emergency medications ready',
                '📞 Rapid response team notified',
                '⚡ Defibrillator ready'
            ]
        
        return activations


if __name__ == "__main__":
    # Test AI triage
    print("AI Triage Module Test")
    print("=" * 60)
    
    predictor = AITriagePredictor()
    
    test_vitals = {
        'heart_rate': 125,
        'blood_pressure_systolic': 85,
        'spo2': 89,
        'gcs': 13,
        'respiratory_rate': 24
    }
    
    test_symptoms = {
        'chest_pain': True,
        'st_elevation': True,
        'diaphoresis': True
    }
    
    test_scores = {
        'stemi_checklist': {'score': 4},
        'shock_index': {'value': 1.47},
        'airway_risk': {'score': 3}
    }
    
    print("\n1. Severity Prediction:")
    severity = predictor.predict_severity(test_vitals, test_symptoms, test_scores)
    print(f"Score: {severity['score']}/100")
    print(f"Level: {severity['color']} {severity['level']}")
    print(f"Priority: {severity['priority']}")
    
    print("\n2. Active Alerts:")
    alerts = predictor.predict_active_alerts(test_vitals, test_symptoms, test_scores)
    print(f"Alerts: {', '.join(alerts)}")
    
    print("\n3. Intervention Predictions:")
    predictions = predictor.predict_interventions(test_vitals, test_symptoms, test_scores)
    print(predictions)
    
    print("\n4. Protocol Activations:")
    protocols = predictor.activate_protocols(alerts, predictions['predictions'])
    for protocol, actions in protocols.items():
        print(f"\n{protocol}:")
        for action in actions:
            print(f"  - {action}")
