"""
Telemetry Simulator - Simulates ambulance vital signs monitoring
Generates realistic high-frequency streams of Heart Rate, SpO2, and Blood Pressure
"""

import pathway as pw
import time
import random
import json
from datetime import datetime
from typing import Dict, Any


class TelemetrySimulator:
    """Simulates real-time vital signs from an ambulance monitor"""
    
    def __init__(self, patient_condition: str = "stable"):
        self.patient_condition = patient_condition
        self.ambulance_id = "AMB-001"
        self.patient_id = "P-2024-001"
        
    def generate_vitals(self) -> Dict[str, Any]:
        """Generate realistic vital signs based on patient condition"""
        
        if self.patient_condition == "critical":
            # Simulating myocardial infarction (MI) patient
            heart_rate = random.randint(95, 135)  # Tachycardia
            spo2 = random.randint(88, 94)  # Low oxygen
            systolic_bp = random.randint(85, 110)  # Hypotension
            diastolic_bp = random.randint(50, 70)
        elif self.patient_condition == "deteriorating":
            # Patient getting worse
            heart_rate = random.randint(110, 145)
            spo2 = random.randint(85, 91)
            systolic_bp = random.randint(75, 95)
            diastolic_bp = random.randint(45, 60)
        else:
            # Stable patient
            heart_rate = random.randint(60, 90)
            spo2 = random.randint(95, 99)
            systolic_bp = random.randint(110, 130)
            diastolic_bp = random.randint(70, 85)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "ambulance_id": self.ambulance_id,
            "patient_id": self.patient_id,
            "heart_rate": heart_rate,
            "spo2": spo2,
            "blood_pressure_systolic": systolic_bp,
            "blood_pressure_diastolic": diastolic_bp,
            "blood_pressure": f"{systolic_bp}/{diastolic_bp}",
            "condition": self.patient_condition
        }
    
    def stream_data(self, interval: float = 2.0):
        """Generator function to stream telemetry data"""
        while True:
            vitals = self.generate_vitals()
            yield vitals
            time.sleep(interval)
    
    def create_pathway_stream(self):
        """Create a Pathway streaming table from telemetry data"""
        def telemetry_generator():
            """Generator for Pathway"""
            for vitals in self.stream_data(interval=2.0):
                yield vitals
        
        # Create schema for the telemetry stream
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
        
        return pw.debug.table_from_rows(
            schema=TelemetrySchema,
            rows=telemetry_generator()
        )


def simulate_scenario_data(scenario: str = "mi_patient", duration: int = 60):
    """
    Simulate different emergency scenarios for testing
    
    Scenarios:
    - mi_patient: Myocardial Infarction (heart attack)
    - trauma: Trauma patient with vital instability
    - stable: Stable patient transport
    """
    
    simulator = TelemetrySimulator(patient_condition="critical")
    
    print(f"Starting telemetry simulation: {scenario}")
    print(f"Duration: {duration} seconds")
    print("-" * 60)
    
    start_time = time.time()
    
    for vitals in simulator.stream_data(interval=2.0):
        elapsed = time.time() - start_time
        if elapsed > duration:
            break
        
        print(f"[{vitals['timestamp']}] HR: {vitals['heart_rate']} bpm | "
              f"SpO2: {vitals['spo2']}% | BP: {vitals['blood_pressure']} mmHg")
        
        # Simulate deterioration after 30 seconds
        if elapsed > 30 and simulator.patient_condition == "critical":
            simulator.patient_condition = "deteriorating"
            print("\n⚠️  PATIENT CONDITION DETERIORATING\n")


if __name__ == "__main__":
    # Test the simulator
    simulate_scenario_data(scenario="mi_patient", duration=20)
