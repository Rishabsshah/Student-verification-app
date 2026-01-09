import cv2
import pytesseract
import sys
import os

# Point to the uploaded image that caused issues
# Using the second one because it was the clearest one from the user
img_path = r"C:\Users\Rishab\.gemini\antigravity\brain\5e89ac3d-3e1a-46b5-8404-eb5478ce7e49\uploaded_image_1767967001991.png"

def run_ocr(label, image):
    try:
        text = pytesseract.image_to_string(image)
        print(f"\n--- {label} ---")
        print(text[:300].replace('\n', ' ')) # Print first 300 chars
        return text
    except Exception as e:
        print(f"{label} Failed: {e}")
        return ""

def main():
    if not os.path.exists(img_path):
        print(f"Image not found at {img_path}")
        return

    print(f"Processing: {img_path}")
    original = cv2.imread(img_path)
    
    # Method 1: Original
    run_ocr("Original", original)

    # Method 2: Grayscale
    gray = cv2.cvtColor(original, cv2.COLOR_BGR2GRAY)
    run_ocr("Grayscale", gray)

    # Method 3: Thresholding (Standard)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    run_ocr("Threshold (1x)", thresh)

    # Method 4: Upscale 2x + Threshold (Current Implementation)
    resized = cv2.resize(original, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    gray_res = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    blurred_res = cv2.GaussianBlur(gray_res, (5, 5), 0)
    _, thresh_res = cv2.threshold(blurred_res, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    run_ocr("Threshold (2x)", thresh_res)

    # Method 5: Upscale 2x + Grayscale (No Threshold)
    run_ocr("Grayscale (2x)", gray_res)

if __name__ == "__main__":
    main()
