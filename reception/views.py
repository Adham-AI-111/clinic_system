from django.shortcuts import render, redirect, get_object_or_404
from .forms import ReceptionSignupForm
from common.permissions import doctor_required
from common.shared_forms import CreateAppointmentForm
from doctor.models import User
from patient.models import Patient


@doctor_required
def reception_signup(request):
    if request.method == 'POST':
        form = ReceptionSignupForm(request.POST, request=request)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = ReceptionSignupForm(request=request)
    context = {'form':form}
    return render(request, 'doctor/add_reception.html', context)


def create_appointment(request, pk):
    '''
    will done from user profile
    '''
    # TODO: get user id from the page, after we passed it from patient profile, and get user instance from user model
    user = get_object_or_404(User, id=pk)
    patient = get_object_or_404(Patient, user=user)
    # print(patient.id)

    form = CreateAppointmentForm(request.POST,  patient=patient)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    
    context = {'form':form, 'user':user}
    return render(request, 'reception/add_appointment.html', context)