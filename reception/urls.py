from django.urls import path
from . import views

urlpatterns = [
    path('reception-signup/', views.reception_signup, name='reception-signup'),
    path('create-appointment/<int:pk>/', views.create_appointment, name='create-appointment'),
]
