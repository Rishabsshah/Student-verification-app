import cv2
import re
import requests
import base64
from typing import Optional, Tuple


COLLEGE_PATTERNS = {
    # Thakur
    "Thakur Polytechnic": r"THAKUR\s*(POLY)?TECHNIC",
    "Thakur College": r"THAKUR\s*COLLEGE",
    "Thakur Institute": r"THAKUR\s*INSTITUTE",


    # Mumbai City
    "A.I. Saboo Siddik Polytechnic": r"SABOO\s*SIDDIK\s*(POLY)?TECHNIC",
    "Government Institute of Printing Technology": r"GOVT.*INSTITUTE.*PRINTING.*TECH",
    "IDEMI Mumbai": r"IDEMI",
    "K.J. Somaiya Polytechnic": r"K\.*\s*J\.*\s*SOMAIYA\s*(POLY)?TECHNIC",
    "L&T Institute of Technology": r"L\s*(&|AND)\s*T\s*INSTITUTE.*TECH",
    "Babasaheb Gawde Institute of Technology": r"BABASAHEB\s*GAWDE\s*INSTITUTE.*TECH",
    "MET Institute of Pharmacy": r"MET\s*INSTITUTE.*PHARMACY|MUMBAI\s*EDUCATIONAL\s*TRUST",
    "Nagrik Shikshan Sanstha Pharmacy": r"NAGRIK\s*SHIKSHAN.*PHARMACY",
    "Sasmira's Institute": r"SASMIRA",
    "Sophia B.K. Somani Polytechnic": r"SOPHIA.*SOMANI\s*(POLY)?TECHNIC",
    "St. Xavier's Technical Institute": r"XAVIER.*TECH",
    "VJTI (Veermata Jijabai)": r"VEERMATA\s*JIJABAI|VJTI",
    "Vidyalankar Polytechnic": r"VIDYALANKAR\s*(POLY)?TECHNIC",
    "VES Polytechnic (Vivekanand)": r"VIVEKANAND.*EDU.*(POLY)?TECHNIC|VES\s*POLYTECHNIC",

    # Mumbai Suburban
    "Abdul Razzak Kalsekar Polytechnic": r"ABDUL\s*RAZZAK|KALSEKAR",
    "Agnel Technical College": r"AGNEL.*TECH",
    "Government Polytechnic Mumbai": r"GOVT.*(POLY)?TECHNIC.*MUMBAI",
    "A.C. Patil College (Jawahar Education)": r"A\.*\s*C\.*\s*PATIL|JAWAHAR.*EDU",
    "Kala Vidya Mandir Institute": r"KALA\s*VIDYA\s*MANDIR",
    "Navjeevan Education Society's Polytechnic": r"NAVJEEVAN",
    "Premlila Vithaldas Polytechnic": r"PREMLILA.*VITHALDAS",
    "Shah and Anchor Kutchhi Polytechnic": r"SHAH.*ANCHOR|KUTCHHI",
    "Shri Bhagubhai Mafatlal Polytechnic": r"BHAGUBHAI.*MAFATLAL",

    # Thane District
    "Agnel Charities Agnel Polytechnic": r"AGNEL\s*CHARITIES|AGNEL\s*(POLY)?TECHNIC",
    "B.R. Harne College of Engineering": r"B\.*\s*R\.*\s*HARNE",
    "Balasaheb Mhatre Polytechnic": r"BALASAHEB\s*MHATRE",
    "Bharati Vidyapeeth Institute of Pharmacy": r"BHARATI\s*VIDYAPEETH.*PHARMACY",
    "Bharati Vidyapeeth Institute of Technology": r"BHARATI\s*VIDYAPEETH.*TECH",
    "Devi Mahalaxmi Polytechnic": r"DEVI\s*MAHALAXMI",
    "Dr. D.Y. Patil Polytechnic": r"D\.*\s*Y\.*\s*PATIL",
    "Dr. Manoj A. Shete College": r"MANOJ\s*.*SHETE",
    "G.E. Society's Katgara Polytechnic": r"KATGARA",
    "Government Polytechnic Vikramgad": r"GOVT.*(POLY)?TECHNIC.*VIKRAMGAD",
    "Government Polytechnic Thane": r"GOVT.*(POLY)?TECHNIC.*THANE",
    "Ideal College of Pharmacy (Kalyan)": r"IDEAL.*PHARMACY.*KALYAN",
    "Ideal Institute of Pharmacy": r"IDEAL.*INSTITUTE.*PHARMACY",
    "Alamuri Ratnamala Institute (Koti Vidya)": r"ALAMURI\s*RATNAMALA|KOTI\s*VIDYA",
    "Muchhala Polytechnic": r"MUCHHALA",
    "NCRD Institute of Pharmacy": r"NCRD",
    "Pravin Patil College": r"PRAVIN\s*PATIL",
    "Prin K.M. Kundnani Pharmacy": r"KUNDNANI",
    "S.H. Jondhale Polytechnic (Samarth Samaj)": r"S\.*\s*H\.*\s*JONDHALE",
    "Shivajirao S. Jondhale Polytechnic": r"SHIVAJIRAO\s*S\.*\s*JONDHALE",
    "Shivgita Institute of Pharmacy": r"SHIVGITA",
    "St. John College of Engineering": r"ST\.*\s*JOHN.*ENG",
    "St. John Institute of Pharmacy": r"ST\.*\s*JOHN.*PHARMACY",
    "Theem College of Engineering": r"THEEM",
    "Vidya Prasarak Mandal's Polytechnic (Thane)": r"VIDYA\s*PRASARAK\s*MANDAL|VPM",
    "Vidyavardhini's Bhausaheb Vartak Polytechnic": r"BHAUSAHEB\s*VARTAK|VIDYAVARDHINI",
    "Vishwatmak Om Gurudev College": r"VISHWATMAK\s*OM\s*GURUDEV",
    "Viva College": r"VIVA",

    # Karjat, Panvel, Raigad
    "B.L. Patil Polytechnic": r"B\.*\s*L\.*\s*PATIL",
    "Bhartiya Education Society Pharmacy": r"BHARTIYA\s*EDU.*PHARMACY",
    "Dilkap Research Institute": r"DILKAP",
    "DBATU (Babasaheb Ambedkar Tech Univ)": r"BATU|AMBEDKAR.*TECH.*UNIV",
    "G.V. Acharya Polytechnic": r"G\.*\s*V\.*\s*ACHARYA",
    "Government Polytechnic Pen": r"GOVT.*(POLY)?TECHNIC.*PEN",
    "Maharashtra Mudran Parishad (Printing Tech)": r"MAHARASHTRA\s*MUDRAN.*PRINTING",
    "Navyug Vidyapeeth Trust": r"NAVYUG",
    "Pillai HOC Polytechnic": r"PILLAI\s*HOC",
    "Prabhakar Patil Education Society": r"PRABHAKAR\s*PATIL",
    "Saraswati Institute of Technology": r"SARASWATI.*TECH",
    "SBNM College of Pharmacy": r"SBNM.*PHARMACY",
    "Shantiniketan Polytechnic": r"SHANTINIKETAN",
    "Sheth Shri Otarmal Sheshmal Parmar College": r"OTARMAL\s*SHESHMAL|PARMAR",
    "Smt Geeta D Tatkare Polytechnic": r"GEETA\s*TATKARE",
    "St. Wilfreds Institute of Pharmacy": r"ST\.*\s*WILFRED.*PHARMACY",
    "Yadavrao Tasgaonkar Institute of Pharmacy": r"TASGAONKAR.*PHARMACY",
    "Yadavrao Tasgaonkar Polytechnic": r"TASGAONKAR.*(POLY)?TECHNIC",
}


