from django.urls import path
from django.views.generic import TemplateView

app_name = "accounts"

urlpatterns = [
    path("login/", TemplateView.as_view(template_name="login.html"), name="login"),
    path("register/", TemplateView.as_view(template_name="register.html"), name="register"),
    path("member/", TemplateView.as_view(template_name="profile_member.html"), name="profile_member"),
    path("staf/", TemplateView.as_view(template_name="profile_staf.html"), name="profile_staf"),
]