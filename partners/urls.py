from django.urls import path
from django.views.generic import TemplateView
from . import views

urlpatterns = [
    path('hadiah/', TemplateView.as_view(template_name='partners/kelola_hadiah.html')),
    path('mitra/', TemplateView.as_view(template_name='partners/kelola_mitra.html')),


    # Hadiah CUD
    path('hadiah/create/', views.create_hadiah, name='create_hadiah'),
    path('hadiah/update/<str:kode_hadiah>/', views.update_hadiah, name='update_hadiah'),
    path('hadiah/delete/<str:kode_hadiah>/', views.delete_hadiah, name='delete_hadiah'),

    # Mitra CUD
    path('mitra/create/', views.create_mitra, name='create_mitra'),
    path('mitra/update/<str:email_mitra>/', views.update_mitra, name='update_mitra'),
    path('mitra/delete/<str:email_mitra>/', views.delete_mitra, name='delete_mitra'),

]