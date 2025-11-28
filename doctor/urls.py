from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('staff-login/', views.staff_login, name='staff-login'),
    path('staff-logout/', views.staff_logout, name='staff-logout'),
    path('patients-dash/', views.patients_dash, name='patients-dash'),
    path('appointments-dash/', views.appointments_dash, name='appointments-dash'),
]
