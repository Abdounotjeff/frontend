from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import get_user_model, authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.forms import inlineformset_factory
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Q
from .models import *
from .tokens import account_activation_token
from .forms import *
from django.core.mail import send_mail
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
        return redirect('profile', username = request.user.username)
    except Racer.DoesNotExist:
        pass  

    if request.method == 'POST':
        form = RacerForm(request.POST, request.FILES)  # ✅ include request.FILES
        if form.is_valid():
            racer = form.save(commit=False)
            racer.user = request.user
            racer.save()
            return redirect('profile', username = request.user.username)
        else:
            print(form.errors)  # ✅ show why it's failing
    else:
        form = RacerForm()

    return render(request, 'racer/create_profile.html', {'form': form})



@login_required
def createOrganizerProfile(request):
    try:
        request.user.organizer
        return redirect('profile', username = request.user.username)
    except Organizer.DoesNotExist:
        pass  

    if request.method == 'POST':
        form = OrganizerForm(request.POST, request.FILES)
        if form.is_valid():
            organizer = form.save(commit=False)
            organizer.user = request.user
            organizer.save()
            return redirect('profile', username = request.user.username)
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

        # ✅ Get all races this racer participated in
        participated_races = Race.objects.filter(racers=racer_profile).order_by("-date")

        race_table = []
        for race in participated_races:
            race_table.append({
                "title": race.title,
                "type": race.type,
                "place": race.place,
                "date": race.date.strftime("%Y-%m-%d %H:%M"),
                "status": race.get_status(),
                "organizer": race.organised_by.user.username,
                "pk": race.pk,
            })

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
            "races": race_table,   # ✅ Add race table to context
            "editable": is_self,   # ✅ editable only if it’s their own profile
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
                "pk" : race.pk,
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
                    "pk": most_popular_race.pk if most_popular_race else None
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
            "passed":race.date >= timezone.now()
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

def upload_picture(request):
    if request.method == 'POST':
        form = PicturesForm(request.POST, request.FILES)
        if form.is_valid():
            picture = form.save(commit=False)
            picture.user = request.user
            picture.save()
            return redirect("profile", username=request.user.username)  # change to your redirect
    else:
        form = PicturesForm()
    return render(request, 'pages/upload_picture.html', {'form': form})



def racers_list(request):
    racers = Racer.objects.select_related('user').all()
    return render(request, 'pages/racers_list.html', {'racers': racers})

def organizers_list(request):
    organizers = Organizer.objects.all()
    organizers_data = []

    for organizer in organizers:
        races = Race.objects.filter(organised_by=organizer)
        total_races = races.count()
        total_racers = sum(race.racers.count() for race in races)

        avg_racers = round(total_racers / total_races, 2) if total_races > 0 else 0

        organizers_data.append({
            "organizer": organizer,
            "total_races_hosted": total_races,
            "average_racers_per_race": avg_racers,
        })

    context = {"organizers_data": organizers_data}
    return render(request, "pages/organizers_list.html", context)


@login_required
def CreateRace(request):
    if not request.user.is_authenticated or not request.user.is_Organizer:
        return render(request, "404.html", {"error": "Oops, something went wrong."}, status=404)

    if request.method == 'POST':
        # ✅ form must be defined before checking .is_valid()
        form = RaceCreationForm(request.POST, request.FILES)
        if form.is_valid():
            race = form.save(commit=False)
            organizer = Organizer.objects.get(user=request.user)
            race.organised_by = organizer
            race.save()
            form.save_m2m()  # Save ManyToMany (Allowed_Ages etc.)

            # ✅ Notify racers by email (based on race type as speciality)
            participants_emails = CustomUser.objects.filter(
                role="Participant",
                racer__speciality=race.type
            ).values_list("email", flat=True)
            participants_emails = list(participants_emails)

            subject = f"You are invited to join {race.title}"
            message = (
                f"Hello racer!\n\n"
                f"The race '{race.title}' has been created by the organizer.\n"
                f"Details:\n"
                f"Title: {race.title}\n"
                f"Type: {race.type}\n"
                f"Place: {race.place}\n"
                f"Date: {race.date}\n\n"
                f"Please check your dashboard for more info.\n\n"
                f"— The Race Team"
            )

            if participants_emails:  # Avoid empty list
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    participants_emails,
                    fail_silently=True
                )

            return redirect("index")
        else:
            print(form.errors)

    else:
        form = RaceCreationForm()

    return render(request, 'pages/CreateRace.html', {'form': form})


