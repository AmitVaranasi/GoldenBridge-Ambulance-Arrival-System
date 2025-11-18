"""
Clinical Scoring Module
Calculates standard clinical scores used in emergency medicine
"""

import random
from typing import Dict, Any


class ClinicalScorer:
    """Calculates various clinical scores for emergency triage"""
    
    @staticmethod
    def calculate_nihss(symptoms: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate NIHSS (National Institutes of Health Stroke Scale)
        Score range: 0-42, higher = more severe stroke
        """
        # Simulated based on patient condition
        if symptoms.get('stroke_suspected', False):
            score = random.randint(8, 18)  # Moderate to severe
            interpretation = "Moderate to Severe Stroke" if score > 15 else "Moderate Stroke"
        else:
            score = random.randint(0, 5)
            interpretation = "Minor or No Stroke"
        
        return {
            'score': score,
            'interpretation': interpretation,
            'max_score': 42,
            'recommendation': 'Immediate CT and Neuro consult' if score > 7 else 'Monitor'
        }
    
    @staticmethod
    def calculate_trauma_score(vitals: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate Revised Trauma Score (RTS)
        Components: GCS, SBP, Respiratory Rate
        Score range: 0-7.8408, lower = more severe
        """
        gcs = vitals.get('gcs', 15)
        sbp = vitals.get('blood_pressure_systolic', 120)
        rr = vitals.get('respiratory_rate', 16)
        
        # RTS calculation
        gcs_value = 4 if gcs >= 13 else (3 if gcs >= 9 else (2 if gcs >= 6 else 1))
        sbp_value = 4 if sbp > 89 else (3 if sbp >= 76 else (2 if sbp >= 50 else 1))
        rr_value = 4 if 10 <= rr <= 29 else (3 if rr > 29 else (2 if rr >= 6 else 1))
        
        rts = (0.9368 * gcs_value) + (0.7326 * sbp_value) + (0.2908 * rr_value)
        
        interpretation = "Minor Trauma" if rts > 7 else ("Moderate Trauma" if rts > 5 else "Severe Trauma")
        
        return {
            'score': round(rts, 2),
            'interpretation': interpretation,
            'max_score': 7.84,
            'recommendation': 'Trauma Team Activation' if rts < 5 else 'Standard Trauma Protocol'
        }
    
    @staticmethod
    def calculate_qsofa(vitals: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate qSOFA (Quick Sequential Organ Failure Assessment)
        Used for sepsis screening
        Score range: 0-3, ≥2 suggests sepsis
        """
        score = 0
        criteria = []
        
        # Respiratory rate ≥22
        rr = vitals.get('respiratory_rate', 16)
        if rr >= 22:
            score += 1
            criteria.append('Tachypnea (RR ≥22)')
        
        # Altered mental status (GCS <15)
        gcs = vitals.get('gcs', 15)
        if gcs < 15:
            score += 1
            criteria.append('Altered Mental Status (GCS <15)')
        
        # Systolic BP ≤100
        sbp = vitals.get('blood_pressure_systolic', 120)
        if sbp <= 100:
            score += 1
            criteria.append('Hypotension (SBP ≤100)')
        
        interpretation = "High Sepsis Risk" if score >= 2 else ("Moderate Risk" if score == 1 else "Low Risk")
        
        return {
            'score': score,
            'interpretation': interpretation,
            'max_score': 3,
            'criteria_met': criteria,
            'recommendation': 'Immediate Sepsis Protocol' if score >= 2 else 'Monitor for Sepsis'
        }
    
    @staticmethod
    def calculate_stemi_checklist(symptoms: Dict[str, Any]) -> Dict[str, Any]:
        """
        STEMI Checklist - Indicators of ST-Elevation Myocardial Infarction
        """
        criteria_met = []
        score = 0
        
        if symptoms.get('chest_pain', False):
            criteria_met.append('✓ Chest Pain Present')
            score += 1
        
        if symptoms.get('st_elevation', False):
            criteria_met.append('✓ ST Elevation on ECG')
            score += 2  # Most important
        
        if symptoms.get('diaphoresis', False):
            criteria_met.append('✓ Diaphoresis')
            score += 1
        
        if symptoms.get('nausea', False):
            criteria_met.append('✓ Nausea/Vomiting')
            score += 1
        
        interpretation = "STEMI Likely" if score >= 3 else ("Possible ACS" if score >= 1 else "Unlikely STEMI")
        
        return {
            'score': score,
            'interpretation': interpretation,
            'criteria_met': criteria_met,
            'recommendation': 'Activate Cath Lab Immediately' if score >= 3 else 'Troponin and Monitor'
        }
    
    @staticmethod
    def calculate_airway_risk(vitals: Dict[str, Any], symptoms: Dict[str, Any]) -> Dict[str, Any]:
        """
        Airway Risk Score - Predicts need for intubation
        """
        risk_factors = []
        score = 0
        
        gcs = vitals.get('gcs', 15)
        if gcs < 9:
            risk_factors.append('⚠️ Severely Altered Mental Status (GCS <9)')
            score += 3
        elif gcs < 13:
            risk_factors.append('⚠️ Altered Mental Status (GCS <13)')
            score += 1
        
        spo2 = vitals.get('spo2', 98)
        if spo2 < 88:
            risk_factors.append('⚠️ Severe Hypoxia (SpO2 <88%)')
            score += 2
        elif spo2 < 92:
            risk_factors.append('⚠️ Hypoxia (SpO2 <92%)')
            score += 1
        
        rr = vitals.get('respiratory_rate', 16)
        if rr < 8 or rr > 30:
            risk_factors.append('⚠️ Abnormal Respiratory Rate')
            score += 2
        
        if symptoms.get('airway_obstruction', False):
            risk_factors.append('⚠️ Airway Obstruction Present')
            score += 3
        
        interpretation = "High Risk - Intubate" if score >= 4 else ("Moderate Risk - Prepare" if score >= 2 else "Low Risk")
        
        return {
            'score': score,
            'interpretation': interpretation,
            'risk_factors': risk_factors,
            'recommendation': 'Prepare for Emergency Intubation' if score >= 4 else 'Monitor Airway Closely'
        }
    
    @staticmethod
    def calculate_shock_index(vitals: Dict[str, Any]) -> Dict[str, Any]:
        """
        Shock Index = Heart Rate / Systolic BP
        Normal: 0.5-0.7, >1.0 suggests shock
        """
        hr = vitals.get('heart_rate', 70)
        sbp = vitals.get('blood_pressure_systolic', 120)
        
        if sbp == 0:
            sbp = 1  # Prevent division by zero
        
        shock_index = hr / sbp
        
        if shock_index > 1.0:
            interpretation = "Shock State"
        elif shock_index > 0.9:
            interpretation = "Pre-Shock / Compensated"
        else:
            interpretation = "Normal"
        
        return {
            'value': round(shock_index, 2),
            'interpretation': interpretation,
            'normal_range': '0.5-0.7',
            'recommendation': 'Immediate Resuscitation' if shock_index > 1.0 else 'Monitor'
        }
    
    @staticmethod
    def calculate_deterioration_index(vitals_history: list) -> Dict[str, Any]:
        """
        AI Deterioration Index - Predicts patient worsening
        Analyzes trends in vital signs
        """
        if len(vitals_history) < 3:
            return {
                'score': 0,
                'interpretation': 'Insufficient Data',
                'trend': 'Unknown'
            }
        
        # Analyze last 3 readings
        recent = vitals_history[-3:]
        
        # Check for declining trends
        deterioration_score = 0
        trends = []
        
        # HR trending up
        hr_values = [v['heart_rate'] for v in recent]
        if hr_values[-1] > hr_values[0] + 10:
            deterioration_score += 1
            trends.append('↑ Increasing HR')
        
        # SpO2 trending down
        spo2_values = [v['spo2'] for v in recent]
        if spo2_values[-1] < spo2_values[0] - 3:
            deterioration_score += 2
            trends.append('↓ Decreasing SpO2')
        
        # BP trending down
        bp_values = [v['blood_pressure_systolic'] for v in recent]
        if bp_values[-1] < bp_values[0] - 15:
            deterioration_score += 2
            trends.append('↓ Decreasing BP')
        
        interpretation = "Rapidly Deteriorating" if deterioration_score >= 3 else (
            "Deteriorating" if deterioration_score >= 2 else (
                "Stable" if deterioration_score == 0 else "Concerning Trend"
            )
        )
        
        return {
            'score': deterioration_score,
            'interpretation': interpretation,
            'trends': trends,
            'recommendation': 'Escalate Care Immediately' if deterioration_score >= 3 else 'Monitor Closely'
        }


if __name__ == "__main__":
    # Test clinical scoring
    print("Clinical Scoring Module Test")
    print("=" * 60)
    
    scorer = ClinicalScorer()
    
    # Test vitals
    test_vitals = {
        'heart_rate': 125,
        'blood_pressure_systolic': 88,
        'blood_pressure_diastolic': 55,
        'spo2': 90,
        'respiratory_rate': 24,
        'gcs': 13,
        'temperature': 37.8
    }
    
    # Test symptoms
    test_symptoms = {
        'chest_pain': True,
        'st_elevation': True,
        'diaphoresis': True,
        'nausea': True,
        'stroke_suspected': False
    }
    
    print("\n1. Trauma Score:")
    print(scorer.calculate_trauma_score(test_vitals))
    
    print("\n2. qSOFA (Sepsis):")
    print(scorer.calculate_qsofa(test_vitals))
    
    print("\n3. STEMI Checklist:")
    print(scorer.calculate_stemi_checklist(test_symptoms))
    
    print("\n4. Shock Index:")
    print(scorer.calculate_shock_index(test_vitals))
    
    print("\n5. Airway Risk:")
    print(scorer.calculate_airway_risk(test_vitals, test_symptoms))
