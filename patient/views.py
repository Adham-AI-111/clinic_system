from django.shortcuts import render, redirect
from .forms import PatientSignupForm
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from doctor.permissions import staff_required

# @staff_required
def signup_patient(request):
    if request.method == 'POST':
        form = PatientSignupForm(request.POST, request=request)
        if form.is_valid():
            print('form is valid')
            form.save()
            return redirect('dashboard')
        else:
            print(form.errors)
    else:
        form = PatientSignupForm(request=request)

    context = {'form':form}
    return render(request, 'reception/add_patient.html', context)