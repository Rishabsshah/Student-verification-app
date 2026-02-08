"""
Aadhaar Verification Service using API Setu

This service handles Aadhaar verification through the API Setu platform:
- Send OTP to Aadhaar-linked mobile
- Verify OTP and retrieve Aadhaar details
- Parse and structure Aadhaar data

API Setu Documentation: https://docs.setu.co/data/aadhaar-verification
"""

import requests
from django.conf import settings
from decouple import config
import logging

logger = logging.getLogger(__name__)


class AadhaarVerificationService:
    """
    Service for Aadhaar verification via API Setu.
    """
    
    def __init__(self):
        self.client_id = config('API_SETU_CLIENT_ID', default='')
        self.client_secret = config('API_SETU_CLIENT_SECRET', default='')
        self.base_url = config('API_SETU_BASE_URL', default='https://dg-sandbox.setu.co')
        
        if not self.client_id or not self.client_secret:
            logger.warning("API Setu credentials not configured. Aadhaar verification will not work.")
    
    def _get_headers(self):
        """Get API headers with authentication"""
        return {
            'x-client-id': self.client_id,
            'x-client-secret': self.client_secret,
            'Content-Type': 'application/json'
        }
    
    def send_otp(self, aadhaar_number):
        """
        Send OTP to the mobile number linked with Aadhaar.
        
        Args:
            aadhaar_number (str): 12-digit Aadhaar number
        
        Returns:
            dict: Response with request_id for OTP verification
            {
                'success': True/False,
                'request_id': 'unique_request_id',
                'message': 'OTP sent successfully',
                'error': None  # or error message
            }
        """
        # Validate Aadhaar number
        if not aadhaar_number or len(aadhaar_number) != 12 or not aadhaar_number.isdigit():
            return {
                'success': False,
                'request_id': None,
                'message': 'Invalid Aadhaar number. Must be 12 digits.',
                'error': 'INVALID_AADHAAR'
            }
        
        try:
            url = f"{self.base_url}/api/verify/aadhaar/otp"
            payload = {
                'aadhaarNumber': aadhaar_number
            }
            
            response = requests.post(
                url,
                json=payload,
                headers=self._get_headers(),
                timeout=30
            )
            
            data = response.json()
            
            if response.status_code == 200 and data.get('success'):
                return {
                    'success': True,
                    'request_id': data.get('id') or data.get('requestId'),
                    'message': 'OTP sent successfully to your Aadhaar-linked mobile',
                    'error': None
                }
            else:
                error_message = data.get('message') or data.get('error') or 'Failed to send OTP'
                return {
                    'success': False,
                    'request_id': None,
                    'message': error_message,
                    'error': data.get('code') or 'OTP_SEND_FAILED'
                }
        
        except requests.exceptions.Timeout:
            logger.error(f"Timeout while sending OTP for Aadhaar: {aadhaar_number[:4]}****")
            return {
                'success': False,
                'request_id': None,
                'message': 'Request timed out. Please try again.',
                'error': 'TIMEOUT'
            }
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error while sending OTP: {str(e)}")
            return {
                'success': False,
                'request_id': None,
                'message': 'Network error. Please check your connection.',
                'error': 'NETWORK_ERROR'
            }
        
        except Exception as e:
            logger.error(f"Unexpected error in send_otp: {str(e)}")
            return {
                'success': False,
                'request_id': None,
                'message': 'An unexpected error occurred. Please try again.',
                'error': 'UNKNOWN_ERROR'
            }
    
    def verify_otp(self, request_id, otp):
        """
        Verify OTP and retrieve Aadhaar details.
        
        Args:
            request_id (str): Request ID from send_otp
            otp (str): 6-digit OTP entered by user
        
        Returns:
            dict: Aadhaar details if successful
            {
                'success': True/False,
                'data': {
                    'name': 'Full Name',
                    'date_of_birth': '1990-01-01',
                    'gender': 'M/F',
                    'address': {
                        'care_of': 'S/O Father Name',
                        'house': 'House No',
                        'street': 'Street Name',
                        'landmark': 'Near Landmark',
                        'locality': 'Locality',
                        'city': 'City Name',
                        'district': 'District',
                        'state': 'State',
                        'pincode': '123456',
                        'full_address': 'Complete formatted address'
                    }
                },
                'message': 'Verification successful',
                'error': None
            }
        """
        # Validate inputs
        if not request_id:
            return {
                'success': False,
                'data': None,
                'message': 'Invalid request ID',
                'error': 'INVALID_REQUEST_ID'
            }
        
        if not otp or len(otp) != 6 or not otp.isdigit():
            return {
                'success': False,
                'data': None,
                'message': 'Invalid OTP. Must be 6 digits.',
                'error': 'INVALID_OTP'
            }
        
        try:
            url = f"{self.base_url}/api/verify/aadhaar/otp/verify"
            payload = {
                'otp': otp,
                'requestId': request_id
            }
            
            response = requests.post(
                url,
                json=payload,
                headers=self._get_headers(),
                timeout=30
            )
            
            data = response.json()
            
            if response.status_code == 200 and data.get('success'):
                # Parse Aadhaar data
                aadhaar_data = data.get('data', {})
                address_data = aadhaar_data.get('address', {})
                
                # Format full address
                address_parts = [
                    address_data.get('careOf', ''),
                    address_data.get('house', ''),
                    address_data.get('street', ''),
                    address_data.get('landmark', ''),
                    address_data.get('locality', ''),
                    address_data.get('villageTownCity') or address_data.get('city', ''),
                    address_data.get('subDistrict', ''),
                    address_data.get('district', ''),
                    address_data.get('state', ''),
                    address_data.get('pincode', '')
                ]
                full_address = ', '.join([part for part in address_parts if part])
                
                return {
                    'success': True,
                    'data': {
                        'name': aadhaar_data.get('name', ''),
                        'date_of_birth': aadhaar_data.get('dateOfBirth') or aadhaar_data.get('dob', ''),
                        'gender': aadhaar_data.get('gender', ''),
                        'address': {
                            'care_of': address_data.get('careOf', ''),
                            'house': address_data.get('house', ''),
                            'street': address_data.get('street', ''),
                            'landmark': address_data.get('landmark', ''),
                            'locality': address_data.get('locality', ''),
                            'city': address_data.get('villageTownCity') or address_data.get('city', ''),
                            'sub_district': address_data.get('subDistrict', ''),
                            'district': address_data.get('district', ''),
                            'state': address_data.get('state', ''),
                            'pincode': address_data.get('pincode', ''),
                            'full_address': full_address
                        }
                    },
                    'message': 'Aadhaar verified successfully',
                    'error': None
                }
            else:
                error_message = data.get('message') or data.get('error') or 'OTP verification failed'
                return {
                    'success': False,
                    'data': None,
                    'message': error_message,
                    'error': data.get('code') or 'VERIFICATION_FAILED'
                }
        
        except requests.exceptions.Timeout:
            logger.error(f"Timeout while verifying OTP for request: {request_id}")
            return {
                'success': False,
                'data': None,
                'message': 'Request timed out. Please try again.',
                'error': 'TIMEOUT'
            }
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error while verifying OTP: {str(e)}")
            return {
                'success': False,
                'data': None,
                'message': 'Network error. Please check your connection.',
                'error': 'NETWORK_ERROR'
            }
        
        except Exception as e:
            logger.error(f"Unexpected error in verify_otp: {str(e)}")
            return {
                'success': False,
                'data': None,
                'message': 'An unexpected error occurred. Please try again.',
                'error': 'UNKNOWN_ERROR'
            }
    
    def verify_aadhaar_offline(self, aadhaar_xml_file):
        """
        Verify Aadhaar using offline XML (for future implementation).
        This is an alternative method where users can download their
        Aadhaar XML from UIDAI and upload it.
        
        Args:
            aadhaar_xml_file: XML file from UIDAI
        
        Returns:
            dict: Parsed Aadhaar data
        """
        # TODO: Implement offline XML verification
        # This requires XML parsing and signature verification
        raise NotImplementedError("Offline Aadhaar verification not yet implemented")
