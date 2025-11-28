from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from doctor.models import User, Doctor

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
    cost = models.DecimalField(
    max_digits=8,
    decimal_places=2,
    validators=[MinValueValidator(0)]
    )
    prior_cost = models.DecimalField(
    max_digits=8,
    decimal_places=2,
    validators=[MinValueValidator(0)]
    )
    status = models.CharField(max_length=12, choices=APPOINT_STATUS, default='Pending')
    is_prior = models.BooleanField(default=False)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointments')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['-created_at'] # the newest first
     
    def __str__(self):
        return f"{self.created_at} - {self.status}"


class Diagnosis(models.Model):
    diagnosis = models.TextField(max_length=200)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.diagnosis[:15]


# class Prescription(models.Model):
#     prescription = models.TextField(max_length=100)
#     appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE)
#     created_at = models.DateTimeField(auto_now_add=True)
