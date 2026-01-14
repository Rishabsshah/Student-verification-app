from django.urls import path
from . import views

urlpatterns = [
    path('verify/', views.verify_student, name='verify_student'),
    path('web-verify/', views.web_verify_student, name='web_verify_student'),
    path('inspect-id/', views.inspect_id_card, name='inspect_id_card'),
    path('verify-selfie/', views.verify_selfie, name='verify_selfie'),
    path('id-verification/', views.id_verification_page, name='id_verification_page'),
    path('account-details/', views.account_details_page, name='account_details_page'),
    path('selfie-check/', views.selfie_check_page, name='selfie_check_page'),
    path('complete-signup/', views.signup_final_page, name='signup_final'),
]