"""
PII Redactor - HIPAA Compliance Module
Uses Presidio for automatic redaction of Personal Identifiable Information
Ensures patient privacy during data transmission
"""

import re
from typing import Dict, Any
from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig


class PIIRedactor:
    """Redacts PII from text for HIPAA compliance"""
    
    def __init__(self):
        # Initialize Presidio engines
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()
        
        # Add custom recognizers for medical contexts
        self._add_custom_recognizers()
        
    def _add_custom_recognizers(self):
        """Add custom pattern recognizers for medical data"""
        
        # SSN pattern recognizer (enhanced)
        ssn_pattern = Pattern(
            name="ssn_pattern",
            regex=r"\b\d{3}-\d{2}-\d{4}\b",
            score=0.9
        )
        
        ssn_recognizer = PatternRecognizer(
            supported_entity="US_SSN",
            patterns=[ssn_pattern]
        )
        
        self.analyzer.registry.add_recognizer(ssn_recognizer)
    
    def redact_text(self, text: str) -> str:
        """
        Redact PII from text
        
        Args:
            text: Input text containing potential PII
            
        Returns:
            Text with PII redacted
        """
        if not text:
            return text
        
        # Analyze text for PII
        results = self.analyzer.analyze(
            text=text,
            language="en",
            entities=[
                "PERSON",
                "US_SSN",
                "PHONE_NUMBER",
                "EMAIL_ADDRESS",
                "MEDICAL_LICENSE",
                "US_DRIVER_LICENSE",
                "CREDIT_CARD",
                "IBAN_CODE",
                "IP_ADDRESS",
                "DATE_TIME",
                "LOCATION",
                "US_PASSPORT"
            ]
        )
        
        # Anonymize the text
        anonymized = self.anonymizer.anonymize(
            text=text,
            analyzer_results=results,
            operators={
                "PERSON": OperatorConfig("replace", {"new_value": "[PATIENT]"}),
                "US_SSN": OperatorConfig("replace", {"new_value": "[SSN-REDACTED]"}),
                "PHONE_NUMBER": OperatorConfig("replace", {"new_value": "[PHONE]"}),
                "EMAIL_ADDRESS": OperatorConfig("replace", {"new_value": "[EMAIL]"}),
                "MEDICAL_LICENSE": OperatorConfig("replace", {"new_value": "[LICENSE]"}),
                "US_DRIVER_LICENSE": OperatorConfig("replace", {"new_value": "[DL]"}),
                "LOCATION": OperatorConfig("replace", {"new_value": "[LOCATION]"}),
                "DEFAULT": OperatorConfig("replace", {"new_value": "[REDACTED]"})
            }
        )
        
        return anonymized.text
    
    def redact_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Redact PII from dictionary fields
        
        Args:
            data: Dictionary with potential PII in text fields
            
        Returns:
            Dictionary with PII redacted from text fields
        """
        redacted_data = data.copy()
        
        # Fields that might contain PII
        text_fields = [
            "voice_note",
            "emt_name",
            "patient_name",
            "notes",
            "description",
            "comment"
        ]
        
        for field in text_fields:
            if field in redacted_data and isinstance(redacted_data[field], str):
                redacted_data[field] = self.redact_text(redacted_data[field])
        
        # Always redact SSN if present as separate field
        if "patient_ssn" in redacted_data:
            redacted_data["patient_ssn"] = "[SSN-REDACTED]"
        
        if "ssn" in redacted_data:
            redacted_data["ssn"] = "[SSN-REDACTED]"
            
        return redacted_data
    
    def is_hipaa_compliant(self, text: str) -> bool:
        """
        Check if text appears to be HIPAA compliant (no obvious PII)
        
        Args:
            text: Text to check
            
        Returns:
            True if no obvious PII detected, False otherwise
        """
        results = self.analyzer.analyze(
            text=text,
            language="en",
            entities=["PERSON", "US_SSN", "PHONE_NUMBER", "EMAIL_ADDRESS"]
        )
        
        # If critical PII found, not compliant
        critical_entities = ["US_SSN", "PHONE_NUMBER", "EMAIL_ADDRESS"]
        for result in results:
            if result.entity_type in critical_entities and result.score > 0.7:
                return False
        
        return True


# Singleton instance
_redactor_instance = None

def get_redactor() -> PIIRedactor:
    """Get singleton instance of PIIRedactor"""
    global _redactor_instance
    if _redactor_instance is None:
        _redactor_instance = PIIRedactor()
    return _redactor_instance


def redact_pii(text: str) -> str:
    """
    Convenience function to redact PII from text
    
    Args:
        text: Input text
        
    Returns:
        Text with PII redacted
    """
    redactor = get_redactor()
    return redactor.redact_text(text)


if __name__ == "__main__":
    # Test the redactor
    redactor = PIIRedactor()
    
    test_cases = [
        "Patient John Smith, SSN 123-45-6789, presenting with chest pain.",
        "EMT Sarah Johnson contacted Dr. Michael Brown at 555-123-4567.",
        "Patient Jane Doe was transported from 123 Main Street.",
    ]
    
    print("PII Redaction Test Cases")
    print("=" * 80)
    
    for i, text in enumerate(test_cases, 1):
        print(f"\nTest Case {i}:")
        print(f"Original: {text}")
        redacted = redactor.redact_text(text)
        print(f"Redacted: {redacted}")
        print(f"HIPAA Compliant: {redactor.is_hipaa_compliant(redacted)}")
