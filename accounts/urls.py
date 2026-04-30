from django.urls import path
from django.views.generic import TemplateView

app_name = "accounts"

urlpatterns = [
    path("login/", TemplateView.as_view(template_name="login.html"), name="login"),
    path("registrasi/", TemplateView.as_view(template_name="registrasi.html"), name="register"),
    path("profile/", TemplateView.as_view(template_name="profile.html", name="profile")),
]