# 🔐 Triple-Lock Verification System - Usage Guide

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Generate Encryption Key

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Copy the output and add to your `.env` file.

### 3. Configure Environment Variables

Create a `.env` file in your project root (use `.env.example` as template):

```env
# Django Settings
SECRET_KEY=your-secret-key
DEBUG=True

# API Setu (Aadhaar)
API_SETU_CLIENT_ID=your_client_id
API_SETU_CLIENT_SECRET=your_client_secret
API_SETU_BASE_URL=https://dg-sandbox.setu.co

# Razorpay
RAZORPAY_KEY_ID=rzp_test_xxxxx
RAZORPAY_KEY_SECRET=your_key_secret
RAZORPAY_WEBHOOK_SECRET=your_webhook_secret

# Security
AADHAAR_ENCRYPTION_KEY=your_generated_key_from_step_2

# Verification Settings
FUZZY_MATCH_THRESHOLD=85
VERIFICATION_AMOUNT=100
```

### 4. Update Django Settings

Add to `CampusSafety/settings.py`:

```python
from decouple import config
from cryptography.fernet import Fernet

# Load environment variables
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)

# Aadhaar encryption key
AADHAAR_ENCRYPTION_KEY = config('AADHAAR_ENCRYPTION_KEY').encode('utf-8')

# Session settings (important for multi-step verification)
SESSION_COOKIE_AGE = 1800  # 30 minutes
SESSION_SAVE_EVERY_REQUEST = True
SESSION_COOKIE_SECURE = not DEBUG  # True in production
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
```

### 5. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Create Superuser (if needed)

```bash
python manage.py createsuperuser
```

### 7. Run Development Server

```bash
python manage.py runserver
```

---

## 🔄 Complete Verification Workflow

### Phase 1: OCR Verification (Existing)

**Endpoint:** `POST /verification/inspect-id/`

The student uploads their college ID card. The system:
1. Extracts: Name, Enrollment Number, College Name
2. Stores in session
3. Returns a session token for next steps

```javascript
// Example API call
const formData = new FormData();
formData.append('id_card', fileInput.files[0]);

fetch('/verification/inspect-id/', {
    method: 'POST',
    body: formData
})
.then(response => response.json())
.then(data => {
    if (data.success) {
        const sessionToken = data.session_token;
        const ocrData = data.ocr_data;
        // Proceed to Aadhaar verification
    }
});
```

---

### Phase 2: Aadhaar Verification

#### Step 2A: Send OTP

**Endpoint:** `POST /verification/api/aadhaar/send-otp/`

```javascript
fetch('/verification/api/aadhaar/send-otp/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        session_token: sessionToken,
        aadhaar_number: '123456789012'
    })
})
.then(response => response.json())
.then(data => {
    if (data.success) {
        const requestId = data.request_id;
        // Show OTP input form
    } else {
        console.error(data.error);
    }
});
```

#### Step 2B: Verify OTP

**Endpoint:** `POST /verification/api/aadhaar/verify-otp/`

```javascript
fetch('/verification/api/aadhaar/verify-otp/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        session_token: sessionToken,
        otp: '123456'
    })
})
.then(response => response.json())
.then(data => {
    if (data.success && data.matched) {
        console.log('Aadhaar verified! Match score:', data.match_score);
        // Proceed to payment
    } else {
        console.error('Name mismatch:', data.error);
    }
});
```

---

### Phase 3: Payment Verification

#### Step 3A: Create Razorpay Order

**Endpoint:** `POST /verification/api/payment/create-order/`

```javascript
fetch('/verification/api/payment/create-order/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        session_token: sessionToken
    })
})
.then(response => response.json())
.then(data => {
    if (data.success) {
        // Initialize Razorpay checkout
        initiateRazorpayPayment(data);
    }
});
```

#### Step 3B: Process Payment with Razorpay

```javascript
function initiateRazorpayPayment(orderData) {
    const options = {
        key: orderData.razorpay_key_id,
        amount: orderData.amount,
        currency: orderData.currency,
        order_id: orderData.order_id,
        name: 'Student Verification',
        description: 'Triple-Lock Verification - ₹1 (Will be refunded)',
        handler: function(response) {
            // Payment successful, verify it
            verifyPayment(response);
        },
        prefill: {
            name: ocrData.name,
            email: userEmail,
            contact: userPhone
        },
        theme: {
            color: '#3399cc'
        }
    };
    
    const rzp = new Razorpay(options);
    rzp.open();
}
```

#### Step 3C: Verify Payment

**Endpoint:** `POST /verification/api/payment/verify/`

