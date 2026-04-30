# miles/urls.py

from django.urls import path
from django.views.generic import TemplateView

app_name = 'miles'

urlpatterns = [
    path('klaim/', TemplateView.as_view(template_name='miles/claim_miles.html'), name='klaim_list'),
    path('klaim/baru/', TemplateView.as_view(template_name='miles/claim_miles.html'), name='klaim_create'),
    path('klaim/<int:pk>/hapus/', TemplateView.as_view(template_name='miles/claim_miles.html'), name='klaim_delete'),
    path('kelola/', TemplateView.as_view(template_name='miles/kelola_klaim.html'), name='kelola_klaim'),
]