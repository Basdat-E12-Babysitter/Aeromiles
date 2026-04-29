from django.urls import path
from django.views.generic import TemplateView

app_name = "dashboard"

urlpatterns = [
    path("member/", TemplateView.as_view(template_name="dashboard/member/dashboard.html"), name="member"),
    path("staf/", TemplateView.as_view(template_name="dashboard/staf/dashboard.html"), name="staf"),
]