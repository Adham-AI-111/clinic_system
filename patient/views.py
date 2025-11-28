from datetime import timedelta
import logging
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from doctor.models import Domain
from common.permissions import staff_required
from .forms import PatientSignupForm


logger = logging.getLogger(__name__)

MAX_LOGIN_ATTEMPTS = 15
LOCKOUT_DURATION = timedelta(minutes=15)


@staff_required
def signup_patient(request):
    if request.method == 'POST':
        form = PatientSignupForm(request.POST, request=request)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = PatientSignupForm(request=request)

    context = {'form':form}
    return render(request, 'reception/add_patient.html', context)



@require_http_methods(["GET", "POST"])
def patient_login(request):
    """
    Handle login for patients.
    Requires: phone and username (no password)
    """
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        phone = request.POST.get('phone', '').strip()
        username = request.POST.get('username', '').strip()
        
        if not phone or not username:
            messages.error(request, 'من فضلك أدخل رقم الهاتف واسم المستخدم')
            return render(request, 'patient/patient_login.html')
        
        # Authenticate
        user = authenticate(request, phone=phone, username=username)
        
        if user is not None:
            # Check if account is locked
            if user.is_locked:
                messages.error(request, 'الحساب مغلق. تواصل مع الاستقبال')
                return render(request, 'patient/patient_login.html')
            
            # Reset failed attempts
            if user.failed_login_attempts > 0:
                user.failed_login_attempts = 0
                user.account_locked_until = None
                user.save(update_fields=['failed_login_attempts', 'account_locked_until'])
            
            login(request, user)
            logger.info(f"Patient login successful: {user.username}")
            
            # GET TENANT DOMAIN AND REDIRECT
            if hasattr(user, 'patient') and user.patient.tenant:
                tenant = user.patient.tenant
                domain = Domain.objects.filter(
                    tenant=tenant,
                    is_primary=True
                ).first()

                if domain:
                    return redirect(f"http://{domain.domain}/")

            messages.success(request, f'مرحباً {user.username}')
            # Fallback if no tenant found
            return redirect('home')
        
        else:
            # Handle failed login
            try:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                user = User.objects.get(phone=phone, username=username)
                
                user.failed_login_attempts += 1
                user.last_login_attempt = timezone.now()
                
                if user.failed_login_attempts >= MAX_LOGIN_ATTEMPTS:
                    user.account_locked_until = timezone.now() + LOCKOUT_DURATION
                    user.save(update_fields=['failed_login_attempts', 'last_login_attempt', 'account_locked_until'])
                    messages.error(request, 'تم غلق الحساب. تواصل مع الاستقبال')
                else:
                    user.save(update_fields=['failed_login_attempts', 'last_login_attempt'])
                    messages.error(request, 'رقم الهاتف أو اسم المستخدم غير صحيح')
            except User.DoesNotExist:
                messages.error(request, 'رقم الهاتف أو اسم المستخدم غير صحيح')
            
            logger.warning(f"Failed patient login - phone: {phone}, username: {username}")
    
    return render(request, 'patient/patient_login.html')


def patient_logout(request):
    logout(request)
    return render(request, 'doctor/home.html')

def patient_profile(request, pk):
    '''
    the single user appointments
    '''
    return render(request, 'patient/patient_profile.html')
