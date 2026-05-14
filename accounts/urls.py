from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("login/",    views.login,         name="login"),
    path("logout/",   views.logout,         name="logout"),
    path("register/", views.register,       name="register"),
    path("member/",   views.profile_member, name="profile_member"),
    path("staf/",     views.profile_staf,   name="profile_staf"),
]