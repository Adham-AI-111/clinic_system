from django.db import models
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from phonenumber_field.modelfields import PhoneNumberField
from django_tenants.models import TenantMixin, DomainMixin
from django.utils.crypto import get_random_string

class UserManager(BaseUserManager):
    def create_user(self, username, phone, password=None, role='patient', **extra_fields):
        """
        Create and save a regular user.
        - username: required for login
        - phone: replaces email (required)
        - password: optional for patients, required for others
        """
        if not username:
            raise ValueError('The username field must be set')
        if not phone:
            raise ValueError('The phone field must be set')
        
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        extra_fields['role'] = role
        
        user = self.model(username=username, phone=phone, **extra_fields)
        
        # Patients can have no password (passwordless auth)
        # Other roles MUST have a password
        if role == 'patient':
            if password:
                user.set_password(password)
            else:
                user.set_unusable_password()  # Passwordless login
        else:
            # Doctors, admins, staff MUST have password
            if not password:
                raise ValueError(f'{role} must have a password')
            user.set_password(password)
        
        user.save(using=self._db)
        return user
    
    def create_superuser(self, username, phone, password=None, **extra_fields):
        """Create and save a superuser (admin access only)."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        if password is None:
            raise ValueError('Superuser must have a password')
        
        return self.create_user(username, phone, password=password, **extra_fields)



class User(AbstractUser):
    ROLE_CHOICES = [('admin', 'Admin'), ('doctor', 'Doctor'), ('reception', 'Reception'), ('patient', 'Patient')]
    role = models.CharField(max_length=12, choices=ROLE_CHOICES, default='patient')
    # one source phone field to use it in authentication
    phone = PhoneNumberField(region="EG", unique=True)  # add region="EG" 
    # username = None

    USERNAME_FIELD = 'username' # when register a superuser
    REQUIRED_FIELDS = ['phone']
    
    objects = UserManager()
    
    def __str__(self):
        return self.username


class Doctor(TenantMixin):
    #TODO: user username field from main User model
    # name = models.CharField(max_length=30)
    major = models.CharField(max_length=50)
    addresses = models.CharField(max_length=150)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    # default true, schema will be automatically created and synced when it is saved
    auto_create_schema = True

    def __str__(self):
        if self.user:
            return f"Doctor: {self.user.username}"
        return "Doctor without user"


class Domain(DomainMixin):
    pass