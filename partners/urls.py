from django.urls import path
from django.views.generic import TemplateView

urlpatterns = [
    path('hadiah/', TemplateView.as_view(template_name='partners/kelola_hadiah.html')),
    path('mitra/', TemplateView.as_view(template_name='partners/kelola_mitra.html')),
]