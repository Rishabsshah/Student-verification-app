from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser for Campus Safety application.

    This model ensures that only verified students can log in and prevents duplicate
    student accounts by enforcing uniqueness on enrollment numbers.
    """

    # Choices for verification status
    VERIFICATION_STATUS_CHOICES = [
        ('VERIFIED', 'Verified'),
        ('REVIEW', 'Under Review'),
        ('REJECTED', 'Rejected'),
    ]

    # Enrollment number to uniquely identify students and prevent duplicate accounts
    # Initially nullable to allow signup before OCR verification
    enrollment_number = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        help_text="Unique student enrollment number, verified via OCR"
    )

    # Verification status to control login access
    # Only VERIFIED students can log in
    verification_status = models.CharField(
        max_length=20,
        choices=VERIFICATION_STATUS_CHOICES,
        default='REVIEW',
        help_text="Current verification status of the student"
    )
    
    # Custom Hash for duplicate detection (Name + Enrollment + College)
    identity_hash = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        help_text="Hash of student details to prevent duplicate registrations"
    )

    # Phone number (mandatory, 10 digits)
    phone_number = models.CharField(
        max_length=10,
        null=True,
        blank=True,
        help_text="Student's 10-digit phone number"
    )


    # Selfie for manual review
    selfie_image = models.ImageField(
        upload_to='student_selfies/',
        null=True,
        blank=True,
        help_text="Captured video selfie for admin review"
    )

    # Triple-Lock Verification Fields
    upi_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Student's UPI ID for financial verification"
    )
    
    address = models.TextField(
        null=True,
        blank=True,
        help_text="Student's address from Aadhaar"
    )
    
    date_of_birth = models.DateField(
        null=True,
        blank=True,
        help_text="Student's date of birth from Aadhaar"
    )


    def __str__(self):
        return f"{self.username} ({self.enrollment_number or 'No enrollment'})"

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
