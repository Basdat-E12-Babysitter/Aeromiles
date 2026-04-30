# rewards/urls.py
from django.urls import path
from django.views.generic import TemplateView

app_name = 'rewards'

urlpatterns = [
    path('redeem/', TemplateView.as_view(template_name='redeem_hadiah.html'), name='redeem_list'), 
    path('redeem/create/', TemplateView.as_view(template_name='redeem_hadiah.html'), name='redeem_create'),

    path('package/', TemplateView.as_view(template_name='beli_package.html'), name='package_list'),
    path('package/beli/', TemplateView.as_view(template_name='beli_package.html'), name='package_beli'),

    path('tier/', TemplateView.as_view(template_name='info_tier.html'), name='tier_info'),

    path('laporan/', TemplateView.as_view(template_name='laporan_transaksi.html'), name='laporan_transaksi'),
    path('laporan/hapus/', TemplateView.as_view(template_name='laporan_transaksi.html'), name='laporan_hapus'),
]