from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import get_user_model, authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.forms import inlineformset_factory
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib import messages
from .models import *
from .tokens import account_activation_token
from .forms import *
from django.core.mail import EmailMessage, get_connection
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
    except:
        user = None
    
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, "Merce d'avoir vérifier votre Email!, tu peux s'incrire maintenant!")
        return redirect('loginPage')
    else:
        messages.error(request, "Lien d'activation est invalide!")
    
    return redirect('registerPage')
##################################################################################

def send_activation_email(request, user, to_email):
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



##################################################################################



@login_required
def createRacerProfile(request):
    try:
        # Prevent already created profile
        request.user.racer
        return redirect('RacerDashboard')
    except Racer.DoesNotExist:
        pass  

    if request.method == 'POST':
        form = RacerForm(request.POST, request.FILES)  # ✅ include request.FILES
        if form.is_valid():
            racer = form.save(commit=False)
            racer.user = request.user
            racer.save()
            return redirect('RacerDashboard')
        else:
            print(form.errors)  # ✅ show why it's failing
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
        form = OrganizerForm(request.POST, request.FILES)
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
    if request.user.is_authenticated:
        return redirect('profile', username=request.user.username)
    elif request.method == 'POST':
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
    if request.user.is_authenticated:
        return redirect('profile', username=request.user.username)
    elif request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_active:
            login(request, user)

            if user.is_Participant:
                if not Racer.objects.filter(user=user).exists():
                    return redirect('createRacerProfile')
                return redirect('profile', username=user.username)

            elif user.is_Organizer:
                if not Organizer.objects.filter(user=user).exists():
                    return redirect('createOrganizerProfile')
                return redirect('profile', username=user.username)

            else:
                return redirect('/admin/')

        else:
            messages.info(request, 'Username OR password is incorrect')

    return render(request, 'pages/login.html', context={})


def logout_view(request):
    logout(request)
    return redirect('loginPage')


def send_email(to_email, msg):
    mail_subject = "RACER Contact"
    email = EmailMessage(
        subject=mail_subject,
        body=msg,
        to=[to_email],
        connection=get_connection()
    )
    return email.send()

def index(request):
    if request.method == 'POST':
        username = request.POST.get('name')     # matches <input name="name">
        email = request.POST.get('email')      # matches <input name="email">
        message = request.POST.get('message')  # matches <textarea name="message">

        # Construct the message you want to send
        full_message = f"Message from {username} ({email}):\n\n{message}"

        try:
            # Example: send message to your admin email
            send_email("bajpremium@gmail.com", full_message)
            messages.success(request, "Your message has been sent successfully!")
        except Exception as e:
            messages.error(request, f"An error occurred: {e}")

        return redirect("index")  # prevent resubmission on refresh

    return render(request, 'pages/index.html')