def race_detail(request, pk):
    """
    Display detailed information about a specific race.
    """
    race = get_object_or_404(Race, pk=pk)
    try:
        racer = request.user
        already_joined = race.racers.filter(user=racer).exists()
    except:
        already_joined = False
        racer = None
    already_joined = race.racers.filter(user=racer).exists()
    context = {
        "race": race,
        "is_joined": already_joined
    }
    return render(request, "pages/raceDetails.html", context)


@login_required
def join_race(request, race_id):
    race = get_object_or_404(Race, id=race_id)

    # --- Normalize race.date to an aware datetime (end of day for DateField) ---
    race_dt = race.date

    # If it's a date (no time), treat as end of that day
    if isinstance(race_dt, date) and not isinstance(race_dt, datetime):
        # use time.max to consider the whole day (23:59:59.999999)
        race_dt = datetime.combine(race_dt, time.max)

    # If race_dt is still naive, make it timezone-aware using current timezone
    try:
        if timezone.is_naive(race_dt):
            race_dt = timezone.make_aware(race_dt, timezone.get_current_timezone())
    except Exception:
        # si pour une raison étrange race.date n'est pas un objet datetime/date,
        # on refuse proprement l'opération
        messages.error(request, "Date de course invalide.")
        return redirect("race_detail", pk=race.pk)

    # Compare with the current timezone-aware datetime
    if race_dt < timezone.now():
        messages.error(request, "Cette course est déjà terminée, vous ne pouvez plus la rejoindre.")
        return redirect("race_detail", pk=race.pk)

    # Vérifie si l'utilisateur a un profil Racer
    try:
        racer = request.user.racer
    except Racer.DoesNotExist:
        messages.error(request, "Seuls les coureurs peuvent rejoindre les courses.")
        return redirect("race_detail", pk=race.pk)

    # Vérifie si l'utilisateur est déjà inscrit (par user)
    already_joined = race.racers.filter(user=request.user).exists()

    if already_joined:
        messages.warning(request, "Vous avez déjà rejoint cette course.")
    else:
        race.racers.add(racer)
        racer.nbr_of_races += 1
        racer.save()
        messages.success(request, "Vous avez rejoint la course avec succès !")

    return redirect("pages/raceDetails", pk=race.pk)


@login_required
def modify_race(request, pk):
    race = get_object_or_404(Race, pk=pk)

    # ✅ Bloquer la modification si la course est passée
    if race.date <= timezone.now():
        return render(request, "403.html", {
            "error": "Vous ne pouvez plus modifier cette course car elle est déjà passée."
        }, status=403)

    # ✅ Vérifier que l'utilisateur est un organisateur
    if not hasattr(request.user, "organizer"):
        return render(request, "403.html", {
            "error": "Vous devez être un organisateur pour modifier une course."
        }, status=403)

    # ✅ Vérifier qu'il est bien l'organisateur de cette course
    if race.organised_by.user != request.user:
        return render(request, "403.html", {
            "error": "Vous ne pouvez modifier que vos propres courses."
        }, status=403)

    race_title = race.title

    # ✅ Get emails of all participants of this race
    participants_emails = CustomUser.objects.filter(
        racer__in=race.racers.all(),
        role="Participant"
    ).values_list("email", flat=True)
    participants_emails = list(participants_emails)

    # ✅ Gestion du formulaire
    if request.method == "POST":
        form = RaceCreationForm(request.POST, instance=race)
        if form.is_valid():
            form.save()

            # ✅ Notify racers by email
            subject = f"Update on {race_title}"
            message = (
                f"Hello racer!\n\n"
                f"The race '{race_title}' has been updated by the organizer.\n"
                f"New details:\n"
                f"Title: {race.title}\n"
                f"Type: {race.type}\n"
                f"Place: {race.place}\n"
                f"Date: {race.date}\n\n"
                f"Please check your dashboard for more info.\n\n"
                f"— The Race Team"
            )

            if participants_emails:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    participants_emails,
                    fail_silently=True
                )

            return redirect("profile", username=request.user.username)
    else:
        form = RaceCreationForm(instance=race)

    return render(request, "pages/EditRace.html", {"form": form, "race_pk": race.pk})


