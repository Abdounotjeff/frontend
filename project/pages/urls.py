from django.urls import path
from . import views
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('register/',views.registerPage , name='registerPage'),
    path('activate/<uidb64>/<token>/', views.activateEmail, name='activate'),
    path('login/', views.loginPage, name='loginPage'),
    path('logout/', views.logout_view, name='logout'),
    path('activateEmail/', views.activ, name='activ'),
    path('',views.index, name='index'), 
    path('createRacerProfile/', views.createRacerProfile, name="createRacerProfile"),
    path('createOrganizerProfile/', views.createOrganizerProfile, name="createOrganizerProfile"),
    path('editProfile/',views.editProfile, name='editProfile'),
    path('editUser/',views.editUser, name='editUser'),
    path('editUser/passwordChange/',views.change_password, name='passwordChange'),
    path('uploadPicture/',views.upload_picture, name='uploadPicture'),
    path('racers/',views.racers_list, name='racers'),
    path('organizers', views.organizers_list, name='organizers'),
    path('<str:username>/',views.profile, name='profile'),
    path('password/reset/', auth_views.PasswordResetView.as_view(
        template_name='users/password_reset.html',
        email_template_name='users/password_reset_email.html',
        subject_template_name='users/password_reset_subject.txt',
        success_url='done/'
    ), name='password_reset'),

    path('password/reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='users/password_reset_done.html'
    ), name='password_reset_done'),

    path('password/reset/confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='users/password_reset_confirm.html',
        success_url='/users/password/reset/complete/'
    ), name='password_reset_confirm'),

    path('users/password/reset/complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='users/password_reset_complete.html'
    ), name='password_reset_complete'),
    
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