def preprocess_image_cloud(image_path: str) -> str:
    """
    Uses OCR.space API for cloud-based OCR (no Tesseract needed).
    Free tier: 25,000 requests/month
    """
    try:
        # OCR.space API endpoint
        url = "https://api.ocr.space/parse/image"
        
        # Free API key (you can get your own at https://ocr.space/ocrapi)
        with open(image_path, 'rb') as image_file:
            payload = {
                'apikey': 'K87899142388957',
                'language': 'eng',
                'isOverlayRequired': 'false',
                'detectOrientation': 'true',
                'scale': 'true',
                'OCREngine': '2'
            }
            files = {'file': image_file}
            
            response = requests.post(url, data=payload, files=files, timeout=30)
        
        # Check if response is valid
        if response.status_code != 200:
            raise Exception(f"API returned status code {response.status_code}")
        
        # Try to parse JSON
        try:
            result = response.json()
        except ValueError:
            raise Exception(f"Invalid API response: {response.text[:200]}")
        
        # Check for errors
        if result.get('IsErroredOnProcessing'):
            error_msgs = result.get('ErrorMessage', [])
            error_msg = error_msgs[0] if error_msgs else 'Unknown error'
            raise Exception(f"OCR API Error: {error_msg}")
        
        # Extract text from all parsed results
        parsed_results = result.get('ParsedResults', [])
        if not parsed_results:
            raise Exception("No text detected in image")
        
        # Combine all detected text
        full_text = '\n'.join([res.get('ParsedText', '') for res in parsed_results])
        
        if not full_text.strip():
            raise Exception("OCR returned empty text - please use a clearer image")
        
        return full_text
        
    except requests.exceptions.Timeout:
        raise Exception("OCR API timeout - please try again")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Network error: {str(e)}")


