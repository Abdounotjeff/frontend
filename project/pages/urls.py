from django.urls import path
from . import views


urlpatterns = [
    path('register/',views.registerPage , name='registerPage'),
    path('activate/<uidb64>/<token>/', views.activateEmail, name='activate'),
    path('login/', views.loginPage, name='loginPage'),
    path('RacerDashboard/', views.RacerDashboard, name='RacerDashboard'),
    path('activateEmail', views.activ, name='activ'),
    # path('OrganizerDashboard/', OrganizerDashboard.as_view(), name="organizer-dashboard"),
    # path('organizer/public/<str:username>/', PublicOrganizerProfile.as_view(), name='public-organizer-profile'),
    # path('organizer/profile/edit/', OrganizerProfileUpdate.as_view(), name='organizer-profile-update'),
    # path('races/create/', CreateRaceView.as_view(), name='race-create'),
    # path('races/<int:pk>/edit/', UpdateRaceView.as_view(), name='race-edit'),
    # path('races/<int:pk>/delete/', DeleteRaceView.as_view(), name='race-delete'),
    # path('racer/profile/',RacerDashboard.as_view(), name='racer-profile'),
    # path('racer/public/<str:username>/', PublicRacerProfileView.as_view(), name='public-racer-profile'),
    # path('racer/profile/edit/', RacerProfileUpdate.as_view(), name='racer-profile-update'),
    # path('pictures/racer/<str:username>/', RacerPicturesView.as_view(), name='racer-pictures'),
    # path('leaderboard/global/', GlobalLeaderboardView.as_view(), name='global_leaderboard'),
    # path('leaderboard/category/<str:category>/', CategoryLeaderboardView.as_view(), name='category_leaderboard'),
    # path('api/subscribe/', SubscribeView.as_view()),
    # path('api/chargily/webhook/', chargily_webhook),
    # path('api/subscription/my/', MySubscriptionView.as_view(), name='my-subscription'),

]