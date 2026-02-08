from django.db import models
from accounts.models import User
from cryptography.fernet import Fernet
from django.conf import settings
import base64


class TripleLockVerification(models.Model):
    """
    Model to track the Triple-Lock verification process:
    1. OCR verification from ID card
    2. Aadhaar verification via API Setu
    3. Financial verification via Razorpay UPI payment
    """
    
    VERIFICATION_STATUS_CHOICES = [
        ('PENDING_OCR', 'Pending OCR'),
        ('PENDING_AADHAAR', 'Pending Aadhaar'),
        ('PENDING_PAYMENT', 'Pending Payment'),
        ('VERIFIED', 'Fully Verified'),
        ('FAILED', 'Verification Failed'),
    ]
    
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE,
        related_name='triple_lock'
    )
    
    # ==================== Phase 1: OCR Data ====================
    ocr_name = models.CharField(max_length=255, blank=True, null=True)
    ocr_enrollment = models.CharField(max_length=50, blank=True, null=True)
    ocr_college = models.CharField(max_length=255, blank=True, null=True)
    ocr_verified = models.BooleanField(default=False)
    ocr_verified_at = models.DateTimeField(blank=True, null=True)
    
    # ==================== Phase 2: Aadhaar Data ====================
    aadhaar_number_encrypted = models.BinaryField(blank=True, null=True)
    aadhaar_name = models.CharField(max_length=255, blank=True, null=True)
    aadhaar_address = models.TextField(blank=True, null=True)
    aadhaar_dob = models.DateField(blank=True, null=True)
    aadhaar_verified = models.BooleanField(default=False)
    aadhaar_match_score = models.FloatField(
        blank=True, 
        null=True,
        help_text="Fuzzy match score between OCR name and Aadhaar name (0-100)"
    )
    aadhaar_verified_at = models.DateTimeField(blank=True, null=True)
    aadhaar_request_id = models.CharField(
        max_length=255, 
        blank=True, 
        null=True,
        help_text="API Setu request ID for OTP verification"
    )
    
    # ==================== Phase 3: Financial Data ====================
    razorpay_order_id = models.CharField(max_length=255, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=255, blank=True, null=True)
    upi_id = models.CharField(max_length=255, blank=True, null=True)
    upi_payer_name = models.CharField(max_length=255, blank=True, null=True)
    upi_verified = models.BooleanField(default=False)
    upi_match_score = models.FloatField(
        blank=True, 
        null=True,
        help_text="Fuzzy match score between Aadhaar name and UPI payer name (0-100)"
    )
    upi_verified_at = models.DateTimeField(blank=True, null=True)
    refund_initiated = models.BooleanField(default=False)
    refund_id = models.CharField(max_length=255, blank=True, null=True)
    refund_status = models.CharField(max_length=50, blank=True, null=True)
    
    # ==================== Overall Status ====================
    verification_status = models.CharField(
        max_length=20,
        choices=VERIFICATION_STATUS_CHOICES,
        default='PENDING_OCR'
    )
    
    # ==================== Timestamps ====================
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    verified_at = models.DateTimeField(
        blank=True, 
        null=True,
        help_text="Timestamp when all three verifications completed"
    )
    
    # ==================== Metadata ====================
    failure_reason = models.TextField(
        blank=True, 
        null=True,
        help_text="Reason for verification failure"
    )
    notes = models.TextField(
        blank=True, 
        null=True,
        help_text="Additional notes or comments"
    )
    
    class Meta:
        verbose_name = "Triple-Lock Verification"
        verbose_name_plural = "Triple-Lock Verifications"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Triple-Lock: {self.user.username} - {self.verification_status}"
    
    # ==================== Aadhaar Encryption Methods ====================
    
    @staticmethod
    def _get_cipher():
        """Get Fernet cipher for encryption/decryption"""
        key = getattr(settings, 'AADHAAR_ENCRYPTION_KEY', None)
        if not key:
            raise ValueError("AADHAAR_ENCRYPTION_KEY not set in settings")
        
        # Ensure key is bytes
        if isinstance(key, str):
            key = key.encode('utf-8')
        
        return Fernet(key)
    
    def set_aadhaar_number(self, aadhaar_number):
        """Encrypt and store Aadhaar number"""
        if aadhaar_number:
            cipher = self._get_cipher()
            encrypted = cipher.encrypt(aadhaar_number.encode('utf-8'))
            self.aadhaar_number_encrypted = encrypted
    
    def get_aadhaar_number(self):
        """Decrypt and return Aadhaar number"""
        if self.aadhaar_number_encrypted:
            cipher = self._get_cipher()
            decrypted = cipher.decrypt(bytes(self.aadhaar_number_encrypted))
            return decrypted.decode('utf-8')
        return None
    
    # ==================== Helper Methods ====================
    
    def get_current_phase(self):
        """Return the current verification phase"""
        if not self.ocr_verified:
            return 1, 'OCR'
        elif not self.aadhaar_verified:
            return 2, 'Aadhaar'
        elif not self.upi_verified:
            return 3, 'Payment'
        else:
            return 4, 'Complete'
    
    def is_fully_verified(self):
        """Check if all three phases are verified"""
        return (
            self.ocr_verified and 
            self.aadhaar_verified and 
            self.upi_verified and
            self.verification_status == 'VERIFIED'
        )
    
    def get_progress_percentage(self):
        """Get verification progress as percentage"""
        phases_completed = sum([
            self.ocr_verified,
            self.aadhaar_verified,
            self.upi_verified
        ])
        return (phases_completed / 3) * 100
    
    def mark_failed(self, reason):
        """Mark verification as failed with reason"""
        self.verification_status = 'FAILED'
        self.failure_reason = reason
        self.save()
