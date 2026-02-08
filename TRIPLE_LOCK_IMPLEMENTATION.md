# 🔐 Triple-Lock Verification System - Implementation Plan

## Overview
A high-security student verification workflow that combines three independent verification methods:
1. **OCR Extraction** - College ID Card verification
2. **Aadhaar Verification** - Government identity verification via API Setu
3. **Financial Identity** - UPI/Bank account verification via Razorpay Penny Drop

## Architecture

### Phase 1: OCR Extraction (EXISTING)
✅ Already implemented using pytesseract and OpenCV
- Extracts: Student Name, Enrollment Number, College Name
- Files: `verification/ocr_utils.py`

### Phase 2: Aadhaar Verification (NEW)
🔨 To be implemented with API Setu
- API: Ministry of Electronics and IT Aadhaar verification
- Returns: Official Name, Address, DOB
- Fuzzy Matching: Compare OCR Name vs Aadhaar Name (>85% similarity)
- Library: `thefuzz` (FuzzyWuzzy)

### Phase 3: Financial Identity Verification (NEW)
🔨 To be implemented with Razorpay
- Payment: ₹1 UPI payment via Razorpay
- Verification: Penny Drop / Smart Collect to get real payer name
- Matching: Compare UPI Payer Name with Aadhaar Name

### Phase 4: Refund & Storage (NEW)
🔨 To be implemented
- Auto-refund ₹1 to student
- Store complete verified profile

## Technical Implementation

### 1. Database Model Extensions

**New Model: `TripleLockVerification`**
```python
class TripleLockVerification(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    # Phase 1: OCR Data
    ocr_name = models.CharField(max_length=255)
    ocr_enrollment = models.CharField(max_length=50)
    ocr_college = models.CharField(max_length=255)
    ocr_verified = models.BooleanField(default=False)
    
    # Phase 2: Aadhaar Data
    aadhaar_number = models.CharField(max_length=12, blank=True, null=True)
    aadhaar_name = models.CharField(max_length=255, blank=True, null=True)
    aadhaar_address = models.TextField(blank=True, null=True)
    aadhaar_dob = models.DateField(blank=True, null=True)
    aadhaar_verified = models.BooleanField(default=False)
    aadhaar_match_score = models.FloatField(blank=True, null=True)
    
    # Phase 3: Financial Data
    razorpay_order_id = models.CharField(max_length=255, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=255, blank=True, null=True)
    upi_id = models.CharField(max_length=255, blank=True, null=True)
    upi_payer_name = models.CharField(max_length=255, blank=True, null=True)
    upi_verified = models.BooleanField(default=False)
    upi_match_score = models.FloatField(blank=True, null=True)
    
    # Overall Status
    verification_status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING_OCR', 'Pending OCR'),
            ('PENDING_AADHAAR', 'Pending Aadhaar'),
            ('PENDING_PAYMENT', 'Pending Payment'),
            ('VERIFIED', 'Fully Verified'),
            ('FAILED', 'Verification Failed'),
        ],
        default='PENDING_OCR'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(blank=True, null=True)
```

**Extended User Model Fields:**
```python
# Add to accounts/models.py User model
aadhaar_number = models.CharField(max_length=12, unique=True, blank=True, null=True)
upi_id = models.CharField(max_length=255, blank=True, null=True)
address = models.TextField(blank=True, null=True)
date_of_birth = models.DateField(blank=True, null=True)
```

### 2. New Services

#### `verification/aadhaar_service.py`
```python
class AadhaarVerificationService:
    """
    Handles Aadhaar verification via API Setu
    """
    def verify_aadhaar(aadhaar_number):
        # Call API Setu Aadhaar verification API
        pass
    
    def send_otp(aadhaar_number):
        # Send OTP for Aadhaar verification
        pass
    
    def verify_otp(aadhaar_number, otp, request_id):
        # Verify OTP and get Aadhaar details
        pass
```

#### `verification/razorpay_service.py`
```python
class RazorpayVerificationService:
    """
    Handles Razorpay payment and Penny Drop verification
    """
    def create_verification_order(amount=100):  # ₹1 in paise
        # Create Razorpay order for ₹1
        pass
    
    def verify_payment(payment_id, order_id, signature):
        # Verify payment signature
        pass
    
    def get_payer_details(payment_id):
        # Get payer name from payment
        pass
    
    def initiate_refund(payment_id):
        # Refund ₹1 to student
        pass
```

