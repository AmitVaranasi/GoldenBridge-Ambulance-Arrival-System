"""
Pipeline package for Smart Ambulance Pre-Arrival System
Contains Pathway-based data processing pipeline
"""

from .ambulance_pipeline import SmartAmbulanceSystem, run_pipeline

__all__ = ['SmartAmbulanceSystem', 'run_pipeline']
