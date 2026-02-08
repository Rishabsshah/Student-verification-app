"""
URL configuration for CampusSafety project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views
from accounts.views import SignupView, dashboard, verify_page
from verification.views import id_verification_page, account_details_page, selfie_check_page, signup_final_page

urlpatterns = [
    path("", views.home, name="home"),
    path("admin/", admin.site.urls),
    path('logout/', auth_views.LogoutView.as_view(next_page='id_verification_page'), name='logout'),
    path('dashboard/', dashboard, name='dashboard'),
    path('id-verification/', id_verification_page, name='id_verification_page'),
    path('account-details/', account_details_page, name='account_details_page'),
    path('selfie-check/', selfie_check_page, name='selfie_check_page'),
    path('complete-signup/', signup_final_page, name='signup_final'),
    path('triple-lock-test/', views.triple_lock_test, name='triple_lock_test'),  # Test page
    path('api/accounts/', include('accounts.urls')),
    path('api/verification/', include('verification.urls')),
    path('verification/', include('verification.urls')),  # Also include under /verification/
]