```javascript
function verifyPayment(razorpayResponse) {
    fetch('/verification/api/payment/verify/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            session_token: sessionToken,
            razorpay_payment_id: razorpayResponse.razorpay_payment_id,
            razorpay_order_id: razorpayResponse.razorpay_order_id,
            razorpay_signature: razorpayResponse.razorpay_signature
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success && data.verification_complete) {
            console.log('✓ All verification complete!');
            console.log('✓ Refund initiated:', data.refund_id);
            // Registration successful
            proceedToAccountCreation();
        } else {
            console.error('Payment verification failed:', data.error);
        }
    });
}
```

---

### Check Verification Status

**Endpoint:** `GET /verification/api/status/?session_token=xxx`

```javascript
fetch(`/verification/api/status/?session_token=${sessionToken}`)
.then(response => response.json())
.then(data => {
    console.log('Current Phase:', data.current_phase);
    console.log('Progress:', data.progress + '%');
    console.log('OCR Verified:', data.ocr_verified);
    console.log('Aadhaar Verified:', data.aadhaar_verified);
    console.log('Payment Verified:', data.payment_verified);
});
```

---

## 🧪 Testing

### Testing with Sandbox Credentials

#### API Setu (Sandbox)
- Use sandbox URL: `https://dg-sandbox.setu.co`
- Test Aadhaar: Get from API Setu documentation
- OTP: Usually `123456` in sandbox

