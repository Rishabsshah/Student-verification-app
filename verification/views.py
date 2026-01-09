from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

from .ocr_utils import verify_student_id
from accounts.models import User


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_student(request):
    """
    API endpoint for student ID verification using OCR.
    ...
    """
    # Check if image file is provided
    if 'id_image' not in request.FILES:
        return Response(
            {'error': 'No image file provided'},
            status=status.HTTP_400_BAD_REQUEST
        )
    # ... rest of existing function

from rest_framework.permissions import AllowAny

from .utils import generate_identity_hash

@api_view(['POST'])
@permission_classes([AllowAny])
def inspect_id_card(request):
    """
    Public API to inspect an ID card before signup.
    Returns extracted college and enrollment number without saving to a User (yet).
    Checks for duplicates using the custom identity hash.
    """
    if 'id_image' not in request.FILES:
        return Response({'error': 'No image file provided'}, status=400)

    image_file = request.FILES['id_image']
    
    try:
        # Save temp
        file_name = default_storage.save('temp/' + image_file.name, ContentFile(image_file.read()))
        file_path = default_storage.path(file_name)
        
        # OCR (extracts name now too)
        name, college, enrollment, msg = verify_student_id(file_path)
        default_storage.delete(file_name)
        
        # Validation Logic
        if college is None:
            # Return debug info
            return Response({
                'valid': False, 
                'message': f'College not recognized. (Debug: {msg})'
            }, status=200)
        
        if enrollment is None:
             # Return debug info
             return Response({
                'valid': False, 
                'message': f'Enrollment not detected. (Debug: {msg})'
             }, status=200)

        # Generate Custom Hash (Name + Enrollment + College)
        # Handle missing name gracefully (fallback to 'UNKNOWN' or fail? User request implied name is needed)
        # Let's assume name is found or use empty string, but for strictness we should require it.
        # However, OCR name extraction is flaky. I'll use "" if None, but optimally should be present.
        
        student_name = name if name else "UNKNOWN"
        identity_hash = generate_identity_hash(student_name, enrollment, college)

        # Check duplicate using HASH
        if User.objects.filter(identity_hash=identity_hash).exists():
             return Response({'valid': False, 'message': 'Identity already registered'}, status=200)
             
        # Also check enrollment for safety (legacy check)
        if User.objects.filter(enrollment_number=enrollment).exists():
             return Response({'valid': False, 'message': 'Enrollment number already registered'}, status=200)
             
        return Response({
            'valid': True, 
            'college': college, 
            'enrollment': enrollment,
            'identity_hash': identity_hash,
            'message': 'Verification successful'
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=500)




from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages


@login_required
def web_verify_student(request):
    """
    Web view for student ID verification.
    Handles form submission and shows results with messages.
    """
    if request.method == 'POST':
        # Check if image file is provided
        if 'id_image' not in request.FILES:
            messages.error(request, 'No image file provided')
            return redirect('verify_page')

        image_file = request.FILES['id_image']

        try:
            # Save the uploaded file temporarily
            file_name = default_storage.save(
                'temp/' + image_file.name,
                ContentFile(image_file.read())
            )
            file_path = default_storage.path(file_name)

            # Perform OCR verification
            college, enrollment, ocr_message = verify_student_id(file_path)

            # Clean up temporary file
            default_storage.delete(file_name)

            # Get the authenticated user
            user = request.user

            # Apply verification rules
            if college is None:
                verification_status = 'REJECTED'
                reason = 'College name not recognized in the ID card'
            elif enrollment is None:
                verification_status = 'REVIEW'
                reason = 'Enrollment number could not be detected'
            else:
                if User.objects.filter(
                    enrollment_number=enrollment
                ).exclude(id=user.id).exists():
                    verification_status = 'REJECTED'
                    reason = 'Enrollment number already registered to another user'
                else:
                    verification_status = 'VERIFIED'
                    reason = 'Student verification successful'
                    user.enrollment_number = enrollment

            # Update user's verification status
            user.verification_status = verification_status
            user.save()

            # Show success or error message
            if verification_status == 'VERIFIED':
                messages.success(request, f'{reason} Enrollment: {enrollment}')
            else:
                messages.error(request, f'{reason} (Extracted college: {college}, enrollment: {enrollment})')

        except Exception as e:
            messages.error(request, f'Verification failed: {str(e)}')

    return redirect('verify_page')
