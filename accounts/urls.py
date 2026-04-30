from django.urls import path
from django.views.generic import TemplateView

app_name = "accounts"

urlpatterns = [
    path("login/", TemplateView.as_view(template_name="login.html"), name="login"),
    path("registrasi/", TemplateView.as_view(template_name="registrasi.html"), name="register"),
    path("profile/member/", TemplateView.as_view(template_name="profile_member.html"), name="profile_member"),
    path("profile/staf/", TemplateView.as_view(template_name="profile_staf.html"), name="profile_staf"),
]