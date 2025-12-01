from django.shortcuts import render, redirect, get_object_or_404
from .forms import ReceptionSignupForm
from common.permissions import doctor_required, staff_required
from common.shared_forms import CreateAppointmentForm
from doctor.models import User
from patient.models import Patient
from django.contrib import messages

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


@staff_required
def create_appointment(request, pk):
    '''
    - will done from user profile
    - pk is the user instance id passed from patient profile
    '''
    user = get_object_or_404(User, id=pk)
    # for link between appointment and the patient in the form
    patient = get_object_or_404(Patient, user=user)
    # print(patient.id)

    if request.method == 'POST':
        form = CreateAppointmentForm(request.POST,  patient=patient)
        if form.is_valid():
            form.save()
            messages.success(request, 'appointment added successfully')
            return redirect('dashboard')
        else:
            print('error found')
    else:
        form = CreateAppointmentForm(patient=patient)
    
    context = {'form':form, 'user':user}
    return render(request, 'reception/add_appointment.html', context)