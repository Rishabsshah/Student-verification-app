from django.urls import path
from . import views

urlpatterns = [
    path('verify/', views.verify_student, name='verify_student'),
    path('web-verify/', views.web_verify_student, name='web_verify_student'),
    path('inspect-id/', views.inspect_id_card, name='inspect_id_card'),
]