@login_required
def delete_race(request, pk):
    race = get_object_or_404(Race, pk=pk)

    # ✅ Get all participant emails (same logic as modify)
    participants_emails = CustomUser.objects.filter(
        racer__in=race.racers.all(),
        role="Participant"
    ).values_list("email", flat=True)
    participants_emails = list(participants_emails)

    # ✅ Only the organizer who created the race can delete it
    if request.user.username == race.organised_by.user.username and request.user.is_Organizer:
        if request.method == "POST":
            race_title = race.title  # store title before deletion
            race.delete()

            # ✅ Notify racers via email
            subject = f"Race '{race_title}' has been cancelled"
            message = (
                f"Hello racer,\n\n"
                f"We regret to inform you that the race '{race_title}' "
                f"has been cancelled by the organizer.\n\n"
                f"Thank you for your understanding.\n\n"
                f"— The Race Team"
            )

            if participants_emails:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    participants_emails,
                    fail_silently=True
                )

            return redirect("profile", username=request.user.username)

        # ✅ If GET request, confirm deletion first
        return render(request, "pages/DeleteRace.html", {"race": race})

    # ❌ Unauthorized access
    return render(request, "403.html", {"error": "You are not allowed to delete this race."}, status=403)


def races_list(request):
    q = request.GET.get("q")
    category = request.GET.get("category")
    sort = request.GET.get("sort")

    # Base queryset
    races = Race.objects.all()

    # 🔍 Search
    if q:
        races = races.filter(
            Q(title__icontains=q) |
            Q(type__icontains=q) |
            Q(place__icontains=q)
        )

    # 🏷️ Category filter
    if category:
        races = races.filter(type=category)

    # 📊 Sorting logic
    if sort == "popular":
        # Annotate with racer count for popularity
        races = races.annotate(racer_count=Count("racers")).order_by("-racer_count")
    elif sort == "relevance":
        races = races.order_by("title")
    elif sort == "date":
        races = races.order_by("-date")
    elif sort == "region":
        races = races.order_by("place")
    else:
        races = races.order_by("-date")

    # Pagination
    paginator = Paginator(races, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Categories
    categories = Race.objects.values("type").annotate(count=Count("id")).order_by("type")

    context = {
        "races": page_obj,
        "page_obj": page_obj,
        "is_paginated": page_obj.has_other_pages(),
        "categories": [{"name": c["type"], "count": c["count"]} for c in categories],
        "sort_options": ["popular", "relevance", "date", "region"],
        "request": request,
    }
    return render(request, "pages/races.html", context)

@login_required
def manage_race_results(request, pk):
    race = get_object_or_404(Race, pk=pk, organised_by__user=request.user)
    racers = race.racers.all()

    if request.method == "POST":
        form = RankingForm(request.POST, racers=racers)
        if form.is_valid():
            # Extraire tous les rangs soumis
            ranking_data = {}
            for racer in racers:
                rank = form.cleaned_data.get(f'rank_{racer.id}')
                if rank:
                    ranking_data[racer] = rank

            # Trier les participants selon leur rang
            sorted_racers = sorted(ranking_data.items(), key=lambda x: x[1])

            # Mettre à jour les statistiques
            for idx, (racer, rank) in enumerate(sorted_racers, start=1):
                racer.nbr_of_races += 1

                # 1ère place
                if rank == 1:
                    racer.finished_first += 1
                    racer.podium += 1

                # 2e ou 3e place
                elif rank in [2, 3]:
                    racer.podium += 1

                racer.save()
            race.is_ranked = True
            race.save()
            return redirect('race_detail', pk=race.pk)

    else:
        form = RankingForm(racers=racers)

    return render(request, "organizer/manage_race_results.html", {
        "race": race,
        "racers": racers,
        "form": form
    })

def race_results_view(request, pk):
    race = get_object_or_404(Race, pk=pk)
    results = RaceResult.objects.filter(race=race).select_related("racer__user").order_by("rank")

    context = {
        "race": race,
        "results": results,
    }
    return render(request, "pages/race_results.html", context)

@login_required
def race_participants_list(request, pk):
    race = get_object_or_404(Race, pk=pk)

    # 🔒 Vérifier que l'utilisateur est bien l'organisateur de cette course
    if not hasattr(request.user, "organizer") or race.organised_by.user != request.user:
        return render(request, "403.html", {
            "error": "Vous n'êtes pas autorisé à consulter la liste des participants de cette course."
        }, status=403)

    # ✅ Récupérer les participants avec leurs infos
    participants = race.racers.select_related("user").all()

    context = {
        "race": race,
        "participants": participants,
    }

    return render(request, "pages/race_participants_list.html", context)