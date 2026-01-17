"""
Face embedding utility using DeepFace.
Production-ready face recognition with deep learning models.
"""
import os
import numpy as np
from deepface import DeepFace
import cv2

class FaceAnalysisModel:
    """
    Face recognition using DeepFace library.
    Uses VGG-Face model for embeddings and verification.
    """
    
    @classmethod
    def get_embedding(cls, image_path):
        """
        Extract a face embedding from an image using DeepFace.
        Returns (embedding_array, message)
        
        Args:
            image_path: Path to the image file
            
        Returns:
            tuple: (embedding array or None, status message)
        """
        try:
            # Check if file exists
            if not os.path.exists(image_path):
                return None, f"Image file not found: {image_path}"
            
            # Read and validate image
            img = cv2.imread(image_path)
            if img is None:
                return None, "Could not read image file"
            
            # Use DeepFace to extract embedding
            # Model options: VGG-Face, Facenet, Facenet512, OpenFace, DeepFace, DeepID, ArcFace, Dlib, SFace
            # VGG-Face is a good balance of accuracy and speed
            embedding_objs = DeepFace.represent(
                img_path=image_path,
                model_name='VGG-Face',  # Good accuracy, widely used
                enforce_detection=False,  # More lenient - handle glasses, angles, lighting
                detector_backend='opencv',  # Fast detection
                align=True  # Align face for better accuracy
            )
            
            # DeepFace.represent returns a list of face embeddings
            if not embedding_objs or len(embedding_objs) == 0:
                return None, "No face detected in image"
            
            # If multiple faces, use the first one (largest/most prominent)
            if len(embedding_objs) > 1:
                print(f"Warning: Multiple faces detected ({len(embedding_objs)}), using the first one")
            
            # Extract the embedding vector
            embedding = np.array(embedding_objs[0]['embedding'], dtype=np.float32)
            
            return embedding, "Success"
            
        except ValueError as e:
            # DeepFace raises ValueError when no face is detected
            if "Face could not be detected" in str(e) or "no face" in str(e).lower():
                return None, "No face detected in image"
            return None, f"Face detection error: {str(e)}"
            
        except Exception as e:
            return None, f"Error processing image: {str(e)}"

    @classmethod
    def compute_similarity(cls, embed1, embed2):
        """
        Compute cosine similarity between two embeddings.
        
        Args:
            embed1: First embedding array
            embed2: Second embedding array
            
        Returns:
            float: Similarity score between -1 and 1 (higher = more similar)
                   For faces: typically 0.3-0.7 range
        """
        if embed1 is None or embed2 is None:
            return 0.0
        
        try:
            v1 = np.array(embed1).flatten()
            v2 = np.array(embed2).flatten()
            
            # Ensure same length
            if len(v1) != len(v2):
                min_len = min(len(v1), len(v2))
                v1 = v1[:min_len]
                v2 = v2[:min_len]
            
            # Cosine similarity: (A · B) / (||A|| * ||B||)
            dot_product = np.dot(v1, v2)
            norm1 = np.linalg.norm(v1)
            norm2 = np.linalg.norm(v2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            # Return raw cosine similarity (already in -1 to 1 range)
            # For VGG-Face embeddings, this typically gives:
            # - Same person: 0.4 to 0.7
            # - Different people: -0.1 to 0.3
            similarity = dot_product / (norm1 * norm2)
            
            return float(similarity)
            
        except Exception as e:
            print(f"Error computing similarity: {e}")
            return 0.0
    
    @classmethod
    def verify_faces(cls, img1_path, img2_path, threshold=0.6):
        """
        Direct verification using DeepFace's built-in verify function.
        This is an alternative to manual embedding + similarity computation.
        
        Args:
            img1_path: Path to first image
            img2_path: Path to second image
            threshold: Similarity threshold (default 0.6 for VGG-Face)
            
        Returns:
            dict: Verification result with 'verified' boolean and 'distance' score
        """
        try:
            result = DeepFace.verify(
                img1_path=img1_path,
                img2_path=img2_path,
                model_name='VGG-Face',
                detector_backend='opencv',
                enforce_detection=True,
                align=True
            )
            return result
            
        except Exception as e:
            return {
                'verified': False,
                'distance': 1.0,
                'error': str(e)
            }


# Backward compatibility: Keep the same function names
def get_face_embedding(image_path):
    """Legacy function name for compatibility"""
    return FaceAnalysisModel.get_embedding(image_path)


def compare_face_embeddings(embed1, embed2):
    """Legacy function name for compatibility"""
    return FaceAnalysisModel.compute_similarity(embed1, embed2)
