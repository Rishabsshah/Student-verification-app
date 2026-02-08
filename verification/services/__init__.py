"""
Verification Services

This package contains services for the Triple-Lock verification system:
- FuzzyMatchingService: Name matching across verification phases
- AadhaarVerificationService: Aadhaar verification via API Setu
- RazorpayVerificationService: Payment and Penny Drop verification
"""

from .fuzzy_matching_service import FuzzyMatchingService
from .aadhaar_service import AadhaarVerificationService
from .razorpay_service import RazorpayVerificationService

__all__ = [
    'FuzzyMatchingService',
    'AadhaarVerificationService',
    'RazorpayVerificationService',
]
