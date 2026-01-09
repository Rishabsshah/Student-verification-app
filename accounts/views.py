from django.contrib.auth import authenticate
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token


@api_view(['POST'])
def login_view(request):
    """
    Custom login view for Campus Safety application.

    Authenticates username/password, then checks verification_status.
    Only allows login for VERIFIED students.

    Steps:
    1. Authenticate credentials normally
    2. Check user.verification_status == "VERIFIED"
    3. If not verified, return 403 Forbidden with clear message
    4. If verified, create/issue token for API access

    This ensures unverified students (REVIEW/REJECTED) cannot access the app.
    """
    # Get credentials from request
    username = request.data.get('username')
    password = request.data.get('password')

    if not username or not password:
        return Response(
            {'error': 'Username and password are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Authenticate user with Django's authenticate function
    user = authenticate(username=username, password=password)

    if user is None:
        return Response(
            {'error': 'Invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    # CRITICAL: Check verification status BEFORE allowing login
    # Only VERIFIED students can access the Campus Safety application
    if user.verification_status != 'VERIFIED':
        return Response(
            {'error': 'Student verification pending or rejected'},
            status=status.HTTP_403_FORBIDDEN
        )

    # User is authenticated AND verified - create token
    token, created = Token.objects.get_or_create(user=user)

    return Response({
        'token': token.key,
        'user_id': user.id,
        'username': user.username,
        'verification_status': user.verification_status
    }, status=status.HTTP_200_OK)


from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.shortcuts import render, redirect
from django.contrib.auth import login
from .models import User
from .forms import CustomUserCreationForm


class SignupView(CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'CampusSafety/signup.html'

    def form_valid(self, form):
        user = form.save(commit=False)
        enrollment_number = self.request.POST.get('enrollment_number')
        identity_hash = self.request.POST.get('identity_hash')
        
        if enrollment_number and identity_hash:
            user.enrollment_number = enrollment_number
            user.identity_hash = identity_hash
            user.verification_status = 'VERIFIED'
        else:
            user.verification_status = 'REVIEW'
            
        user.save()
        return super().form_valid(form)


def dashboard(request):
    if not request.user.is_authenticated:
        return redirect('login')
    return render(request, 'CampusSafety/dashboard.html', {
        'user': request.user
    })


def verify_page(request):
    if not request.user.is_authenticated:
        return redirect('login')
    return render(request, 'CampusSafety/verify.html', {
        'user': request.user
    })
