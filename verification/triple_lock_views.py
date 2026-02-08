"""
Triple-Lock Verification API Views

This module provides API endpoints for the three-phase verification workflow:
1. Phase 1: OCR verification (already exists in views.py)
2. Phase 2: Aadhaar verification
3. Phase 3: Payment verification
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
import logging

from verification.models import TripleLockVerification
from verification.services import (
    FuzzyMatchingService,
    AadhaarVerificationService,
    RazorpayVerificationService
)
from accounts.models import User
from decouple import config

logger = logging.getLogger(__name__)


# ==================== Phase 2: Aadhaar Verification ====================

@api_view(['POST'])
@permission_classes([AllowAny])
def aadhaar_send_otp(request):
    """
    Send OTP to Aadhaar-linked mobile number.
    
    Request Body:
        {
            "session_token": "temp_verification_token",
            "aadhaar_number": "123456789012"
        }
    
    Response:
        {
            "success": true,
            "request_id": "unique_request_id",
            "message": "OTP sent successfully",
            "masked_mobile": "******1234"
        }
    """
    try:
        session_token = request.data.get('session_token')
        aadhaar_number = request.data.get('aadhaar_number', '').strip()
        
        if not session_token or not aadhaar_number:
            return Response({
                'success': False,
                'error': 'session_token and aadhaar_number are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get session data
        session_data = request.session.get('triple_lock_state', {})
        
        if session_data.get('session_token') != session_token:
            return Response({
                'success': False,
                'error': 'Invalid or expired session'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Check if OCR is verified
        if not session_data.get('ocr_verified'):
            return Response({
                'success': False,
                'error': 'Please complete ID card verification first'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # HACKATHON MODE: Bypass actual API call
        hackathon_mode = config('HACKATHON_MODE', default=False, cast=bool)
        if hackathon_mode:
            # Store mock request_id in session
            session_data['aadhaar_request_id'] = 'DEMO_REQUEST_ID_' + aadhaar_number[-4:]
            session_data['aadhaar_number'] = aadhaar_number
            request.session['triple_lock_state'] = session_data
            request.session.modified = True
            
            return Response({
                'success': True,
                'request_id': session_data['aadhaar_request_id'],
                'message': '🎯 DEMO MODE: OTP sent successfully (any 6-digit code will work)',
                'masked_mobile': '******' + aadhaar_number[-4:]
            }, status=status.HTTP_200_OK)
        
        # Send OTP via Aadhaar service
        aadhaar_service = AadhaarVerificationService()
        result = aadhaar_service.send_otp(aadhaar_number)
        
        if result['success']:
            # Store request_id in session
            session_data['aadhaar_request_id'] = result['request_id']
            session_data['aadhaar_number'] = aadhaar_number  # Store temporarily
            request.session['triple_lock_state'] = session_data
            request.session.modified = True
            
            return Response({
                'success': True,
                'request_id': result['request_id'],
                'message': result['message'],
                'masked_mobile': '******' + aadhaar_number[-4:]  # Mask for privacy
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'error': result['message']
            }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        logger.error(f"Error in aadhaar_send_otp: {str(e)}")
        return Response({
            'success': False,
            'error': 'An unexpected error occurred'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def aadhaar_verify_otp(request):
    """
    Verify OTP and complete Aadhaar verification.
    
    Request Body:
        {
            "session_token": "temp_verification_token",
            "otp": "123456"
        }
    
    Response:
        {
            "success": true,
            "match_score": 92.5,
            "matched": true,
            "message": "Aadhaar verified successfully",
            "aadhaar_data": {
                "name": "John Doe",
                "dob": "1990-01-01",
                "address": "..."
            }
        }
    """
    try:
        session_token = request.data.get('session_token')
        otp = request.data.get('otp', '').strip()
        
        if not session_token or not otp:
            return Response({
                'success': False,
                'error': 'session_token and otp are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get session data
        session_data = request.session.get('triple_lock_state', {})
        
        if session_data.get('session_token') != session_token:
            return Response({
                'success': False,
                'error': 'Invalid or expired session'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        request_id = session_data.get('aadhaar_request_id')
        aadhaar_number = session_data.get('aadhaar_number')
        ocr_name = session_data.get('ocr_data', {}).get('name')
        
        if not request_id or not ocr_name:
            return Response({
                'success': False,
                'error': 'Session data incomplete. Please start again.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # HACKATHON MODE: Accept any OTP
        hackathon_mode = config('HACKATHON_MODE', default=False, cast=bool)
        if hackathon_mode:
            # Simulate successful Aadhaar verification
            aadhaar_name = ocr_name  # Use OCR name for perfect match
            match_score = 100.0  # Perfect match in demo mode
            
            # Store Aadhaar data in session
            session_data['aadhaar_verified'] = True
            session_data['aadhaar_data'] = {
                'name': aadhaar_name,
                'dob': '1990-01-01',  # Mock DOB
                'address': 'Demo Address, Demo City, Demo State - 123456',  # Mock address
                'match_score': match_score
            }
            session_data['current_phase'] = 'PAYMENT'
            request.session['triple_lock_state'] = session_data
            request.session.modified = True
            
            return Response({
                'success': True,
                'matched': True,
                'match_score': match_score,
                'message': '🎯 DEMO MODE: Aadhaar verified successfully',
                'aadhaar_data': {
                    'name': aadhaar_name,
                    'dob': '1990-01-01',
                    'address': 'Demo Address, Demo City, Demo State - 123456'
                },
                'next_step': 'payment'
            }, status=status.HTTP_200_OK)
        
        # Verify OTP and get Aadhaar data
        aadhaar_service = AadhaarVerificationService()
        result = aadhaar_service.verify_otp(request_id, otp)
        
        if not result['success']:
            return Response({
                'success': False,
                'error': result['message']
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Extract Aadhaar data
        aadhaar_data = result['data']
        aadhaar_name = aadhaar_data['name']
        
        # Perform fuzzy matching between OCR name and Aadhaar name
        fuzzy_threshold = config('FUZZY_MATCH_THRESHOLD', default=85, cast=int)
        is_match, match_score, match_details = FuzzyMatchingService.match_names(
            ocr_name,
            aadhaar_name,
            threshold=fuzzy_threshold
        )
        
        if not is_match:
            return Response({
                'success': False,
                'matched': False,
                'match_score': match_score,
                'ocr_name': ocr_name,
                'aadhaar_name': aadhaar_name,
                'error': f'Name mismatch. OCR: {ocr_name}, Aadhaar: {aadhaar_name}',
                'message': f'Names do not match sufficiently (Score: {match_score}%, Required: {fuzzy_threshold}%)'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Success! Store Aadhaar data in session
        session_data['aadhaar_verified'] = True
        session_data['aadhaar_data'] = {
            'name': aadhaar_name,
            'dob': aadhaar_data['date_of_birth'],
            'address': aadhaar_data['address']['full_address'],
            'match_score': match_score
        }
        session_data['current_phase'] = 'PAYMENT'
        request.session['triple_lock_state'] = session_data
        request.session.modified = True
        
        return Response({
            'success': True,
            'matched': True,
            'match_score': match_score,
            'message': 'Aadhaar verified successfully',
            'aadhaar_data': {
                'name': aadhaar_name,
                'dob': aadhaar_data['date_of_birth'],
                'address': aadhaar_data['address']['full_address']
            },
            'next_step': 'payment'
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Error in aadhaar_verify_otp: {str(e)}")
        return Response({
            'success': False,
            'error': 'An unexpected error occurred'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== Phase 3: Payment Verification ====================

@api_view(['POST'])
@permission_classes([AllowAny])
def payment_create_order(request):
    """
    Create Razorpay order for ₹1 verification payment.
    
    Request Body:
        {
            "session_token": "temp_verification_token"
        }
    
    Response:
        {
            "success": true,
            "order_id": "order_xxxxx",
            "amount": 100,
            "currency": "INR",
            "razorpay_key_id": "rzp_xxxxx"
        }
    """
    try:
        session_token = request.data.get('session_token')
        
        if not session_token:
            return Response({
                'success': False,
                'error': 'session_token is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get session data
        session_data = request.session.get('triple_lock_state', {})
        
        if session_data.get('session_token') != session_token:
            return Response({
                'success': False,
                'error': 'Invalid or expired session'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Check if Aadhaar is verified
        if not session_data.get('aadhaar_verified'):
            return Response({
                'success': False,
                'error': 'Please complete Aadhaar verification first'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create Razorpay order
        razorpay_service = RazorpayVerificationService()
        user_id = session_data.get('user_id', 0)
        result = razorpay_service.create_verification_order(user_id)
        
        if result['success']:
            # Store order ID in session
            session_data['razorpay_order_id'] = result['order_id']
            request.session['triple_lock_state'] = session_data
            request.session.modified = True
            
            return Response({
                'success': True,
                'order_id': result['order_id'],
                'amount': result['amount'],
                'currency': result['currency'],
                'razorpay_key_id': result['razorpay_key_id']
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'error': result['error']
            }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        logger.error(f"Error in payment_create_order: {str(e)}")
        return Response({
            'success': False,
            'error': 'An unexpected error occurred'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def payment_verify(request):
    """
    Verify payment and complete Triple-Lock verification.
    
    Request Body:
        {
            "session_token": "temp_verification_token",
            "razorpay_payment_id": "pay_xxxxx",
            "razorpay_order_id": "order_xxxxx",
            "razorpay_signature": "signature_xxxxx"
        }
    
    Response:
        {
            "success": true,
            "matched": true,
            "match_score": 88.5,
            "verification_complete": true,
            "message": "All verifications complete!",
            "refund_initiated": true
        }
    """
    try:
        session_token = request.data.get('session_token')
        payment_id = request.data.get('razorpay_payment_id')
        order_id = request.data.get('razorpay_order_id')
        signature = request.data.get('razorpay_signature')
        
        if not all([session_token, payment_id, order_id, signature]):
            return Response({
                'success': False,
                'error': 'All payment details are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get session data
        session_data = request.session.get('triple_lock_state', {})
        
        if session_data.get('session_token') != session_token:
            return Response({
                'success': False,
                'error': 'Invalid or expired session'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Verify payment signature
        razorpay_service = RazorpayVerificationService()
        verification = razorpay_service.verify_payment_signature(order_id, payment_id, signature)
        
        if not verification['verified']:
            return Response({
                'success': False,
                'error': 'Payment verification failed'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get payment details to extract payer name
        payment_details = razorpay_service.get_payment_details(payment_id)
        
        if not payment_details['success']:
            return Response({
                'success': False,
                'error': 'Could not fetch payment details'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        payer_name = payment_details.get('payer_name')
        
        # HACKATHON MODE: Simulate payer name if not available in test mode
        hackathon_mode = config('HACKATHON_MODE', default=False, cast=bool)
        if not payer_name and hackathon_mode:
            # In test mode, use Aadhaar name for perfect match simulation
            aadhaar_name = session_data.get('aadhaar_data', {}).get('name')
            payer_name = aadhaar_name  # Simulate perfect match
            logger.info(f"HACKATHON MODE: Simulated payer name as '{payer_name}'")
        
        if not payer_name:
            return Response({
                'success': False,
                'error': 'Could not extract payer name from payment. Payment method may not support this feature.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Match UPI payer name with Aadhaar name
        aadhaar_name = session_data.get('aadhaar_data', {}).get('name')
        fuzzy_threshold = config('FUZZY_MATCH_THRESHOLD', default=85, cast=int)
        
        is_match, match_score, match_details = FuzzyMatchingService.match_names(
            aadhaar_name,
            payer_name,
            threshold=fuzzy_threshold
        )
        
        # Store payment data
        session_data['payment_verified'] = is_match
        session_data['payment_data'] = {
            'payment_id': payment_id,
            'payer_name': payer_name,
            'vpa': payment_details.get('vpa'),
            'match_score': match_score
        }
        
        if not is_match:
            # Initiate refund even on failure
            razorpay_service.initiate_refund(payment_id)
            
            request.session['triple_lock_state'] = session_data
            request.session.modified = True
            
            return Response({
                'success': False,
                'matched': False,
                'match_score': match_score,
                'aadhaar_name': aadhaar_name,
                'payer_name': payer_name,
                'error': f'Payer name mismatch. Aadhaar: {aadhaar_name}, UPI: {payer_name}',
                'message': f'Names do not match sufficiently (Score: {match_score}%, Required: {fuzzy_threshold}%)',
                'refund_initiated': True
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # SUCCESS! All three phases verified
        session_data['verification_complete'] = True
        session_data['current_phase'] = 'COMPLETE'
        request.session['triple_lock_state'] = session_data
        request.session.modified = True
        
        # Initiate refund
        refund_result = razorpay_service.initiate_refund(payment_id)
        
        return Response({
            'success': True,
            'matched': True,
            'match_score': match_score,
            'verification_complete': True,
            'message': 'All verification steps completed successfully!',
            'refund_initiated': refund_result['success'],
            'refund_id': refund_result.get('refund_id')
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Error in payment_verify: {str(e)}")
        return Response({
            'success': False,
            'error': 'An unexpected error occurred'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== Razorpay Webhook ====================

@csrf_exempt
def razorpay_webhook(request):
    """
    Handle Razorpay webhooks for payment events.
    
    This is called by Razorpay when payment status changes.
    Use for additional processing or logging.
    """
    try:
        if request.method != 'POST':
            return JsonResponse({'error': 'Invalid method'}, status=405)
        
        # Verify webhook signature
        signature = request.headers.get('X-Razorpay-Signature', '')
        payload = request.body.decode('utf-8')
        
        razorpay_service = RazorpayVerificationService()
        is_valid = razorpay_service.verify_webhook_signature(payload, signature)
        
        if not is_valid:
            logger.warning("Invalid webhook signature")
            return JsonResponse({'error': 'Invalid signature'}, status=401)
        
        # Parse webhook data
        data = json.loads(payload)
        event = data.get('event')
        
        logger.info(f"Received webhook event: {event}")
        
        # Handle different events
        if event == 'payment.captured':
            payment_entity = data.get('payload', {}).get('payment', {}).get('entity', {})
            payment_id = payment_entity.get('id')
            logger.info(f"Payment captured: {payment_id}")
        
        elif event == 'refund.processed':
            refund_entity = data.get('payload', {}).get('refund', {}).get('entity', {})
            refund_id = refund_entity.get('id')
            logger.info(f"Refund processed: {refund_id}")
        
        return JsonResponse({'success': True})
    
    except Exception as e:
        logger.error(f"Error in razorpay_webhook: {str(e)}")
        return JsonResponse({'error': 'Internal error'}, status=500)


# ==================== Status & Helper Endpoints ====================

@api_view(['GET'])
@permission_classes([AllowAny])
def verification_status(request):
    """
    Get current verification status from session.
    
    Query Params:
        session_token: Session token
    
    Response:
        {
            "current_phase": "AADHAAR",
            "ocr_verified": true,
            "aadhaar_verified": false,
            "payment_verified": false,
            "progress": 33.33
        }
    """
    try:
        session_token = request.GET.get('session_token')
        
        if not session_token:
            return Response({
                'success': False,
                'error': 'session_token is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        session_data = request.session.get('triple_lock_state', {})
        
        if session_data.get('session_token') != session_token:
            return Response({
                'success': False,
                'error': 'Invalid or expired session'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Calculate progress
        phases_completed = sum([
            session_data.get('ocr_verified', False),
            session_data.get('aadhaar_verified', False),
            session_data.get('payment_verified', False)
        ])
        progress = (phases_completed / 3) * 100
        
        return Response({
            'success': True,
            'current_phase': session_data.get('current_phase', 'OCR'),
            'ocr_verified': session_data.get('ocr_verified', False),
            'aadhaar_verified': session_data.get('aadhaar_verified', False),
            'payment_verified': session_data.get('payment_verified', False),
            'verification_complete': session_data.get('verification_complete', False),
            'progress': round(progress, 2)
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Error in verification_status: {str(e)}")
        return Response({
            'success': False,
            'error': 'An unexpected error occurred'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
