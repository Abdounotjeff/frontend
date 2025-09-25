from django.contrib import admin
from .models import *
# Register your models here.

admin.site.register(CustomUser)
admin.site.register(Organizer)
admin.site.register(Racer)
admin.site.register(Race)
admin.site.register(Pictures)
admin.site.register(AllowedAge)
admin.site.register(Plan)
admin.site.register(Subscription)