from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='api_login'),
    path('api/student-signup/', views.student_signup_api, name='student_signup_api'),
]
