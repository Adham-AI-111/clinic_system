from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from datetime import timedelta
import logging
from django.db.models import F
from .models import User, Doctor
from patient.models import Patient, Appointment
from common.permissions import staff_required
from .models import Domain

logger = logging.getLogger(__name__)

MAX_LOGIN_ATTEMPTS = 15
LOCKOUT_DURATION = timedelta(minutes=15)

@require_http_methods(["GET", "POST"])
def staff_login(request):
    """
    Handle login for staff members (doctors, reception, admin).
    Requires: username and password
    """
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        if not username or not password:
            messages.error(request, 'من فضلك أدخل اسم المستخدم وكلمة المرور')
            return render(request, 'doctor/staff_login.html')
        
        # Authenticate
        user = authenticate(request, username=username, password=password)
        
        if user is not None and user.is_staff_member:
            # Check if account is locked
            if user.is_locked:
                messages.error(
                    request, 
                    f'الحساب مغلق حتى {user.account_locked_until.strftime("%H:%M")}. حاول لاحقاً'
                )
                return render(request, 'doctor/staff_login.html')

            # Reset failed attempts
            if user.failed_login_attempts > 0:
                user.failed_login_attempts = 0
                user.account_locked_until = None
                user.save(update_fields=['failed_login_attempts', 'account_locked_until'])

            login(request, user)
            logger.info(f"Staff login successful: {user.username}")
            messages.success(request, f'مرحباً {user.username}')
        
            # Redirect to tenant domain
            tenant = None
            if hasattr(user, 'doctor'):
                tenant = user.doctor
            elif hasattr(user, 'reception'):
                tenant = user.reception.doctor

            if tenant:
                domain = Domain.objects.filter(tenant=tenant, is_primary=True).first()
                if domain:
                    return redirect(f"http://{domain.domain}:8000/")
            else:
                print(f'no domain found for this user {user.username, user.role}')
                logger.info(f"someone who not doctor or recetion logged in {user.username, user.role}")
                logout(request)
                return redirect('home')
        
        # authenticate return none
        else:
            # Handle failed login
            try:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                user = User.objects.get(username=username)
                
                user.failed_login_attempts += 1
                user.last_login_attempt = timezone.now()
                
                if user.failed_login_attempts >= MAX_LOGIN_ATTEMPTS:
                    user.account_locked_until = timezone.now() + LOCKOUT_DURATION
                    user.save(update_fields=['failed_login_attempts', 'last_login_attempt', 'account_locked_until'])
                    messages.error(
                        request, 
                        f'تم غلق الحساب لمدة {LOCKOUT_DURATION.seconds // 60} دقيقة بسبب المحاولات الفاشلة'
                    )
                else:
                    user.save(update_fields=['failed_login_attempts', 'last_login_attempt'])
                    remaining = MAX_LOGIN_ATTEMPTS - user.failed_login_attempts
                    messages.error(request, f'بيانات خاطئة. المحاولات المتبقية: {remaining}')
            except User.DoesNotExist:
                messages.error(request, 'اسم المستخدم أو كلمة المرور غير صحيحة')
            
            logger.warning(f"Failed staff login attempt for: {username}")
    
    return render(request, 'doctor/staff_login.html')


def staff_logout(request):
    logout(request)
    return render(request, 'doctor/home.html')


def home(request):
    '''
    the entry point for the system --login urls
    '''
    if request.user.is_authenticated and request.user.is_staff_member:
        return redirect('dashboard')
    return render(request, 'doctor/home.html')

@staff_required
def dashboard(request):
    return render(request, 'doctor/dashboard.html')

def patients_dash(request):
    # we quesry every instance in patient model with its related data in user model
    patients = Patient.objects.select_related('user').all()
    
    context = {'patients':patients}
    return render(request, 'doctor/patients.html', context)

def appointments_dash(request):
    '''
    all appointments for the current doctor are on the system
    '''
    # get all appointments model columns combined with custom columns from user model that related to the patient
    # I related to patient__user instead of patient only, to minimize the queries while I won't see any columns from the patient model itself
    appointments = Appointment.objects.select_related('patient__user').annotate(
        patient_ID = F("patient__user__id"),
        patient_name = F("patient__user__username"),
        patient_age = F("patient__age"),
    )
    context = {'appointments':appointments}
    return render(request, 'doctor/appointments_history.html', context)