def normalize_text(text: str) -> str:
    text = text.upper()
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def extract_college_name(text: str) -> Optional[str]:
    # 1. High Confidence: Check against defined patterns
    for college_name, pattern in COLLEGE_PATTERNS.items():
        if re.search(pattern, text, re.IGNORECASE):
            return college_name
            
    # 2. Fallback: Generic detection
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    keywords = ["COLLEGE", "POLYTECHNIC", "INSTITUTE", "UNIVERSITY", "VIDYALAYA", "ACADEMY", "TRUST", "SCHOOL"]
    
    for line in lines:
        upper_line = line.upper()
        
        # Fuzzy check for "TECHNIC" split cases (e.g. "TEC HNIC")
        if "TEC" in upper_line and "HNIC" in upper_line and len(upper_line) < 100:
             return re.sub(r'[|_[\]]', '', line).strip()

        if any(kw in upper_line for kw in keywords):
            # Clean up the line
            cleaned = re.sub(r'[|_[\]]', '', line).strip()
            # Ensure it's long enough and has some letters
            if len(cleaned) > 10 and any(c.isalpha() for c in cleaned):
                return cleaned
                
    return None


def extract_student_name(text: str) -> Optional[str]:
    # 1. Try to find explicit "NAME:" label
    name_match = re.search(r'NAME\s*[:\-]?.?\s*([A-Z\s]+)', text, re.IGNORECASE)
    if name_match:
        # Get the group, clean it up
        raw_name = name_match.group(1).strip()
        # Take the first line of the match if it spans multiple
        return raw_name.split('\n')[0].strip()

    # 2. Fallback Heuristic: Process text line by line
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    candidate_names = []
    
    for line in lines:
        # Skip if line matches college name
        is_college = False
        for college in COLLEGE_PATTERNS.keys():
            words = college.upper().split()
            # Simple check if any main word of college is in line
            if any(w in line.upper() for w in words if len(w) > 3):
                is_college = True
                break
        if is_college:
            continue
            
        # Skip if line looks like enrollment number
        if re.search(r'\d{2}\s*[A-Z]{2,3}\s*\d{3,4}', line):
            continue
            
        # Skip if line is too short (e.g. "ID CARD", "STUDENT")
        if len(line) < 4:
            continue
            
        if "STUDENT" in line.upper() or "IDENTITY" in line.upper() or "CARD" in line.upper() or "BRANCH" in line.upper():
            continue
            
        # If it passed filters, it might be a name
        if any(c.isalpha() for c in line):
            candidate_names.append(line)
            
    if candidate_names:
        return candidate_names[0]
        
    return None


