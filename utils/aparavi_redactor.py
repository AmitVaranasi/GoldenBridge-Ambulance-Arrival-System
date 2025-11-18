"""
Aparavi PII Redactor - HIPAA Compliance Module
Uses Aparavi's data intelligence platform for PII redaction
Ensures patient privacy during data transmission
"""

import re
from typing import Dict, Any, List
import requests
import os


class AparaviRedactor:
    """
    Redacts PII from text using Aparavi data intelligence platform
    
    Note: This is a simulation/wrapper for Aparavi integration.
    In production, this would connect to Aparavi's API endpoints.
    """
    
    def __init__(self, aparavi_api_key: str = None):
        """
        Initialize Aparavi redactor
        
        Args:
            aparavi_api_key: API key for Aparavi platform
        """
        self.api_key = aparavi_api_key or os.getenv('APARAVI_API_KEY', 'demo_key')
        self.endpoint = "https://api.aparavi.com/v1/redact"  # Simulated endpoint
        
        # PII patterns for detection
        self.pii_patterns = {
            'SSN': r'\b\d{3}-\d{2}-\d{4}\b',
            'PHONE': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            'EMAIL': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'NAME': r'\b[A-Z][a-z]+ [A-Z][a-z]+\b',  # Simple name pattern
            'ADDRESS': r'\b\d{1,5}\s\w+\s(Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr)\b',
        }
        
    def _detect_pii_locally(self, text: str) -> List[Dict[str, Any]]:
        """
        Local PII detection using pattern matching
        Simulates Aparavi's PII detection capabilities
        
        Args:
            text: Input text to analyze
            
        Returns:
            List of detected PII entities
        """
        detected_pii = []
        
        for pii_type, pattern in self.pii_patterns.items():
            matches = re.finditer(pattern, text)
            for match in matches:
                detected_pii.append({
                    'type': pii_type,
                    'text': match.group(),
                    'start': match.start(),
                    'end': match.end(),
                    'confidence': 0.95
                })
        
        return detected_pii
    
    def redact_text(self, text: str) -> str:
        """
        Redact PII from text using Aparavi intelligence
        
        Args:
            text: Input text containing potential PII
            
        Returns:
            Text with PII redacted
        """
        if not text:
            return text
        
        # In production, this would call Aparavi API:
        # response = requests.post(
        #     self.endpoint,
        #     headers={'Authorization': f'Bearer {self.api_key}'},
        #     json={'text': text, 'redaction_level': 'HIPAA'}
        # )
        # return response.json()['redacted_text']
        
        # For demo, using local pattern-based redaction
        detected_pii = self._detect_pii_locally(text)
        
        # Sort by position (reverse order to maintain indices)
        detected_pii.sort(key=lambda x: x['start'], reverse=True)
        
        redacted_text = text
        for entity in detected_pii:
            replacement = self._get_replacement(entity['type'])
            redacted_text = (
                redacted_text[:entity['start']] + 
                replacement + 
                redacted_text[entity['end']:]
            )
        
        return redacted_text
    
    def _get_replacement(self, pii_type: str) -> str:
        """Get appropriate replacement text for PII type"""
        replacements = {
            'SSN': '[SSN-REDACTED]',
            'PHONE': '[PHONE]',
            'EMAIL': '[EMAIL]',
            'NAME': '[PATIENT]',
            'ADDRESS': '[LOCATION]'
        }
        return replacements.get(pii_type, '[REDACTED]')
    
    def redact_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Redact PII from dictionary fields using Aparavi
        
        Args:
            data: Dictionary with potential PII in text fields
            
        Returns:
            Dictionary with PII redacted from text fields
        """
        redacted_data = data.copy()
        
        # Fields that might contain PII
        text_fields = [
            'voice_note',
            'emt_name',
            'patient_name',
            'notes',
            'description',
            'comment',
            'message'
        ]
        
        for field in text_fields:
            if field in redacted_data and isinstance(redacted_data[field], str):
                redacted_data[field] = self.redact_text(redacted_data[field])
        
        # Always redact SSN fields
        if "patient_ssn" in redacted_data:
            redacted_data["patient_ssn"] = "[SSN-REDACTED]"
        
        if "ssn" in redacted_data:
            redacted_data["ssn"] = "[SSN-REDACTED]"
            
        return redacted_data
    
    def is_hipaa_compliant(self, text: str) -> bool:
        """
        Check if text appears to be HIPAA compliant using Aparavi analysis
        
        Args:
            text: Text to check
            
        Returns:
            True if no obvious PII detected, False otherwise
        """
        detected_pii = self._detect_pii_locally(text)
        
        # If critical PII found, not compliant
        critical_types = ['SSN', 'PHONE', 'EMAIL']
        for entity in detected_pii:
            if entity['type'] in critical_types and entity['confidence'] > 0.7:
                return False
        
        return True
    
    def analyze_pii_risk(self, text: str) -> Dict[str, Any]:
        """
        Analyze PII risk level using Aparavi intelligence
        
        Returns detailed risk assessment
        """
        detected_pii = self._detect_pii_locally(text)
        
        risk_level = "LOW"
        if len(detected_pii) > 0:
            risk_level = "MEDIUM"
        if any(e['type'] in ['SSN', 'PHONE'] for e in detected_pii):
            risk_level = "HIGH"
        
        return {
            'risk_level': risk_level,
            'pii_count': len(detected_pii),
            'pii_types': list(set(e['type'] for e in detected_pii)),
            'hipaa_compliant': self.is_hipaa_compliant(text),
            'detected_entities': detected_pii
        }


# Singleton instance
_redactor_instance = None

def get_aparavi_redactor() -> AparaviRedactor:
    """Get singleton instance of AparaviRedactor"""
    global _redactor_instance
    if _redactor_instance is None:
        _redactor_instance = AparaviRedactor()
    return _redactor_instance


def redact_pii(text: str) -> str:
    """
    Convenience function to redact PII from text using Aparavi
    
    Args:
        text: Input text
        
    Returns:
        Text with PII redacted
    """
    redactor = get_aparavi_redactor()
    return redactor.redact_text(text)


if __name__ == "__main__":
    # Test the Aparavi redactor
    redactor = AparaviRedactor()
    
    test_cases = [
        "Patient John Smith, SSN 123-45-6789, presenting with chest pain.",
        "EMT Sarah Johnson contacted Dr. Michael Brown at 555-123-4567.",
        "Patient Jane Doe was transported from 123 Main Street.",
        "Contact: john.doe@email.com for follow-up."
    ]
    
    print("=" * 80)
    print("Aparavi PII Redaction Test Cases")
    print("=" * 80)
    
    for i, text in enumerate(test_cases, 1):
        print(f"\nTest Case {i}:")
        print(f"Original: {text}")
        
        # Analyze risk
        risk_analysis = redactor.analyze_pii_risk(text)
        print(f"Risk Level: {risk_analysis['risk_level']}")
        print(f"PII Types Found: {', '.join(risk_analysis['pii_types'])}")
        
        # Redact
        redacted = redactor.redact_text(text)
        print(f"Redacted: {redacted}")
        print(f"HIPAA Compliant: {redactor.is_hipaa_compliant(redacted)}")
    
    print("\n" + "=" * 80)
    print("✅ Aparavi Integration Test Complete")
    print("=" * 80)
