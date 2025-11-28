from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from .forms import ReceptionSignupForm
from doctor.permissions import doctor_required


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