#### `verification/fuzzy_matching_service.py`
```python
from thefuzz import fuzz

class FuzzyMatchingService:
    """
    Handles fuzzy string matching for name verification
    """
    @staticmethod
    def match_names(name1, name2, threshold=85):
        """
        Compare two names using fuzzy matching
        Returns: (is_match: bool, score: float)
        """
        # Normalize names
        name1_clean = normalize_name(name1)
        name2_clean = normalize_name(name2)
        
        # Calculate similarity scores
        ratio = fuzz.ratio(name1_clean, name2_clean)
        partial_ratio = fuzz.partial_ratio(name1_clean, name2_clean)
        token_sort_ratio = fuzz.token_sort_ratio(name1_clean, name2_clean)
        
        # Use weighted average
        score = (ratio * 0.4 + partial_ratio * 0.3 + token_sort_ratio * 0.3)
        
        return score >= threshold, score
```

### 3. API Endpoints

#### Phase 2: Aadhaar Verification
```
POST /api/verification/aadhaar/send-otp/
POST /api/verification/aadhaar/verify-otp/
POST /api/verification/aadhaar/verify/
```

#### Phase 3: Payment Verification
```
POST /api/verification/payment/create-order/
POST /api/verification/payment/verify/
POST /api/verification/payment/webhook/
```

#### Combined Flow
```
GET /api/verification/status/
POST /api/verification/complete/
```

### 4. Verification Workflow

```
User Journey:
┌─────────────────────────────────────────────────────┐
│ 1. Upload ID Card → OCR Extraction                  │
│    ✓ Extract: Name, Enrollment, College             │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│ 2. Enter Aadhaar Number → Send OTP                  │
│    ✓ Verify OTP                                     │
│    ✓ Fetch: Aadhaar Name, Address, DOB              │
│    ✓ Fuzzy Match: OCR Name vs Aadhaar Name          │
│    ✗ If match < 85%, REJECT                         │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│ 3. Pay ₹1 via UPI (Razorpay)                        │
│    ✓ Capture Payment                                │
│    ✓ Extract: UPI Payer Name                        │
│    ✓ Fuzzy Match: UPI Name vs Aadhaar Name          │
│    ✗ If match < 85%, REJECT + REFUND                │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│ 4. Success → Auto Refund ₹1                         │
│    ✓ Mark as VERIFIED                               │
│    ✓ Store complete profile                         │
└─────────────────────────────────────────────────────┘
```

### 5. Session State Management

**Django Session Storage:**
```python
# Store verification state in session
request.session['triple_lock_state'] = {
    'ocr_verified': False,
    'aadhaar_verified': False,
    'payment_verified': False,
    'current_phase': 'OCR',
    'ocr_data': {...},
    'aadhaar_data': {...},
    'payment_data': {...}
}
```

**Middleware for Phase Validation:**
```python
class TripleLockPhaseMiddleware:
    """
    Ensures users cannot skip phases
    """
    def __call__(self, request):
        if request.path.startswith('/verification/payment/'):
            state = request.session.get('triple_lock_state', {})
            if not state.get('aadhaar_verified'):
                return redirect('/verification/aadhaar/')
```

## API Integrations

### API Setu (Aadhaar Verification)

**Sandbox Environment:**
- Base URL: `https://dg-sandbox.setu.co`
- Production URL: `https://dg.setu.co`

**Endpoints:**
1. **Generate OTP:**
   ```
   POST /api/verify/aadhaar/otp
   Headers:
     - x-client-id: <YOUR_CLIENT_ID>
     - x-client-secret: <YOUR_CLIENT_SECRET>
   Body:
     {
       "aadhaarNumber": "123456789012"
     }
   ```

2. **Verify OTP:**
   ```
   POST /api/verify/aadhaar/otp/verify
   Body:
     {
       "otp": "123456",
       "requestId": "<REQUEST_ID_FROM_STEP_1>"
     }
   ```

**Response (on success):**
```json
{
  "name": "John Doe",
  "dateOfBirth": "1990-01-01",
  "address": {
    "careOf": "S/O Father Name",
    "house": "House No",
    "street": "Street Name",
    "landmark": "Near Landmark",
    "locality": "Locality",
    "villageTownCity": "City",
    "subDistrict": "Sub District",
    "district": "District",
    "state": "State",
    "pincode": "123456"
  }
}
```

### Razorpay (Payment & Penny Drop)

