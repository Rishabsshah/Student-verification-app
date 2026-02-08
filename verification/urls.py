from django.urls import path
from . import views
from . import triple_lock_views

urlpatterns = [
    # Existing verification endpoints
    path('verify/', views.verify_student, name='verify_student'),
    path('web-verify/', views.web_verify_student, name='web_verify_student'),
    path('inspect-id/', views.inspect_id_card, name='inspect_id_card'),
    path('verify-selfie/', views.verify_selfie, name='verify_selfie'),
    path('id-verification/', views.id_verification_page, name='id_verification_page'),
    path('account-details/', views.account_details_page, name='account_details_page'),
    path('selfie/', views.selfie_check_page, name='selfie_check_page'),
    path('triple-lock/', views.triple_lock_page, name='triple_lock_page'),
    path('signup-final/', views.signup_final_page, name='signup_final_page'),
    
    # Triple-Lock Verification API Endpoints
    # Phase 2: Aadhaar Verification
    path('api/aadhaar/send-otp/', triple_lock_views.aadhaar_send_otp, name='aadhaar_send_otp'),
    path('api/aadhaar/verify-otp/', triple_lock_views.aadhaar_verify_otp, name='aadhaar_verify_otp'),
    
    # Phase 3: Payment Verification
    path('api/payment/create-order/', triple_lock_views.payment_create_order, name='payment_create_order'),
    path('api/payment/verify/', triple_lock_views.payment_verify, name='payment_verify'),
    path('api/payment/webhook/', triple_lock_views.razorpay_webhook, name='razorpay_webhook'),
    
    # Status & Helper
    path('api/status/', triple_lock_views.verification_status, name='verification_status'),
]