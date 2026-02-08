from django.contrib import admin
from .models import TripleLockVerification


@admin.register(TripleLockVerification)
class TripleLockVerificationAdmin(admin.ModelAdmin):
    """Admin interface for Triple-Lock verification management"""
    
    list_display = [
        'user',
        'verification_status',
        'ocr_verified',
        'aadhaar_verified',
        'upi_verified',
        'get_progress',
        'created_at',
        'verified_at'
    ]
    
    list_filter = [
        'verification_status',
        'ocr_verified',
        'aadhaar_verified',
        'upi_verified',
        'refund_initiated',
        'created_at'
    ]
    
    search_fields = [
        'user__username',
        'user__email',
        'ocr_name',
        'aadhaar_name',
        'upi_payer_name',
        'razorpay_payment_id',
        'razorpay_order_id'
    ]
    
    readonly_fields = [
        'created_at',
        'updated_at',
        'verified_at',
        'get_aadhaar_number_display',
        'get_progress',
        'get_current_phase_display'
    ]
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'verification_status', 'get_progress', 'get_current_phase_display')
        }),
        ('Phase 1: OCR Verification', {
            'fields': ('ocr_name', 'ocr_enrollment', 'ocr_college', 'ocr_verified', 'ocr_verified_at')
        }),
        ('Phase 2: Aadhaar Verification', {
            'fields': (
                'get_aadhaar_number_display',
                'aadhaar_name',
                'aadhaar_address',
                'aadhaar_dob',
                'aadhaar_verified',
                'aadhaar_match_score',
                'aadhaar_verified_at'
            )
        }),
        ('Phase 3: Payment Verification', {
            'fields': (
                'razorpay_order_id',
                'razorpay_payment_id',
                'upi_id',
                'upi_payer_name',
                'upi_verified',
                'upi_match_score',
                'upi_verified_at',
                'refund_initiated',
                'refund_id',
                'refund_status'
            )
        }),
        ('Metadata', {
            'fields': ('failure_reason', 'notes', 'created_at', 'updated_at', 'verified_at')
        }),
    )
    
    def get_progress(self, obj):
        """Display verification progress as percentage"""
        return f"{obj.get_progress_percentage():.0f}%"
    get_progress.short_description = 'Progress'
    
    def get_current_phase_display(self, obj):
        """Display current verification phase"""
        phase_num, phase_name = obj.get_current_phase()
        return f"Phase {phase_num}: {phase_name}"
    get_current_phase_display.short_description = 'Current Phase'
    
    def get_aadhaar_number_display(self, obj):
        """Display masked Aadhaar number"""
        aadhaar = obj.get_aadhaar_number()
        if aadhaar:
            return f"{'*' * 8}{aadhaar[-4:]}"
        return "Not provided"
    get_aadhaar_number_display.short_description = 'Aadhaar Number'
