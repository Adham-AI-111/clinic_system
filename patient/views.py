from audioop import reverse
from datetime import timedelta
import logging

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import ValidationError
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from common.permissions import doctor_required, staff_required, user_owns_profile
from doctor.models import Domain, User

from .forms import (
    CreateDiagnosisForm,
    CreatePrescriptionForm,
    CreateRequiresForm,
    PatientSignupForm,
)
from .models import Appointment, Diagnosis, Patient


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
                    return redirect(f"http://{domain.domain}/patient-profile/{user.id}")

            messages.success(request, f'مرحباً {user.username}')
            # Fallback if no tenant found
            # user_id not pk because i use this name in path
            return redirect('patient-profile', user_id=user.id)
        
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

 
# prevent non-owner to access tha profile
@user_owns_profile
def patient_profile(request, user_id):
    '''
    the single user appointments
    get by user_id the patient appointments
    '''
    
    user = User.objects.get(id=user_id) # get the patient instance in user model by user_id
    patient = Patient.objects.get(user=user) # get the patient instance itself in patient model
    appointments = Appointment.objects.filter(patient=patient)

    # i passed the user_id itself to use it in create appointment url
    context = {'user_id':user_id, 'patient':patient, 'appointments':appointments} # use patient to set his identifier data in profile, and appointment to redirect to appointment details
    return render(request, 'patient/patient_profile.html', context)


def appointment_details(request, appoint_id, user_id):
    user = get_object_or_404(User, id=user_id)
    appointment = get_object_or_404(Appointment, id=appoint_id)
    
    # prevent user from request onther user appointment by pass user id manaually in the url
    # http://localhost:8000/patient/appointment-details/2/11/  ->this is the true path
    # http://localhost:8000/patient/appointment-details/2/7/  -> this is a vain path  11 to 7
    #? the result is -> data that depends on user id will change but the  data that depends on appoint_id will not change
    if appointment.patient.user.id != user_id:
        return HttpResponseForbidden("Invalid URL parameters.")

    # ------ Get existing diagnosis for this appointment --------
    try:
        diagnosis = Diagnosis.objects.get(appointment=appointment)
        # or if there can be multiple: diagnosis = Diagnosis.objects.filter(appointment=appointment).first()
    except Diagnosis.DoesNotExist:
        diagnosis = None

    # ? handle prescription and requirements exits __instaed using try/except
    # prescription = appointment.prescription if hasattr(appointment, 'prescription') else None
    # requirements = appointment.requirements if hasattr(appointment, 'requirements') else None

    context = {
        'user':user,
        'appointment':appointment,
        'diagnosis': diagnosis}
    return render(request, 'patient/appointment_details.html', context)


@doctor_required
def create_diagnosis(request, appoint_id):
    appoint = Appointment.objects.get(id=appoint_id)
    
    # debug the url 
    try:
        url = reverse('add-diagnosis', args=[appoint.id])
    except Exception as e:
        url = None

    if request.method == 'POST':
        form = CreateDiagnosisForm(request.POST, appointment=appoint)
        
        if form.is_valid():
            new_diagnosis = form.save()
            return render(request, 'patient/partials/diagnosis_view.html', {'diagnosis': new_diagnosis})
        else:
            # Return form with errors so user can see what's wrong
            context = {'form': form, 'appointment': appoint}
            return render(request, 'patient/partials/diagnosis_form.html', context)
    else:
        form = CreateDiagnosisForm(appointment=appoint)
    
    context = {'form': form, 'appointment': appoint, 'url_path':url}
    return render(request, 'patient/partials/diagnosis_form.html', context)


@doctor_required
def update_diagnosis(request, diagnosis_id):
    diagnosis = get_object_or_404(Diagnosis, id=diagnosis_id)
    
    # debug the url 
    try:
        url = reverse('update-diagnosis', args=[diagnosis.id])
    except Exception as e:
        url = None

    if request.method == 'POST':
        form = CreateDiagnosisForm(request.POST, instance=diagnosis, appointment=diagnosis.appointment)
        if form.is_valid():
            updated_diagnosis = form.save()
            return render(request, 'patient/partials/diagnosis_view.html', {'diagnosis':updated_diagnosis})
    else:
        form = CreateDiagnosisForm(instance=diagnosis, appointment=diagnosis.appointment)
    context = {'form':form, 'url_path':url}
    return render(request, 'patient/partials/diagnosis_form.html', context)


@doctor_required
def delete_diagnosis(requets):
    pass