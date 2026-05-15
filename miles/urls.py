# miles/urls.py

from django.urls import path
from . import views

app_name = 'miles'

urlpatterns = [
    # Klaim missing miles (member)
    path('klaim/', views.klaim_list, name='klaim_list'),
    path('klaim/baru/', views.klaim_create, name='klaim_create'),
    path('klaim/<int:pk>/edit/', views.klaim_update, name='klaim_update'),
    path('klaim/<int:pk>/hapus/', views.klaim_delete, name='klaim_delete'),
    # Transfer miles (member)
    path('transfer/', views.transfer_list,   name='transfer_list'),
    path('transfer/baru/', views.transfer_create, name='transfer_create'),
    # Kelola miles (staff)
    path('kelola/', views.kelola_klaim, name='kelola_klaim'),
]