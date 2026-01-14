# Campus Safety - Student Verification System

A Django-based student verification system with ID card OCR, face matching, and liveness detection.

## 🎯 Features

- **ID Card Verification** - OCR extracts enrollment number and college name from student ID cards
- **Face Matching** - Compares selfie against ID card photo using histogram embeddings
- **Liveness Detection** - MediaPipe Face Mesh detects blinks and head turns to prevent photo spoofing
- **Multi-step Signup Flow** - 4-step registration: ID → Account Details → Selfie → Password
- **Admin Review** - Users with low match confidence are flagged for manual verification

## 🛠️ Tech Stack

### Backend
| Technology | Purpose |
|------------|---------|
| Django 5.1 | Web framework |
| Django REST Framework | REST API endpoints |
| SQLite | Database |
| OpenCV | Face detection (Haar Cascades) |
| Pytesseract | OCR for ID card text extraction |
| Pillow | Image processing |

### Frontend
| Technology | Purpose |
|------------|---------|
| HTML/CSS/JavaScript | User interface |
| MediaPipe Face Mesh | Client-side liveness detection |
| HTML5 Camera API | Webcam access |

## 📁 Project Structure

```
Student verification/
├── CampusSafety/           # Main Django project
│   ├── settings.py         # Django settings
│   ├── urls.py             # Root URL configuration
│   └── templates/          # HTML templates
│       └── CampusSafety/
│           ├── id_verification.html
│           ├── account_details.html
│           ├── selfie_check.html
│           ├── signup_final.html
│           ├── login.html
│           └── dashboard.html
├── accounts/               # User authentication app
│   ├── models.py           # Custom User model
│   ├── forms.py            # Registration forms
│   └── views.py            # Auth views
├── verification/           # Verification logic app
│   ├── views.py            # API & page views
│   ├── ocr_utils.py        # OCR & text extraction
│   ├── face_embedding.py   # Face detection & embedding
│   └── urls.py             # API routes
├── media/                  # Uploaded files
├── requirements.txt        # Python dependencies
└── manage.py               # Django CLI
```

## 🚀 Installation

### Prerequisites
- Python 3.11 or 3.12 (recommended)
- Tesseract OCR installed on your system

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd "Student verification"
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   # source .venv/bin/activate  # Linux/Mac
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Tesseract OCR**
   - Windows: Download from [UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki)
   - Add to PATH or set `TESSERACT_CMD` in environment

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create superuser (optional)**
   ```bash
   python manage.py createsuperuser
   ```

7. **Start development server**
   ```bash
   python manage.py runserver
   ```

8. **Access the app**
   - Main: http://127.0.0.1:8000/
   - Admin: http://127.0.0.1:8000/admin/

## 📝 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/verification/inspect-id/` | POST | Upload ID card, extract info, store face embedding |
| `/api/verification/verify-selfie/` | POST | Compare selfie against ID card face |

## 🔐 Verification Flow

1. **Step 1: ID Verification**
   - User uploads student ID card
   - OCR extracts enrollment number and college
   - Face embedding extracted and stored in session

2. **Step 2: Account Details**
   - User enters username and email

3. **Step 3: Selfie Verification**
   - Liveness detection (blink/turn head)
   - Capture selfie frame
   - Compare against ID card face

4. **Step 4: Password Setup**
   - Create account password
   - Account created with verification status

## ⚙️ Configuration

### Environment Variables (optional)
Create a `.env` file in the project root:
```env
SECRET_KEY=your-secret-key-here
DEBUG=True
```

### Supported Colleges
Edit `verification/ocr_utils.py` to add college name patterns:
```python
COLLEGE_PATTERNS = [
    "your university name",
    "college name",
]
```

## 🧪 Testing

```bash
python manage.py test
```

## 📄 License

This project is for educational purposes.

## 👤 Author

Rishab Shah
