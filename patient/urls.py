from django.urls import path
from . import views

urlpatterns = [
    path('patient-signup/', views.signup_patient, name='patient-signup'),
    path('patient-login/', views.patient_login, name='patient-login'),
    path('patient-profile/<int:user_id>/', views.patient_profile, name='patient-profile'),
    path('appointment-details/<int:appoint_id>/<int:patient_id>/', views.appointment_details, name='appointment-details'),
]
