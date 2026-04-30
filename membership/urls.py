from django.urls import path
from django.views.generic import TemplateView

app_name = "membership"

urlpatterns = [
    path("kelola/", TemplateView.as_view(template_name="membership/kelola_member.html"), name="kelola_member"),
    path("identitas/", TemplateView.as_view(template_name="membership/identitas.html"), name="identitas"),
]