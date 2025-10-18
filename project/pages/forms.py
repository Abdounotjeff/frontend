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
            'placeholder': "Enter your First name"
        })
        self.fields['last_name'].widget.attrs.update({
            'class': common_classes,
            'placeholder': "Enter your Last name"
        })

        # Role
        self.fields['role'].widget.attrs.update({
            'class': common_classes,
        })

        # Passwords
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

class RaceCreationForm(forms.ModelForm):
    class Meta:
        model = Race
        fields = ['type', 'title', 'rules', 'description', 'place', 'wilaya','price','date', 'logo', 'Allowed_Ages']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500'
            })

        # Extra tweaks (optional)
        self.fields['rules'].widget.attrs['rows'] = 4
        self.fields['description'].widget.attrs['rows'] = 4
        self.fields['place'].widget.attrs['placeholder'] = 'https://maps.google.com/...'
        self.fields['date'].widget.attrs['type'] = 'datetime-local'

class RankingForm(forms.Form):
    def __init__(self, *args, racers=None, **kwargs):
        super().__init__(*args, **kwargs)
        if racers:
            for racer in racers:
                self.fields[f'rank_{racer.id}'] = forms.IntegerField(
                    required=False,
                    label=f"{racer.user.get_full_name}",
                    min_value=1,
                    widget=forms.NumberInput(attrs={
                        'class': 'w-24 border rounded p-1 text-center'
                    })
                )
