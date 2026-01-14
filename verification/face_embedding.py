"""
Face embedding utility using MediaPipe.
Compatible with Python 3.13.
"""
import os
import cv2
import numpy as np

# We'll use a simpler approach: extract face region and compute histogram-based embedding
# This is a fallback that works without complex ML models

class FaceAnalysisModel:
    _face_cascade = None

    @classmethod
    def load_model(cls):
        if cls._face_cascade is None:
            # Use OpenCV's built-in face detector
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            cls._face_cascade = cv2.CascadeClassifier(cascade_path)
            print("Face detector loaded.")

    @classmethod
    def get_embedding(cls, image_path):
        """
        Extract a face embedding from an image.
        Returns (embedding_array, message)
        """
        cls.load_model()
        
        try:
            # Read image
            img = cv2.imread(image_path)
            if img is None:
                return None, "Could not read image"
            
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Detect faces (relaxed parameters for better detection)
            faces = cls._face_cascade.detectMultiScale(
                gray, 
                scaleFactor=1.05, 
                minNeighbors=3, 
                minSize=(30, 30)
            )
            
            if len(faces) == 0:
                return None, "No face detected"
            
            if len(faces) > 1:
                # Use the largest face
                faces = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
            
            # Get the face region
            x, y, w, h = faces[0]
            
            # Add some padding
            pad = int(0.1 * w)
            x1 = max(0, x - pad)
            y1 = max(0, y - pad)
            x2 = min(img.shape[1], x + w + pad)
            y2 = min(img.shape[0], y + h + pad)
            
            face_img = img[y1:y2, x1:x2]
            
            # Resize to standard size
            face_img = cv2.resize(face_img, (128, 128))
            
            # Convert to LAB color space for better color comparison
            lab = cv2.cvtColor(face_img, cv2.COLOR_BGR2LAB)
            
            # Compute histogram for each channel
            hist_features = []
            for i in range(3):
                hist = cv2.calcHist([lab], [i], None, [32], [0, 256])
                hist = cv2.normalize(hist, hist).flatten()
                hist_features.extend(hist)
            
            # Also add some geometric features from the grayscale face
            gray_face = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
            
            # LBP-like texture features (simplified)
            # Divide face into 4x4 grid and compute mean/std for each cell
            cell_h, cell_w = 32, 32
            for row in range(4):
                for col in range(4):
                    cell = gray_face[row*cell_h:(row+1)*cell_h, col*cell_w:(col+1)*cell_w]
                    hist_features.append(np.mean(cell) / 255.0)
                    hist_features.append(np.std(cell) / 128.0)
            
            embedding = np.array(hist_features, dtype=np.float32)
            return embedding, "Success"
            
        except Exception as e:
            return None, str(e)

    @classmethod
    def compute_similarity(cls, embed1, embed2):
        """
        Compute cosine similarity between two embeddings.
        Returns value between 0 and 1.
        """
        if embed1 is None or embed2 is None:
            return 0.0
        
        v1 = np.array(embed1).flatten()
        v2 = np.array(embed2).flatten()
        
        # Ensure same length
        min_len = min(len(v1), len(v2))
        v1 = v1[:min_len]
        v2 = v2[:min_len]
        
        # Cosine similarity
        dot_product = np.dot(v1, v2)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        similarity = dot_product / (norm1 * norm2)
        return max(0.0, min(1.0, similarity))
