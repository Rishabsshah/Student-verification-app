from django.contrib.auth import authenticate
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
import re


@api_view(['POST'])
def student_signup_api(request):
    """
    API endpoint for minimal student signup.

    Required fields:
        - username
        - email
        - password
        - full_name
        - aadhar_number  (12-digit Aadhaar number)

    Optional fields:
        - phone_number
        - enrollment_number

    Returns 201 on success with token and user details.
    """
    data = request.data

    # ── Required field validation ──────────────────────────────────────────────
    required = ['username', 'email', 'password', 'full_name', 'aadhar_number']
    missing = [f for f in required if not data.get(f, '').strip()]
    if missing:
        return Response(
            {'error': f"Missing required fields: {', '.join(missing)}"},
            status=status.HTTP_400_BAD_REQUEST
        )

    username      = data['username'].strip()
    email         = data['email'].strip()
    password      = data['password']
    full_name     = data['full_name'].strip()
    aadhar_number = data['aadhar_number'].strip()

    # ── Aadhar format validation (exactly 12 digits) ──────────────────────────
    if not re.fullmatch(r'\d{12}', aadhar_number):
        return Response(
            {'error': 'aadhar_number must be exactly 12 digits'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # ── Duplicate checks ───────────────────────────────────────────────────────
    from .models import User
    if User.objects.filter(username=username).exists():
        return Response(
            {'error': 'Username already taken'},
            status=status.HTTP_409_CONFLICT
        )
    if User.objects.filter(email=email).exists():
        return Response(
            {'error': 'Email already registered'},
            status=status.HTTP_409_CONFLICT
        )

    # ── Create user ────────────────────────────────────────────────────────────
    # Split full_name into first/last for Django's AbstractUser
    name_parts = full_name.split(' ', 1)
    first_name = name_parts[0]
    last_name  = name_parts[1] if len(name_parts) > 1 else ''

    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        aadhar_number=aadhar_number,
        phone_number=data.get('phone_number', '').strip() or None,
        enrollment_number=data.get('enrollment_number', '').strip() or None,
        verification_status='REVIEW',   # always starts under review
    )

    # Issue an auth token immediately so the client can authenticate follow-up calls
    token, _ = Token.objects.get_or_create(user=user)

    return Response({
        'message': 'Student registered successfully',
        'user_id': user.id,
        'username': user.username,
        'email': user.email,
        'full_name': f"{user.first_name} {user.last_name}".strip(),
        'aadhar_number': user.aadhar_number,
        'verification_status': user.verification_status,
        'token': token.key,
    }, status=status.HTTP_201_CREATED)


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
    # Admins and staff go straight to Django admin panel
    if request.user.is_staff or request.user.is_superuser:
        return redirect('/admin/')
    return render(request, 'CampusSafety/dashboard.html', {
        'user': request.user
    })


def verify_page(request):
    if not request.user.is_authenticated:
        return redirect('login')
    return render(request, 'CampusSafety/verify.html', {
        'user': request.user
    })
