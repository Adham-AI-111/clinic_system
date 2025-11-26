from django import forms
from doctor.models import User, Doctor
from .models import Patient
from doctor.forms import UserSignupForm

# used in concat between user model and patient model
class PatientProfileForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = ['age']
        widgets = {
            'age': forms.NumberInput(attrs={'type': 'number'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['age'].label = 'العمر'


class PatientSignupForm(UserSignupForm):
    '''
    compination between user model and patient model to create patint user
    '''
    def __init__(self, *args, **kwargs):
        # allow us to use "request" in save method
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        # create PatientProfileForm instance to use its fields
        self.patient_form = PatientProfileForm(data=self.data if self.is_bound else None,
            prefix='patient')

        #!  "combinaton fields here"  Merge fields into this form
        self.fields.update(self.patient_form.fields)

        def is_valid(self):
            return super().is_valid() and self.patient_form.is_valid()

        def save(self, commit=True):
            if not self.request:
                raise ValueError("Request must be passed to PatientSignupForm")

            # save user directly by commit=true, beacuse no more actions we want to do on user model
            # if not saved the teacher will not created, because the relation will faild
            user = super().save(commit=commit)

            if commit:
                # set the relations
                patient = self.patient_form.save(commit=False)
                patient.user = user
                patient.doctor = self.request.tenant
                patient.save()

            # TODO: how commit work in view in this case, if type commit=false in view
            return user