#### Razorpay (Test Mode)
- Use test keys: `rzp_test_xxxxx`
- Test cards: Any card from [Razorpay Test Cards](https://razorpay.com/docs/payments/payments/test-card-details/)
- Test UPI: Use `success@razorpay` for successful payment

### Manual Testing Steps

1. **Test OCR Phase:**
   ```bash
   # Upload a clear ID card image
   # Verify extracted data is correct
   ```

2. **Test Aadhaar Phase:**
   ```bash
   # Enter test Aadhaar number
   # Receive OTP (check sandbox docs)
   # Verify OTP
   # Check fuzzy matching score
   ```

3. **Test Payment Phase:**
   ```bash
   # Create payment order
   # Use test UPI/card
   # Complete payment
   # Verify payer name extraction
   # Check refund initiation
   ```

---

## 🎨 Frontend Integration Example

### Complete HTML/JavaScript Example

```html
<!DOCTYPE html>
<html>
<head>
    <title>Triple-Lock Verification</title>
    <script src="https://checkout.razorpay.com/v1/checkout.js"></script>
</head>
<body>
    <div id="app">
        <!-- Phase 1: ID Card Upload -->
        <div id="phase1">
            <h2>Step 1: Upload ID Card</h2>
            <input type="file" id="idCard" accept="image/*">
            <button onclick="uploadID()">Upload</button>
        </div>

        <!-- Phase 2: Aadhaar Verification -->
        <div id="phase2" style="display:none;">
            <h2>Step 2: Aadhaar Verification</h2>
            <input type="text" id="aadhaar" placeholder="Enter 12-digit Aadhaar">
            <button onclick="sendOTP()">Send OTP</button>
            
            <div id="otpSection" style="display:none;">
                <input type="text" id="otp" placeholder="Enter 6-digit OTP">
                <button onclick="verifyOTP()">Verify OTP</button>
            </div>
        </div>

        <!-- Phase 3: Payment -->
        <div id="phase3" style="display:none;">
            <h2>Step 3: Financial Verification</h2>
            <p>Pay ₹1 to verify your identity (will be refunded immediately)</p>
            <button onclick="initiatePayment()">Pay ₹1</button>
        </div>

        <!-- Success -->
        <div id="success" style="display:none;">
            <h2>✓ Verification Complete!</h2>
            <p>All three verifications passed. Your ₹1 has been refunded.</p>
        </div>
    </div>

    <script>
        let sessionToken = null;
        let orderData = null;

        async function uploadID() {
            const file = document.getElementById('idCard').files[0];
            const formData = new FormData();
            formData.append('id_card', file);

            const response = await fetch('/verification/inspect-id/', {
                method: 'POST',
                body: formData
            });
            const data = await response.json();
            
            if (data.success) {
                sessionToken = data.session_token;
                document.getElementById('phase1').style.display = 'none';
                document.getElementById('phase2').style.display = 'block';
            }
        }

        async function sendOTP() {
            const aadhaar = document.getElementById('aadhaar').value;
            
            const response = await fetch('/verification/api/aadhaar/send-otp/', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({session_token: sessionToken, aadhaar_number: aadhaar})
            });
            const data = await response.json();
            
            if (data.success) {
                document.getElementById('otpSection').style.display = 'block';
                alert('OTP sent to your Aadhaar-linked mobile');
            }
        }

        async function verifyOTP() {
            const otp = document.getElementById('otp').value;
            
            const response = await fetch('/verification/api/aadhaar/verify-otp/', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({session_token: sessionToken, otp: otp})
            });
            const data = await response.json();
            
            if (data.success && data.matched) {
                document.getElementById('phase2').style.display = 'none';
                document.getElementById('phase3').style.display = 'block';
                alert(`Names matched! Score: ${data.match_score}%`);
            } else {
                alert('Verification failed: ' + data.error);
            }
        }

        async function initiatePayment() {
            const response = await fetch('/verification/api/payment/create-order/', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({session_token: sessionToken})
            });
            orderData = await response.json();
            
            if (orderData.success) {
                const options = {
                    key: orderData.razorpay_key_id,
                    amount: orderData.amount,
                    currency: orderData.currency,
                    order_id: orderData.order_id,
                    name: 'Student Verification',
                    description: 'Triple-Lock Verification (₹1 - Refundable)',
                    handler: async function(response) {
                        await verifyPayment(response);
                    }
                };
                const rzp = new Razorpay(options);
                rzp.open();
            }
        }

        async function verifyPayment(razorpayResponse) {
            const response = await fetch('/verification/api/payment/verify/', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    session_token: sessionToken,
                    razorpay_payment_id: razorpayResponse.razorpay_payment_id,
                    razorpay_order_id: razorpayResponse.razorpay_order_id,
                    razorpay_signature: razorpayResponse.razorpay_signature
                })
            });
            const data = await response.json();
            
            if (data.success && data.verification_complete) {
                document.getElementById('phase3').style.display = 'none';
                document.getElementById('success').style.display = 'block';
            } else {
                alert('Payment verification failed: ' + data.error);
            }
        }
    </script>
</body>
</html>
```

---

## 📊 Admin Dashboard

Access the admin panel at: `http://localhost:8000/admin/`

Navigate to **Verification > Triple-Lock Verifications** to see:
- All verification records
- Current phase for each user
- Match scores
- Payment and refund status
- Filterable by status, dates, etc.

---

## 🔒 Security Best Practices

1. **Never log Aadhaar numbers** - They are encrypted in database
2. **Use HTTPS in production** - Enable SSL/TLS
3. **Rotate API keys regularly** - Update keys every 90 days
4. **Monitor webhook calls** - Check for suspicious activity
5. **Implement rate limiting** - Prevent abuse
6. **Session timeout** - 30 minutes default
7. **Verify webhook signatures** - Always validate Razorpay webhooks

---

## 🐛 Troubleshooting

### Common Issues

#### 1. "Aadhaar encryption key not set"
**Solution:** Generate and add `AADHAAR_ENCRYPTION_KEY` to `.env`

#### 2. "Razorpay not configured"
**Solution:** Add Razorpay credentials to `.env`

#### 3. "Name mismatch" (Low match score)
**Solution:** Adjust `FUZZY_MATCH_THRESHOLD` in `.env` (lower to 75-80 for testing)

#### 4. "Cannot extract payer name"
**Solution:** Ensure UPI payment method is used (not card/netbanking in sandbox)

#### 5. Session expired
**Solution:** Increase `SESSION_COOKIE_AGE` in settings.py

---

## 📝 API Reference

See `TRIPLE_LOCK_IMPLEMENTATION.md` for complete API documentation.

---

## 🚀 Production Deployment

### Before deploying to production:

1. Switch to production APIs:
   ```env
   API_SETU_BASE_URL=https://dg.setu.co
   RAZORPAY_KEY_ID=rzp_live_xxxxx
   ```

2. Enable security settings:
   ```python
   DEBUG = False
   SESSION_COOKIE_SECURE = True
   CSRF_COOKIE_SECURE = True
   ```

3. Set up Razorpay webhook:
   - Go to Razorpay Dashboard > Webhooks
   - Add: `https://yourdomain.com/verification/api/payment/webhook/`
   - Events: `payment.captured`, `refund.processed`

4. Test thoroughly with real data

---

## ✅ Verification Flow Summary

```
┌─────────────────────────────────────────┐
│  1. Upload ID Card                       │
│     → OCR extracts Name, Enrollment      │
└─────────────┬───────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│  2. Enter Aadhaar → Send OTP             │
│     → Verify OTP                         │
│     → Match OCR Name vs Aadhaar Name     │
│     → Threshold: 85%                     │
└─────────────┬───────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│  3. Pay ₹1 via UPI                       │
│     → Extract Payer Name                 │
│     → Match Aadhaar Name vs Payer Name   │
│     → Threshold: 85%                     │
└─────────────┬───────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│  ✓ All Verified!                         │
│     → Auto-refund ₹1                     │
│     → Create user account                │
└─────────────────────────────────────────┘
```

---

**Happy Verifying! 🎉**

For issues or questions, check the main implementation document: `TRIPLE_LOCK_IMPLEMENTATION.md`
