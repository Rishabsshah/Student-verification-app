"""
Simple face verification using OpenCV + Histogram comparison.
Fast, lightweight, perfect for hackathon prototype!
"""
import cv2
import numpy as np
import os

class FaceAnalysisModel:
    """
    Simple face recognition using OpenCV's Haar Cascade + Histogram comparison.
    No heavy ML models needed - fast and works offline!
    """
    
    # Load Haar Cascade for face detection
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    @classmethod
    def get_embedding(cls, image_path):
        """
        Extract face region and compute color histogram as "embedding".
        Returns (histogram_array, message)
        
        Args:
            image_path: Path to the image file
            
        Returns:
            tuple: (histogram array or None, status message)
        """
        try:
            # Check if file exists
            if not os.path.exists(image_path):
                return None, f"Image file not found: {image_path}"
            
            # Read image
            img = cv2.imread(image_path)
            if img is None:
                return None, "Could not read image file"
            
            # Convert to grayscale for face detection
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Detect faces - EXTREMELY LENIENT settings for hackathon demo
            # These settings prioritize detection over accuracy
            faces = cls.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.05,   # LOWERED from 1.1 - detects at more scales
                minNeighbors=2,     # LOWERED from 3 - even more lenient
                minSize=(15, 15),   # LOWERED from 20x20 - detects very small faces
                flags=cv2.CASCADE_SCALE_IMAGE
            )
            
            if len(faces) == 0:
                # 🎯 HACKATHON FALLBACK: If no face detected, use center crop of image
                # This ensures the demo ALWAYS works, even with challenging conditions
                print("Warning: No face detected by Haar Cascade. Using center crop fallback.")
                
                h, w = img.shape[:2]
                # Take center 60% of image (where face usually is)
                crop_size = min(h, w) * 0.6
                center_x, center_y = w // 2, h // 2
                x1 = int(center_x - crop_size // 2)
                y1 = int(center_y - crop_size // 2)
                x2 = int(center_x + crop_size // 2)
                y2 = int(center_y + crop_size // 2)
                
                # Ensure bounds
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(w, x2), min(h, y2)
                
                face_region = img[y1:y2, x1:x2]
                
                if face_region.size == 0:
                    return None, "Could not extract face region from image"
                
                print(f"Using center crop fallback: {face_region.shape}")
            else:
                # Face detected - use it
                if len(faces) > 1:
                    print(f"Warning: {len(faces)} faces detected, using the largest")
                    # Sort by area (w*h) and take largest
                    faces = sorted(faces, key=lambda f: f[2]*f[3], reverse=True)
                
                # Extract the face region
                x, y, w, h = faces[0]
                face_region = img[y:y+h, x:x+w]
            
            # Resize face to standard size for consistent comparison
            face_resized = cv2.resize(face_region, (100, 100))
            
            # Compute color histogram (our "embedding")
            # Using HSV color space - more robust to lighting changes
            face_hsv = cv2.cvtColor(face_resized, cv2.COLOR_BGR2HSV)
            
            # Calculate histogram for each channel
            hist_h = cv2.calcHist([face_hsv], [0], None, [50], [0, 180])  # Hue
            hist_s = cv2.calcHist([face_hsv], [1], None, [60], [0, 256])  # Saturation
            hist_v = cv2.calcHist([face_hsv], [2], None, [60], [0, 256])  # Value
            
            # Normalize histograms
            cv2.normalize(hist_h, hist_h)
            cv2.normalize(hist_s, hist_s)
            cv2.normalize(hist_v, hist_v)
            
            # Concatenate all histograms into one feature vector
            histogram = np.concatenate([hist_h.flatten(), hist_s.flatten(), hist_v.flatten()])
            
            return histogram, "Success"
            
        except Exception as e:
            return None, f"Error processing image: {str(e)}"

    @classmethod
    def compute_similarity(cls, hist1, hist2):
        """
        Compare two histograms using correlation method.
        
        Args:
            hist1: First histogram array
            hist2: Second histogram array
            
        Returns:
            float: Similarity score between 0 and 1 (higher = more similar)
                   0.0 = completely different
                   1.0 = identical
        """
        if hist1 is None or hist2 is None:
            return 0.0
        
        try:
            h1 = np.array(hist1).flatten().astype(np.float32)
            h2 = np.array(hist2).flatten().astype(np.float32)
            
            # Ensure same length
            if len(h1) != len(h2):
                min_len = min(len(h1), len(h2))
                h1 = h1[:min_len]
                h2 = h2[:min_len]
            
            # Use correlation method - returns value between -1 and 1
            # 1 = perfect match, 0 = no correlation, -1 = inverse
            similarity = cv2.compareHist(h1, h2, cv2.HISTCMP_CORREL)
            
            # Normalize to 0-1 range (clip negative values to 0)
            similarity = max(0.0, similarity)
            
            return float(similarity)
            
        except Exception as e:
            print(f"Error computing similarity: {e}")
            return 0.0


# Backward compatibility: Keep the same function names
def get_face_embedding(image_path):
    """Legacy function name for compatibility"""
    return FaceAnalysisModel.get_embedding(image_path)


def compare_face_embeddings(embed1, embed2):
    """Legacy function name for compatibility"""
    return FaceAnalysisModel.compute_similarity(embed1, embed2)
