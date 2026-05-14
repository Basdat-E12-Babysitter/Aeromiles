from django.urls import path
from . import views

app_name = "dashboard"

urlpatterns = [
    path("member/", views.dashboard_member, name="member"),
    path("staf/",   views.dashboard_staf,   name="staf"),
]