from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import get_user_model, authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.forms import inlineformset_factory
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from .models import *
from .tokens import account_activation_token
from .forms import *
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import get_connection
from django.http import JsonResponse
import json
from django.utils.timezone import now
from django.shortcuts import get_object_or_404
from datetime import datetime, date
from django.core.exceptions import ObjectDoesNotExist
from datetime import timedelta
import requests
from django.views.decorators.csrf import csrf_exempt
import hmac
import hashlib
import json

def activateEmail(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = get_user_model().objects.get(pk=uid)
        role = user.role
        print(role)
        print("1")
    except:
        user = None
        print(2)
    
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        print("3")
        user.save()
        messages.success(request, "Merce d'avoir vérifier votre Email!, tu peux s'incrire maintenant!")
        if role == "Organizer":
            Organizer.objects.create(user=user)
        elif role == "Participant":
            Racer.objects.create(user=user)
        return redirect('loginPage')
    else:
        print(4)
        messages.error(request, "Lien d'activation est invalide!")
    
    return redirect('registerPage')
##################################################################################

def send_activation_email(request, user, to_email):
    """
    Sends an activation email to a user.

    :param request: The request object passed to the view.
    :param user: The user instance to send the email to.
    :param to_email: The email address to send the email to.
    :return: The number of emails sent.
    """
    mail_subject = "Activate your account."
    message = render_to_string("pages/user_email.html", {
        'user': user,
        'domain': get_current_site(request).domain,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': account_activation_token.make_token(user),
        'protocol': 'http',  # change to 'https' in production
    })

    email = EmailMessage(mail_subject, message, to=[to_email], connection=get_connection())
    return email.send()

def resend_verification(request):
    email = request.session.get('pending_email')  # Get email from session

    if not email:
        messages.error(request, "Aucune adresse email trouvée. Inscrivez-vous d'abord.")
        return redirect("registerPage")  # Redirect to registration if no email is found

    try:
        user = User.objects.get(email=email)
        if user.is_active:
            messages.info(request, "Ce compte est déjà activé.")
        else:
            send_activation_email(request, user, user.email)
            messages.success(request, "Un nouvel email de vérification a été envoyé !")
    except User.DoesNotExist:
        messages.error(request, "Aucun compte trouvé avec cet email.")

    return render(request, "pages/verify_code.html", {"user_email": email})


@login_required
def createRacerProfile(request):
    try:
        # Prevent already created profile
        request.user.racer
        return redirect('RacerDashboard')
    except Racer.DoesNotExist:
        pass  

    if request.method == 'POST':
        form = RacerForm(request.POST)
        if form.is_valid():
            racer = form.save(commit=False)
            racer.user = request.user
            racer.save()
            return redirect('RacerDashboard')
    else:
        form = RacerForm()

    return render(request, 'racer/create_profile.html', {'form': form})


@login_required
def createOrganizerProfile(request):
    try:
        request.user.organizer
        return redirect('organizerDashboard')
    except Organizer.DoesNotExist:
        pass  

    if request.method == 'POST':
        form = OrganizerForm(request.POST)
        if form.is_valid():
            organizer = form.save(commit=False)
            organizer.user = request.user
            organizer.save()
            return redirect('organizerDashboard')
    else:
        form = OrganizerForm()

    return render(request, 'organizer/create_profile.html', {'form': form})

# 🚀 Register View
def registerPage(request):
    if request.method == 'POST':
        form = CreateUserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False) 
            user.is_active=False
            user.save() 
            email = form.cleaned_data.get('email')
            request.session['pending_email'] = email  # Store email in session
            send_activation_email(request, user, email)
            # Create role-specific object
           
            return redirect('activ')
        else:
            print(form.errors)  # Debugging: Prints form errors in console
            messages.error(request, 'Form validation failed. Please correct the errors.')
    
    else:  # GET request
        form = CreateUserForm()

    context = {'form': form}
    return render(request, 'pages/register.html', context)

def activ(request):
    return render(request, 'pages/verify_code.html')

# 🔐 Login View
def loginPage(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_active:
            login(request, user)

            if user.is_Participant:
                if not Racer.objects.filter(user=user).exists():
                    return redirect('createRacerProfile')
                return redirect('RacerDashboard')

            elif user.is_Organizer:
                if not Organizer.objects.filter(user=user).exists():
                    return redirect('createOrganizerProfile')
                return redirect('organizerDashboard')

            else:
                return redirect('/admin/')

        else:
            messages.info(request, 'Username OR password is incorrect')

    return render(request, 'pages/login.html', context={})


def index(request):
    return render(request, 'pages/index.html')

@login_required
def RacerDashboard(request):
    user = request.user

    # Only Racers can access
    if not user.is_Participant:
        return render(request, "403.html", {"error": "You are not authorized as a Racer."})
    print(1)
    # Get Racer profile
    racer_profile = get_object_or_404(Racer, user=user)
    print(2)
    # Stats
    stats = {
        "win_rate": f"{racer_profile.win_rate}%",
        "podium_rate": f"{racer_profile.podium_rate}%",
        "races_total": racer_profile.nbr_of_races,
        "podium": racer_profile.podium,
        "finished_first": racer_profile.finished_first,
    }

    # Pictures
    user_pictures = Pictures.objects.filter(user=user)

    context = {
        "profile": racer_profile,
        "stats": stats,
        "pictures": user_pictures,
    }

    return render(request, "racer/dashboard.html", context)

