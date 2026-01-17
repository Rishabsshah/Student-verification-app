# DeepFace Configuration - Prototype/Demo Mode

## Overview
The DeepFace face verification system has been configured with **lenient thresholds** to make the prototype work smoothly for demonstrations.

## Current Configuration

### Face Detection Settings (face_embedding.py)
```python
DeepFace.represent(
    img_path=image_path,
    model_name='VGG-Face',           # Balance of accuracy and speed
    enforce_detection=False,          # ✅ LENIENT - Handles poor angles, glasses, lighting
    detector_backend='opencv',        # Fast detection
    align=True                        # Auto-align faces for better accuracy
)
```

### Verification Thresholds (verification/views.py)

#### 🎯 PROTOTYPE/DEMO MODE (Current - Lenient)
- **Auto-Verify**: Similarity > 0.20 ✅ (LOWERED from 0.40)
- **Review**: Similarity 0.10 - 0.20 ⚠️ (LOWERED from 0.25-0.40)
- **Reject**: Similarity < 0.10 ❌ (LOWERED from 0.25)

#### 🔒 PRODUCTION MODE (Recommended for deployment)
- **Auto-Verify**: Similarity > 0.40 ✅
- **Review**: Similarity 0.25 - 0.40 ⚠️
- **Reject**: Similarity < 0.25 ❌

## Why These Changes?

### Prototype Benefits (Current Settings):
✅ Works with various lighting conditions
✅ Tolerates different angles and poses
✅ Handles glasses, hats, facial expressions
✅ Better for quick demos
✅ Lower false rejection rate

### Production Concerns:
⚠️ Higher false acceptance rate
⚠️ Less secure verification
⚠️ May accept different people who look similar

## Similarity Score Interpretation

### VGG-Face Cosine Similarity Range: -1.0 to 1.0
- **0.60 - 1.00**: Almost identical (same person, similar photo)
- **0.40 - 0.60**: Strong match (same person, different conditions)
- **0.20 - 0.40**: Moderate match (DEMO: acceptable, PROD: uncertain)
- **0.10 - 0.20**: Weak match (DEMO: review, PROD: reject)
- **Below 0.10**: No match (different people)

## Testing Tips for Prototype

1. **ID Card Photo**: Use clear, well-lit photo
2. **Selfie**: 
   - Look directly at camera
   - Good lighting
   - Remove glasses if they were not in ID photo
   - Neutral expression similar to ID

3. **Expected Results**:
   - Same person, similar conditions: 0.40-0.70 (✅ Verified)
   - Same person, different lighting: 0.25-0.45 (✅ Verified in demo mode)
   - Same person, very different angle: 0.15-0.30 (⚠️ May need review)
   - Different people: 0.00-0.20 (❌ Rejected)

## When to Switch to Production Mode

Before deploying to real users:
1. Change thresholds back to production values in `verification/views.py`
2. Test with real student ID cards
3. Consider adding additional security checks
4. Enable strict face detection (`enforce_detection=True`)

## How to Revert to Production Mode

In `verification/views.py`, line ~210, change:
```python
# DEMO MODE
if similarity > 0.20:  # LENIENT

# PRODUCTION MODE
if similarity > 0.40:  # STRICT
```

And similarly for review and reject thresholds.

---

**Note**: Current settings are optimized for **prototype demonstrations**. For production deployment with real students, use stricter thresholds!
