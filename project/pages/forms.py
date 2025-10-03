from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth import get_user_model
from .models import *

class CreateUserForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2', 'role']
        def __init__(self, *args, **kwargs):
            super(CreateUserForm, self).__init__(*args, **kwargs)

            common_classes = 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 shadow-sm'

            # Update widget attributes for username and email
            self.fields['username'].widget.attrs.update({
                'class': common_classes,
                'placeholder': "Enter your username"
            })
            self.fields['email'].widget.attrs.update({
                'class': common_classes,
                'placeholder': "Example@mail.com"
            })
            

            # Add first_name and last_name fields
            self.fields['first_name'].widget.attrs.update({
                'class': common_classes,
                'placeholder': " Enter your First name"
            })
            self.fields['last_name'].widget.attrs.update({
                'class': common_classes,
                'placeholder': "Enter your Last name"
            })
            self.fields['role'].widget.attrs.update({
                'class': common_classes,
            })

            # Manually override password fields
            self.fields['password1'].widget = forms.PasswordInput(attrs={
                'class': common_classes,
                'placeholder': "Your Password goes here"
            })
            self.fields['password2'].widget = forms.PasswordInput(attrs={
                'class': common_classes,
                'placeholder': "Confirm your Password"
            })

class EditUserForm(UserChangeForm):
    password = None  # Hide password field from normal editing
    role = None

    class Meta:
        model = CustomUser
        fields = ["username", "email", "first_name", "last_name"]


class OrganizerForm(forms.ModelForm):
    class Meta:
        model =  Organizer
        fields = ['tel', 'carte_biometrique','pfp','bio']
class RacerForm(forms.ModelForm):
    class Meta:
        model =  Racer
        fields = ['tel', 'carte_biometrique','pfp','bio','date_birth','speciality']
        widgets = {
            'date_birth': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
                }
            ),
        }


class PicturesForm(forms.ModelForm):
    class Meta:
        model = Pictures
        fields = ['IMG']

