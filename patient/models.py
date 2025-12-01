from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.http import request
from doctor.models import User, Doctor
from django.utils import timezone
from django.core.exceptions import ValidationError


class Patient(models.Model):
    #TODO: use username field from main User model
    # name = models.CharField(max_length=30)
    age = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)])  # max digit
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patients')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.user.username


class Appointment(models.Model):
    APPOINT_STATUS = [('Completed', 'Completed'), ('Pending', 'Pending'), ('Canceled', 'Canceled')]
    # i will use this field to handle the appointments date operation like order matter in home page
    date = models.DateField()
    cost = models.IntegerField(
    validators=[MinValueValidator(0)]
    )
    status = models.CharField(max_length=12, choices=APPOINT_STATUS, default='Pending')
    is_prior = models.BooleanField(default=False)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointments')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at'] # the newest first
     
    def __str__(self):
        return f"{self.date} - {self.status}"
    
    def save(self, *args, **kwargs):
        if not self.pk and not self.is_prior: 
            self.cost = self.patient.doctor.default_cost
        elif self.is_prior:
            self.cost = self.patient.doctor.default_prior_cost
        else:
            # keep cost immutable
            old = Appointment.objects.get(pk=self.pk)
            self.cost = old.cost
        
        super().save(*args, **kwargs)

    def clean(self):
        if self.date < timezone.now().date():
            raise ValidationError("Appointment cannot be in the past.")


class Diagnosis(models.Model):
    diagnosis = models.TextField(max_length=200)
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.diagnosis[:10]


class Prescription(models.Model):
    prescription = models.TextField(max_length=100)
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Requires(models.Model):
    requires = models.TextField(max_length=100)
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
