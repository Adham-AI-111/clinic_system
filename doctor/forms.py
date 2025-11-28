from django import forms
from django.forms import widgets
from .models import User, Doctor


class UserSignupForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'phone', 'role', 'password',]
        widgets = {
            # ? use widgets to control HTML behavior
            # 'role': forms.Select(attrs={'disabled': True})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'الاسم'
        self.fields['phone'].label = 'رقم الهاتف'
        self.fields['role'].label = 'التصنيف'
        self.fields['password'].label = 'الرقم السري'
        # self.fields['password1'].label = 'تأكيد الرقم السري'
