import cv2
import pytesseract
import re
from typing import Optional, Tuple


COLLEGE_PATTERNS = {
    "Thakur Polytechnic": r"THAKUR.*?(POLY)?TECHNIC",
    "ABC College": r"ABC\s*COLLEGE",
    "DEF Institute": r"DEF\s*INSTITUTE",
}


def preprocess_image(image_path: str) -> str:
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError("Invalid image path or unreadable image")

    texts = []

    # Strategy 1: Resized (2x) + Threshold (Good for small text)
    resized = cv2.resize(image, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    gray_res = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    blurred_res = cv2.GaussianBlur(gray_res, (5, 5), 0)
    _, thresh_res = cv2.threshold(blurred_res, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    texts.append(pytesseract.image_to_string(thresh_res))

    # Strategy 2: Original + Grayscale (Good for noisy backgrounds where threshold fails)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    texts.append(pytesseract.image_to_string(gray))

    # Strategy 3: Original + Threshold (Standard)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    texts.append(pytesseract.image_to_string(thresh))

    # Return all texts combined. The extraction logic will scan this large blob.
    return "\n".join(texts)


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
        raw_text = preprocess_image(image_path)
        normalized_text = normalize_text(raw_text)

        college = extract_college_name(normalized_text)
        enrollment = extract_enrollment_number(normalized_text)
        name = extract_student_name(raw_text)

        # Increased debug length to 500 to catch everything
        status_msg = f"OCR successful. Extracted: {name}, {college}, {enrollment}. Text: {normalized_text[:500]}..."

        return name, college, enrollment, status_msg

    except Exception as e:
        return None, None, None, f"OCR processing failed: {str(e)}"
