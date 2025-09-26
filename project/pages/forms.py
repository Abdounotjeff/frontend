from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from .models import *

class CreateUserForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2', 'role']

class OrganizerForm(UserCreationForm):
    class Meta:
        model =  Organizer
        fields = ['tel', 'carte_biometrique','pfp','bio']
class RacerForm(UserCreationForm):
    class Meta:
        model =  Racer
        fields = ['tel', 'carte_biometrique','pfp','bio','date_birth','speciality']