/*
* Android Liveness Detection Snippet (Kotlin)
* Dependencies:
* implementation "com.google.mlkit:face-detection:16.1.5"
* implementation "androidx.camera:camera-core:1.2.3"
* implementation "androidx.camera:camera-lifecycle:1.2.3"
* implementation "androidx.camera:camera-view:1.2.3"
*/

import android.graphics.Bitmap
import android.util.Log
import android.widget.Toast
import androidx.camera.core.ImageAnalysis
import androidx.camera.core.ImageProxy
import com.google.mlkit.vision.common.InputImage
import com.google.mlkit.vision.face.Face
import com.google.mlkit.vision.face.FaceDetection
import com.google.mlkit.vision.face.FaceDetectorOptions
import java.io.ByteArrayOutputStream
import java.util.concurrent.Executors

class FaceLivenessAnalyzer(private val onLivenessConfirmed: (Bitmap) -> Unit) : ImageAnalysis.Analyzer {

    private val detector = FaceDetection.getClient(
        FaceDetectorOptions.Builder()
            .setPerformanceMode(FaceDetectorOptions.PERFORMANCE_MODE_ACCURATE)
            .setLandmarkMode(FaceDetectorOptions.LANDMARK_MODE_ALL)
            .setClassificationMode(FaceDetectorOptions.CLASSIFICATION_MODE_ALL) // Required for Blink
            .build()
    )

    private var isBlinked = false
    private var isProcessing = false

    @androidx.annotation.OptIn(androidx.camera.core.ExperimentalGetImage::class)
    override fun analyze(imageProxy: ImageProxy) {
        if (isProcessing) {
            imageProxy.close()
            return
        }

        val mediaImage = imageProxy.image
        if (mediaImage != null) {
            val image = InputImage.fromMediaImage(mediaImage, imageProxy.imageInfo.rotationDegrees)
            
            detector.process(image)
                .addOnSuccessListener { faces ->
                    if (faces.isNotEmpty()) {
                        checkLiveness(faces[0], imageProxy)
                    } else {
                        imageProxy.close()
                    }
                }
                .addOnFailureListener {
                    imageProxy.close()
                }
        }
    }

    private fun checkLiveness(face: Face, imageProxy: ImageProxy) {
        val leftEyeOpen = face.leftEyeOpenProbability ?: 1.0f
        val rightEyeOpen = face.rightEyeOpenProbability ?: 1.0f

        // Blink Detection Logic
        // If both eyes are closed (< 0.3 probability), mark as blinked
        if (leftEyeOpen < 0.3f && rightEyeOpen < 0.3f) {
            isBlinked = true
            Log.d("Liveness", "Blink Detected!")
        }

        // If eyes are now open AND we previously detected a blink -> Liveness Confirmed
        if (isBlinked && leftEyeOpen > 0.8f && rightEyeOpen > 0.8f) {
            isProcessing = true // Stop analyzing to prevent double triggers
            captureFrame(imageProxy)
        } else {
            imageProxy.close()
        }
    }

    private fun captureFrame(imageProxy: ImageProxy) {
        // Convert ImageProxy to Bitmap
        // (Simplified: In real app, you need YUV to Bitmap converter or use CameraView.bitmap)
        // For this snippet, assuming you have a converter:
        val bitmap = imageProxy.toBitmap() 
        
        onLivenessConfirmed(bitmap)
        imageProxy.close()
    }
}

// --- Usage in Activity ---
/*
val analyzer = FaceLivenessAnalyzer { bitmap ->
    uploadSelfie(bitmap)
}
cameraController.setImageAnalysisAnalyzer(executor, analyzer)

fun uploadSelfie(bitmap: Bitmap) {
    val stream = ByteArrayOutputStream()
    bitmap.compress(Bitmap.CompressFormat.JPEG, 95, stream)
    val byteArray = stream.toByteArray()
    
    // POST byteArray to /api/verify-selfie/
}
*/
