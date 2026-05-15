# rewards/urls.py
from django.urls import path
from django.views.generic import TemplateView
from . import views

app_name = 'rewards'

urlpatterns = [
    path('redeem/', views.redeem_hadiah, name='redeem_hadiah'),
    path('redeem/list/', views.redeem_hadiah, name='redeem_list'),

    path('package/', views.beli_package, name='package_list'),
    path('package/beli/', views.beli_package, name='package_beli'),

    path('tier/', views.info_tier, name='tier_info'),

    path('laporan/', TemplateView.as_view(template_name='laporan_transaksi.html'), name='laporan_transaksi'),
    path('laporan/hapus/', TemplateView.as_view(template_name='laporan_transaksi.html'), name='laporan_hapus'),
]