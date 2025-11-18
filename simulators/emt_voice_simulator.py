"""
EMT Voice/Text Simulator - Simulates transcribed voice notes from EMTs
Generates realistic medical reports and updates during transport
"""

import pathway as pw
import time
import random
from datetime import datetime
from typing import Dict, Any, List


class EMTVoiceSimulator:
    """Simulates transcribed voice notes from Emergency Medical Technicians"""
    
    def __init__(self, scenario: str = "mi_patient"):
        self.scenario = scenario
        self.ambulance_id = "AMB-001"
        self.patient_id = "P-2024-001"
        self.emt_name = "John Smith"  # Contains PII - will be redacted
        self.patient_name = "Sarah Johnson"  # Contains PII - will be redacted
        self.patient_ssn = "123-45-6789"  # Contains PII - will be redacted
        self.eta_minutes = 8
        
        # Pre-defined voice notes for different scenarios
        self.mi_scenario_notes = [
            f"This is EMT {self.emt_name} from ambulance {self.ambulance_id}. We have a 58-year-old female patient {self.patient_name}, SSN {self.patient_ssn}, presenting with severe chest pain radiating to the left arm. Patient reports history of angina and hypertension. ETA 8 minutes.",
            f"Update on patient {self.patient_name}. Chest pain started approximately 45 minutes ago. Patient describes it as crushing pressure. Administered aspirin 325mg and started oxygen at 4L. Vitals show tachycardia and hypotension.",
            f"Patient is experiencing diaphoresis and nausea. Strong suspicion of myocardial infarction. Patient states her father died of heart attack at age 62. Currently on nitroglycerin from personal medication. Request cardiology team standby.",
            f"ETA now 4 minutes. Patient {self.patient_name} remains conscious but in significant distress. Pain level 8 out of 10. ST elevation noted on 12-lead ECG. This appears to be an acute MI. Recommend immediate catheter lab prep.",
            f"Two minutes out. Patient condition stable but critical. Nitroglycerin providing minimal relief. IV established. All documentation will be transferred upon arrival. Catheter lab should be ready."
        ]
        
        self.trauma_scenario_notes = [
            f"EMT {self.emt_name} reporting. Motor vehicle collision victim, {self.patient_name}, SSN {self.patient_ssn}. Multiple trauma, suspected internal bleeding. Patient is semi-conscious. ETA 10 minutes.",
            f"Patient has visible trauma to chest and abdomen. Possible rib fractures. Blood pressure dropping. Started two large bore IVs with normal saline. Rapid transport initiated.",
            f"Update: Patient becoming more unstable. Signs of shock developing. Increased fluid resuscitation. Surgery team should be notified immediately. ETA 5 minutes."
        ]
        
        self.current_note_index = 0
        
    def get_scenario_notes(self) -> List[str]:
        """Get voice notes based on scenario"""
        if self.scenario == "mi_patient":
            return self.mi_scenario_notes
        elif self.scenario == "trauma":
            return self.trauma_scenario_notes
        else:
            return self.mi_scenario_notes
    
    def generate_voice_note(self) -> Dict[str, Any]:
        """Generate the next voice note in the sequence"""
        notes = self.get_scenario_notes()
        
        if self.current_note_index >= len(notes):
            # Cycle back or return final update
            note_text = f"Final update: Arriving at hospital now. Patient {self.patient_name} ready for immediate transfer to ER team."
        else:
            note_text = notes[self.current_note_index]
            self.current_note_index += 1
        
        return {
            "timestamp": datetime.now().isoformat(),
            "ambulance_id": self.ambulance_id,
            "patient_id": self.patient_id,
            "emt_name": self.emt_name,
            "voice_note": note_text,
            "note_type": "voice_transcription",
            "eta_minutes": max(0, self.eta_minutes - (self.current_note_index * 2))
        }
    
    def stream_data(self, interval: float = 15.0):
        """Generator function to stream voice notes at intervals"""
        while True:
            if self.current_note_index <= len(self.get_scenario_notes()):
                voice_note = self.generate_voice_note()
                yield voice_note
                time.sleep(interval)
            else:
                break
    
    def create_pathway_stream(self):
        """Create a Pathway streaming table from voice notes"""
        def voice_generator():
            """Generator for Pathway"""
            for note in self.stream_data(interval=15.0):
                yield note
        
        # Create schema for the voice notes stream
        class VoiceNoteSchema(pw.Schema):
            timestamp: str
            ambulance_id: str
            patient_id: str
            emt_name: str
            voice_note: str
            note_type: str
            eta_minutes: int
        
        return pw.debug.table_from_rows(
            schema=VoiceNoteSchema,
            rows=voice_generator()
        )


def simulate_voice_notes(scenario: str = "mi_patient", duration: int = 90):
    """
    Simulate EMT voice notes for testing
    
    Scenarios:
    - mi_patient: Myocardial Infarction patient
    - trauma: Trauma patient
    """
    
    simulator = EMTVoiceSimulator(scenario=scenario)
    
    print(f"Starting EMT voice note simulation: {scenario}")
    print(f"Duration: {duration} seconds")
    print("=" * 80)
    
    start_time = time.time()
    
    for note_data in simulator.stream_data(interval=15.0):
        elapsed = time.time() - start_time
        if elapsed > duration:
            break
        
        print(f"\n[{note_data['timestamp']}]")
        print(f"EMT: {note_data['emt_name']}")
        print(f"ETA: {note_data['eta_minutes']} minutes")
        print(f"Voice Note: {note_data['voice_note']}")
        print("-" * 80)


if __name__ == "__main__":
    # Test the simulator
    simulate_voice_notes(scenario="mi_patient", duration=80)