@login_required
def profile(request, username):
    profile_user = get_object_or_404(CustomUser, username=username)  # user being visited
    request_user = request.user  # user making the request

    # Condition flags
    is_self = profile_user == request_user
    is_participant = profile_user.is_Participant
    is_organizer = profile_user.is_Organizer

    # Case 1 & 2 → Participant profiles
    if is_participant:
        try:
            racer_profile = Racer.objects.get(user=profile_user)
        except Racer.DoesNotExist:
            return render(request, "404.html", {"error": "Racer profile not found."}, status=404)

        stats = {
            "win_rate": f"{racer_profile.win_rate}%",
            "podium_rate": f"{racer_profile.podium_rate}%",
            "races_total": racer_profile.nbr_of_races,
            "podium": racer_profile.podium,
            "finished_first": racer_profile.finished_first,
        }

        pictures = Pictures.objects.filter(user=profile_user)

        context = {
            "profile": racer_profile,
            "stats": stats,
            "pictures": pictures,
            "editable": is_self,  # ✅ editable only if it’s their own profile
        }

        return render(request, "pages/racer.html", context)

    # Case 3 & 4 → Organizer profiles
    elif is_organizer:
        try:
            organizer_profile = Organizer.objects.get(user=profile_user)
        except Organizer.DoesNotExist:
            return render(request, "404.html", {"error": "Organizer profile not found."}, status=404)

        races = Race.objects.filter(organised_by=organizer_profile).order_by("-date")
        total_races = races.count()

        race_table, total_signups, most_popular_race, most_racers = [], 0, None, 0
        for race in races:
            num_racers = race.racers.count()
            total_signups += num_racers

            race_data = {
                "title": race.title,
                "type": race.type,
                "place": race.place,
                "date": race.date.strftime("%Y-%m-%d %H:%M"),
                "status": race.get_status(),
                "racers_count": num_racers,
            }
            race_table.append(race_data)

            if num_racers > most_racers:
                most_racers = num_racers
                most_popular_race = race

        top_races = sorted(race_table, key=lambda x: x["racers_count"], reverse=True)[:3]

        context = {
            "analytics": {
                "total_signups": total_signups,
                "most_popular_race": {
                    "title": most_popular_race.title if most_popular_race else None,
                    "racers_count": most_racers,
                    "date": most_popular_race.date.strftime("%Y-%m-%d") if most_popular_race else None,
                } if most_popular_race else {},
                "average_racers_per_race": round(total_signups / total_races, 2) if total_races > 0 else 0,
                "top_races": top_races,
            },
            "organizer": {
                "id": organizer_profile.user.id,
                "role": profile_user.role,
                "pfp": organizer_profile.pfp.url if organizer_profile.pfp else None,
                "username": profile_user.username,
                "full_name": f"{profile_user.first_name} {profile_user.last_name}".strip(),
                "email": profile_user.email,
                "tel": organizer_profile.tel,
                "bio": organizer_profile.bio,
                "date_joined": organizer_profile.date_joined,
                "location": race_table[0]["place"] if race_table else "N/A",
                "total_races_hosted": total_races,
            },
            "races": race_table,
            "editable": is_self,  # ✅ editable only if it’s their own profile
        }

        return render(request, "pages/organizer.html", context)

    else:
        return render(request, "403.html", {"error": "Unknown role."}, status=403)
    

@login_required
def editProfile(request):
    user = request.user  # logged-in user

    # If user is a participant (Racer)
    if user.is_Participant:
        racer_profile = get_object_or_404(Racer, user=user)

        if request.method == "POST":
            form = RacerForm(request.POST, request.FILES, instance=racer_profile)
            if form.is_valid():
                form.save()
                return redirect("profile", username=user.username)
        else:
            form = RacerForm(instance=racer_profile)

        return render(request, "pages/edit_profile.html", {"form": form, "role": "Racer"})

    # If user is an organizer
    elif user.is_Organizer:
        organizer_profile = get_object_or_404(Organizer, user=user)

        if request.method == "POST":
            form = OrganizerForm(request.POST, request.FILES, instance=organizer_profile)
            if form.is_valid():
                form.save()
                return redirect("profile", username=user.username)
        else:
            form = OrganizerForm(instance=organizer_profile)

        return render(request, "pages/edit_profile.html", {"form": form, "role": "Organizer"})

    else:
        return render(request, "403.html", {"error": "You are not allowed to edit profiles."}, status=403)
    
@login_required
def editUser(request):
    user = request.user  # logged-in user

    if request.method == "POST":
        form = EditUserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            user.is_active = False
            user.save()
            email = form.cleaned_data.get('email')
            request.session['pending_email'] = email  # Store email in session
            send_activation_email(request, user, email)
            # Create role-specific object
           
            return redirect('activ')
    else:
        form = EditUserForm(instance=user)

    return render(request, "pages/edit_user.html", {"form": form})


@login_required
def change_password(request):
    if request.method == "POST":
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            # Keep user logged in after password change
            update_session_auth_hash(request, user)
            return redirect("profile", username=request.user.username)
    else:
        form = PasswordChangeForm(user=request.user)

    return render(request, "pages/change_password.html", {"form": form})