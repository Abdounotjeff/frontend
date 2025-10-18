from django.contrib.auth.models import AbstractUser,User
from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
# Create your models here.

ROLE_CHOICES = (
        ("Organizer","Organizer"),
        ("Participant","Participant"),
    )

TYPE = (
    ("Cycling","Cycling"),
    ("Triathlon","Triathlon"),
    ("Marathon","Marathon"),
    ("Swimming","Swimming"),
    ("Crossfit","Crossfit"),
    ("Calisthenics","Calisthenics"),
    ("Rally Racing","Rally Racing"),
    ("Moto GP","Moto GP"),
)
###############  USERS Model here ###################################
class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    role = models.CharField(choices=ROLE_CHOICES, default="Participant", null=False, blank=False, max_length=20)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.username

    @property
    def is_Organizer(self):
        return self.role == "Organizer"
    
    @property
    def is_Participant(self):
        return self.role == "Participant"
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def has_active_subscription(self):
        return self.subscription_set.filter(end_date__gte=timezone.now()).exists()

    

class Organizer(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    tel = models.CharField(max_length=10,default="+213")
    carte_biometrique = models.ImageField(null=True)
    date_joined = models.DateField(auto_now_add=True)
    pfp = models.ImageField(upload_to="pfp", default="img/pfp.webp")
    bio = models.TextField(default="Hi, I make racing events!", null=True)

    def __str__(self):
        return self.user.username
    
    def getPictures(self):
        return Pictures.objects.filter(user=self.user)
    
class Racer(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    tel = models.CharField(max_length=10,default="+213")
    carte_biometrique = models.ImageField(null=True)
    date_joined = models.DateField(auto_now_add=True)
    pfp = models.ImageField(upload_to="pfp", null=True)
    bio = models.TextField(default="Hi, I love racing!", null=True)
    date_birth = models.DateField(null=True)
    podium = models.IntegerField(default=0)
    finished_first = models.IntegerField(default=0)
    nbr_of_races = models.IntegerField(default=0)
    speciality = models.CharField(choices=TYPE, max_length=20, default="Cycling")

    @property
    def win_rate(self):
        if self.nbr_of_races == 0:
            return 0
        return round((self.finished_first / self.nbr_of_races) * 100, 2)

    @property
    def podium_rate(self):
        if self.nbr_of_races == 0:
            return 0
        return round((self.podium / self.nbr_of_races) * 100, 2)

    def getUpcomingRaces(self):
        return Race.objects.filter(racers=self, raceinstance__date__gte=timezone.now())  # if RaceInstance model exists



    def __str__(self):
        return self.user.username
    
    def getPictures(self):
        return Pictures.objects.filter(user=self.user)
    

############################################################

####################### PICTURES TABLE RELATED TO CUSTOMUSER MODEL ################

class Pictures(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    IMG = models.ImageField()

    def __str__(self):
        return self.user.username
    @property
    def url(self):
        if self.IMG and hasattr(self.IMG, 'url'):
            return self.IMG.url
        return ''
    


    
###################### RACE MODEL ########################

class AllowedAge(models.Model):
    name = models.CharField(max_length=10)

    def __str__(self):
        return f"Age Category: {self.name}"


class Race(models.Model):
    organised_by = models.ForeignKey(Organizer, on_delete=models.CASCADE)
    racers = models.ManyToManyField(Racer)
    type = models.CharField(choices=TYPE, max_length=20)
    title = models.CharField(max_length=100)
    rules = models.TextField()
    description = models.TextField()
    place = models.CharField(max_length=400) #this field to define a link to google maps
    wilaya = models.CharField(max_length=20, default="Annaba")
    Allowed_Ages = models.ManyToManyField(AllowedAge)
    date = models.DateTimeField(default=timezone.now)
    logo = models.ImageField()
    price = models.IntegerField(default=0)

    def __str__(self):
        return self.title
    
    def get_status(self):
        return "Upcoming" if self.date >= timezone.now() else "Past"
    
    def getRacers(self):
        return self.racers
    
    def participant_count(self):
        return self.racers.count()

    def getAllowedAgesAsList(self):
        return list(self.Allowed_Ages.values_list("name", flat=True))
    def get_embed_map_url(self):
        """
        Retourne un lien d'intégration Google Maps (ou OpenStreetMap si non supporté)
        """
        if not self.place:
            return None

        # Si le lien est déjà un embed, on le garde
        if "google.com/maps/embed" in self.place:
            return self.place

        # Si c’est un lien Google Maps normal
        if "google.com/maps" in self.place or "goo.gl/maps" in self.place:
            return self.place.replace("/maps/", "/maps/embed/")

        # Sinon on retourne None (ou une carte OSM par défaut)
        return "https://www.openstreetmap.org/export/embed.html?bbox=2.8,36.7,3.2,36.9&layer=mapnik"

    
######################## PLAN and SUBSCRIPTION ################

class Plan(models.Model):
    name = models.CharField(max_length=50)  # e.g., Free, Pro
    price = models.DecimalField(max_digits=6, decimal_places=2)
    duration_days = models.IntegerField()  # e.g., 30 for a monthly plan
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Subscription(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    plan = models.ForeignKey(Plan, on_delete=models.SET_NULL, null=True)
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField()

    @property
    def days_left(self):
        remaining = self.end_date - timezone.now()
        return remaining.days if remaining.days > 0 else 0

    def renew(self):
        self.start_date = timezone.now()
        self.end_date = self.start_date + timedelta(days=self.plan.duration_days)
        self.save()

    def is_active(self):
        return self.end_date >= timezone.now()

    def cancel(self):
        
        self.end_date = timezone.now()
        self.save()

    def __str__(self):
        return f"{self.user.username} - {self.plan.name}"
    
    def save(self, *args, **kwargs):
        if self.user.role != "Organiser":
            raise ValueError("Only organizers can have subscriptions.")
        if not self.end_date:
            self.end_date = self.start_date + timedelta(days=self.plan.duration_days)
        super().save(*args, **kwargs)

    
########################################################################