**API Keys:**
- Key ID: `rzp_test_xxxxx`
- Key Secret: `xxxxx`

**1. Create Order:**
```python
import razorpay
client = razorpay.Client(auth=(key_id, key_secret))

order = client.order.create({
    'amount': 100,  # ₹1 in paise
    'currency': 'INR',
    'receipt': 'verification_order_rcptid_11',
    'notes': {
        'purpose': 'Student Verification',
        'user_id': user.id
    }
})
```

**2. Payment Webhook:**
```python
@csrf_exempt
def razorpay_webhook(request):
    webhook_signature = request.headers.get('X-Razorpay-Signature')
    webhook_secret = settings.RAZORPAY_WEBHOOK_SECRET
    
    # Verify signature
    client.utility.verify_webhook_signature(
        request.body.decode('utf-8'),
        webhook_signature,
        webhook_secret
    )
    
    # Extract payment details
    payment_entity = payload['payment']['entity']
    payer_name = payment_entity['vpa']  # or from payment method
```

**3. Fetch Payment Details (Penny Drop):**
```python
payment = client.payment.fetch(payment_id)
# Extract payer name from:
# - payment['vpa'] for UPI
# - payment['bank'] for netbanking
# - payment['card']['name'] for card
```

**4. Refund:**
```python
refund = client.payment.refund(payment_id, {
    'amount': 100,
    'speed': 'optimum',
    'notes': {
        'reason': 'Verification complete'
    }
})
```

## Security Considerations

1. **Aadhaar Number Storage:**
   - Encrypt Aadhaar numbers at rest
   - Use Django's field-level encryption
   - Never expose Aadhaar in logs or responses

2. **Session Security:**
   - Use secure session cookies
   - Implement CSRF protection
   - Set session timeout (30 minutes)
   - Clear session data after verification

3. **Payment Security:**
   - Verify all Razorpay webhooks with signature
   - Store payment IDs, not sensitive payment data
   - Implement idempotency for refunds

4. **API Key Management:**
   - Store API keys in environment variables
   - Never commit keys to version control
   - Use different keys for sandbox/production

## Dependencies to Add

```txt
# Add to requirements.txt
thefuzz  # Fuzzy string matching
razorpay  # Razorpay payment integration
cryptography  # For Aadhaar encryption
python-decouple  # Environment variable management
```

## Environment Variables

```env
# .env file
# API Setu (Aadhaar)
API_SETU_CLIENT_ID=your_client_id
API_SETU_CLIENT_SECRET=your_client_secret
API_SETU_BASE_URL=https://dg-sandbox.setu.co

# Razorpay
RAZORPAY_KEY_ID=rzp_test_xxxxx
RAZORPAY_KEY_SECRET=xxxxx
RAZORPAY_WEBHOOK_SECRET=xxxxx

# Security
AADHAAR_ENCRYPTION_KEY=your_encryption_key
```

## Testing Strategy

### Phase 1: OCR (Already tested)
✅ Existing

### Phase 2: Aadhaar Verification
- [ ] Test with API Setu sandbox
- [ ] Test fuzzy matching with various name formats
- [ ] Test OTP flow
- [ ] Test error handling

### Phase 3: Payment Verification
- [ ] Test Razorpay test mode
- [ ] Test webhook signature verification
- [ ] Test payer name extraction
- [ ] Test refund flow

### Integration Testing
- [ ] Test complete end-to-end flow
- [ ] Test session state management
- [ ] Test phase skipping prevention
- [ ] Test error recovery

## File Structure

```
verification/
├── models.py (Add TripleLockVerification model)
├── services/
│   ├── __init__.py
│   ├── aadhaar_service.py
│   ├── razorpay_service.py
│   └── fuzzy_matching_service.py
├── views/
│   ├── __init__.py
│   ├── aadhaar_views.py
│   ├── payment_views.py
│   └── triple_lock_views.py
├── middleware/
│   └── phase_validation.py
└── utils/
    ├── encryption.py
    └── name_normalization.py
```

## Next Steps

1. ✅ Create this implementation plan
2. 🔨 Install dependencies
3. 🔨 Extend database models
4. 🔨 Implement Aadhaar service
5. 🔨 Implement Razorpay service
6. 🔨 Implement fuzzy matching service
7. 🔨 Create API endpoints
8. 🔨 Build frontend UI
9. 🔨 Test integration
10. 🔨 Deploy to production

---

**Ready to implement!** 🚀
