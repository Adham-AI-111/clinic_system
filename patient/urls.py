from django.urls import path
from . import views

urlpatterns = [
    path('patient-signup/', views.signup_patient, name='patient-signup')
]