def extract_enrollment_number(text: str) -> Optional[str]:
    # 1. Try explicit label "Enrollment No: ..."
    # Common labels: "Enrollment No", "Enr No", "Roll No", "PRN", "Enrolment No"
    label_match = re.search(r'(Enrollment|Enrolment|Enr|Roll|PRN)\s*(No|Num|Number)?[\s\.\:\-]*([A-Z0-9\s]+)', text, re.IGNORECASE)
    if label_match:
        content = label_match.group(3).strip()
        # Strategy A: Look for the strict pattern in the content
        id_match = re.search(r'\b\d{2}[\sA-Z0-1]{2,5}\s*[0-9OQ]{3,4}\b', content) 
        if id_match:
             clean_id = id_match.group(0).upper().replace('O', '0').replace('Q', '0').replace(' ', '')
             return clean_id
             
        # Strategy B (Fallback): If strict pattern fails, just take the first meaningful alphanumeric word
        # This handles cases where format is different e.g. "2023001" or "ABC-123"
        # We take the first token that has at least 1 digit and length > 3
        tokens = content.split()
        for token in tokens:
            cleaned_token = re.sub(r'[^A-Z0-9]', '', token.upper())
            if len(cleaned_token) > 3 and any(c.isdigit() for c in cleaned_token):
                return cleaned_token

    # 2. Regex designed to capture common OCR errors (Strict Fallback without label):
    # This tries to match the specific college format: XX AA XXXX
    pattern = r'\b(\d{2})[\s\.\-\_]*([A-Z0-1]{2,3})[\s\.\-\_]*([0-9OQ]{3,4})\b'
    
    matches = re.finditer(pattern, text, re.IGNORECASE)
    for match in matches:
        p1, p2, p3 = match.groups()
        p2 = p2.upper()
        p3 = p3.upper().replace('O', '0').replace('Q', '0')
        return f"{p1}{p2}{p3}"

    # 3. Deep Fallback: Generic Numeric Enrollment ID
    # Look for any sequence of 10-14 digits.
    # Prioritize numbers starting with '2' (often year 20xx) or just the longest reasonable one.
    numeric_matches = re.findall(r'\b\d{10,14}\b', text)
    if numeric_matches:
        # Sort by length (descending), then maybe preference for starting with '2'
        # Heuristic: If one starts with '20' or '21' or '22' or '23', it's likely a student ID from recent years.
        for num in numeric_matches:
            if num.startswith(('20', '21', '22', '23', '24', '25')):
                return num
        
        # Otherwise just return the first/longest one
        return max(numeric_matches, key=len)
        
    return None

def verify_student_id(image_path: str) -> Tuple[Optional[str], Optional[str], Optional[str], str]:
    try:
        raw_text = preprocess_image_cloud(image_path)
        normalized_text = normalize_text(raw_text)

        college = extract_college_name(normalized_text)
        enrollment = extract_enrollment_number(normalized_text)
        name = extract_student_name(raw_text)

        # Increased debug length to 500 to catch everything
        status_msg = f"OCR successful. Extracted: {name}, {college}, {enrollment}. Text: {normalized_text[:500]}..."

        return name, college, enrollment, status_msg

    except Exception as e:
        return None, None, None, f"OCR processing failed: {str(e)}"


# --- LEGACY Face Verification Code (NOT USED - Replaced by face_embedding.py) ---
# Commented out for hackathon - using lightweight OpenCV implementation instead

# import numpy as np
# try:
#     import face_recognition
#     FACE_REC_AVAILABLE = True
# except ImportError:
#     FACE_REC_AVAILABLE = False
#     print("Warning: face_recognition library not found. using basic OpenCV fallback.")

# def load_and_encode_face(image_path: str):
#     """
#     LEGACY - NOT USED
#     """
#     pass

# def compare_faces(id_card_path: str, selfie_path: str, tolerance: float = 0.6):
#     """
#     LEGACY - NOT USED
#     This function has been replaced by FaceAnalysisModel in face_embedding.py
#     """
#     pass
