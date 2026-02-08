"""
Razorpay Payment Service for Triple-Lock Verification

This service handles:
- Creating ₹1 verification payment orders
- Verifying payment signatures
- Extracting payer name from payment details (Penny Drop)
- Processing refunds

Razorpay Documentation: https://razorpay.com/docs/
"""

import razorpay
from django.conf import settings
from decouple import config
import logging
import hmac
import hashlib

logger = logging.getLogger(__name__)


class RazorpayVerificationService:
    """
    Service for handling Razorpay payments and verification.
    """
    
    def __init__(self):
        self.key_id = config('RAZORPAY_KEY_ID', default='')
        self.key_secret = config('RAZORPAY_KEY_SECRET', default='')
        self.webhook_secret = config('RAZORPAY_WEBHOOK_SECRET', default='')
        
        if not self.key_id or not self.key_secret:
            logger.warning("Razorpay credentials not configured. Payment verification will not work.")
            self.client = None
        else:
            self.client = razorpay.Client(auth=(self.key_id, self.key_secret))
    
    def create_verification_order(self, user_id, amount=None):
        """
        Create a Razorpay order for ₹1 verification payment.
        
        Args:
            user_id (int): User ID for tracking
            amount (int, optional): Amount in paise (default: 100 = ₹1)
        
        Returns:
            dict: Order details
            {
                'success': True/False,
                'order_id': 'order_xxxxx',
                'amount': 100,
                'currency': 'INR',
                'razorpay_key_id': 'rzp_xxxxx',
                'error': None
            }
        """
        if not self.client:
            return {
                'success': False,
                'order_id': None,
                'error': 'Razorpay not configured'
            }
        
        # Default amount is ₹1 (100 paise)
        if amount is None:
            amount = config('VERIFICATION_AMOUNT', default=100, cast=int)
        
        try:
            order_data = {
                'amount': amount,  # Amount in paise
                'currency': 'INR',
                'receipt': f'verify_{user_id}_{int(__import__("time").time())}',
                'notes': {
                    'purpose': 'Student Verification - Triple Lock',
                    'user_id': str(user_id),
                    'refundable': 'yes'
                }
            }
            
            order = self.client.order.create(data=order_data)
            
            return {
                'success': True,
                'order_id': order['id'],
                'amount': order['amount'],
                'currency': order['currency'],
                'razorpay_key_id': self.key_id,
                'receipt': order['receipt'],
                'notes': order.get('notes', {}),
                'error': None
            }
        
        except razorpay.errors.BadRequestError as e:
            error_msg = str(e)
            logger.error(f"Razorpay Bad Request Error: {error_msg}")
            print(f"DEBUG - Razorpay Error: {error_msg}")  # Console debug
            print(f"DEBUG - Key ID: {self.key_id[:10]}...")  # Show first 10 chars
            return {
                'success': False,
                'order_id': None,
                'error': f'Payment gateway error: {error_msg}'
            }
        
        except razorpay.errors.ServerError as e:
            logger.error(f"Razorpay Server Error: {str(e)}")
            return {
                'success': False,
                'order_id': None,
                'error': 'Payment gateway temporarily unavailable'
            }
        
        except Exception as e:
            logger.error(f"Unexpected error creating order: {str(e)}")
            return {
                'success': False,
                'order_id': None,
                'error': 'Failed to create payment order'
            }
    
    def verify_payment_signature(self, order_id, payment_id, signature):
        """
        Verify Razorpay payment signature to ensure authenticity.
        
        Args:
            order_id (str): Razorpay order ID
            payment_id (str): Razorpay payment ID
            signature (str): Signature from Razorpay
        
        Returns:
            dict: Verification result
            {
                'success': True/False,
                'verified': True/False,
                'error': None
            }
        """
        if not self.client:
            return {
                'success': False,
                'verified': False,
                'error': 'Razorpay not configured'
            }
        
        try:
            # Razorpay signature verification
            params_dict = {
                'razorpay_order_id': order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            }
            
            self.client.utility.verify_payment_signature(params_dict)
            
            return {
                'success': True,
                'verified': True,
                'error': None
            }
        
        except razorpay.errors.SignatureVerificationError:
            logger.warning(f"Invalid signature for payment {payment_id}")
            return {
                'success': False,
                'verified': False,
                'error': 'Invalid payment signature'
            }
        
        except Exception as e:
            logger.error(f"Error verifying signature: {str(e)}")
            return {
                'success': False,
                'verified': False,
                'error': 'Signature verification failed'
            }
    
    def get_payment_details(self, payment_id):
        """
        Fetch payment details including payer name (Penny Drop).
        
        Args:
            payment_id (str): Razorpay payment ID
        
        Returns:
            dict: Payment details with payer name
            {
                'success': True/False,
                'payment_id': 'pay_xxxxx',
                'amount': 100,
                'method': 'upi',
                'payer_name': 'John Doe',
                'vpa': 'john@upi',
                'status': 'captured',
                'error': None
            }
        """
        if not self.client:
            return {
                'success': False,
                'payer_name': None,
                'error': 'Razorpay not configured'
            }
        
        try:
            payment = self.client.payment.fetch(payment_id)
            
            # Extract payer name based on payment method
            payer_name = None
            vpa = None
            
            if payment.get('method') == 'upi':
                vpa = payment.get('vpa', '')
                # Try to get name from acquirer_data
                acquirer_data = payment.get('acquirer_data', {})
                payer_name = acquirer_data.get('payer_name') or acquirer_data.get('upi_payer_name')
                
                # If not in acquirer_data, try from payment notes or VPA
                if not payer_name:
                    # Some payment gateways return name in notes
                    notes = payment.get('notes', {})
                    payer_name = notes.get('payer_name')
            
            elif payment.get('method') == 'netbanking':
                # For netbanking, name might be in bank field
                payer_name = payment.get('bank', '')
            
            elif payment.get('method') == 'card':
                # For card payments, name is on the card
                card = payment.get('card', {})
                payer_name = card.get('name', '')
            
            return {
                'success': True,
                'payment_id': payment['id'],
                'amount': payment['amount'],
                'method': payment.get('method', ''),
                'payer_name': payer_name,
                'vpa': vpa,
                'status': payment.get('status', ''),
                'email': payment.get('email', ''),
                'contact': payment.get('contact', ''),
                'created_at': payment.get('created_at', ''),
                'error': None
            }
        
        except razorpay.errors.BadRequestError:
            logger.error(f"Payment not found: {payment_id}")
            return {
                'success': False,
                'payer_name': None,
                'error': 'Payment not found'
            }
        
        except Exception as e:
            logger.error(f"Error fetching payment details: {str(e)}")
            return {
                'success': False,
                'payer_name': None,
                'error': 'Failed to fetch payment details'
            }
    
    def initiate_refund(self, payment_id, amount=None, notes=None):
        """
        Initiate a refund for the verification payment.
        
        Args:
            payment_id (str): Razorpay payment ID
            amount (int, optional): Amount to refund in paise (None = full refund)
            notes (dict, optional): Additional notes for refund
        
        Returns:
            dict: Refund details
            {
                'success': True/False,
                'refund_id': 'rfnd_xxxxx',
                'amount': 100,
                'status': 'processed',
                'error': None
            }
        """
        if not self.client:
            return {
                'success': False,
                'refund_id': None,
                'error': 'Razorpay not configured'
            }
        
        try:
            refund_data = {
                'speed': 'optimum',  # optimum or normal
            }
            
            if amount is not None:
                refund_data['amount'] = amount
            
            if notes:
                refund_data['notes'] = notes
            else:
                refund_data['notes'] = {
                    'reason': 'Verification complete - Triple Lock',
                    'refund_type': 'Automatic'
                }
            
            refund = self.client.payment.refund(payment_id, refund_data)
            
            return {
                'success': True,
                'refund_id': refund['id'],
                'amount': refund['amount'],
                'payment_id': refund['payment_id'],
                'status': refund.get('status', ''),
                'speed': refund.get('speed_requested', ''),
                'created_at': refund.get('created_at', ''),
                'error': None
            }
        
        except razorpay.errors.BadRequestError as e:
            logger.error(f"Bad request for refund {payment_id}: {str(e)}")
            return {
                'success': False,
                'refund_id': None,
                'error': 'Invalid refund request'
            }
        
        except Exception as e:
            logger.error(f"Error initiating refund: {str(e)}")
            return {
                'success': False,
                'refund_id': None,
                'error': 'Failed to initiate refund'
            }
    
    def verify_webhook_signature(self, payload, signature):
        """
        Verify webhook signature from Razorpay.
        
        Args:
            payload (str): Raw webhook payload
            signature (str): X-Razorpay-Signature header
        
        Returns:
            bool: True if signature is valid
        """
        if not self.webhook_secret:
            logger.warning("Webhook secret not configured")
            return False
        
        try:
            expected_signature = hmac.new(
                self.webhook_secret.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(expected_signature, signature)
        
        except Exception as e:
            logger.error(f"Error verifying webhook signature: {str(e)}")
            return False
