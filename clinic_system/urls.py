from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('doctor.urls')),
    path('patient/', include('patient.urls')),
    path('reception/', include('reception.urls')),
]
