from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from .models import Race

class OrganizerLockMiddleware:
    """
    Si un organisateur a une course passée non classée,
    il est redirigé vers la page de classement.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user
        if user.is_authenticated and hasattr(user, "organizer"):
            organizer = user.organizer

            pending_race = Race.objects.filter(
                organised_by=organizer,
                date__lte=timezone.now(),
                is_ranked=False
            ).first()

            if pending_race:
                manage_url = reverse("manage_race_results", args=[pending_race.pk])
                
                # 🚫 Empêche la boucle : si on est déjà sur la bonne page, ne pas rediriger
                if not request.path.startswith(manage_url):
                    return redirect(manage_url)

        return self.get_response(request)
