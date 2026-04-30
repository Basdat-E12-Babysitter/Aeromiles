# miles/urls.py

from django.urls import path
from django.views.generic import TemplateView

app_name = 'miles'

urlpatterns = [
    path('klaim/', TemplateView.as_view(template_name='miles/claim_miles.html'), name='klaim_list'),
    path('klaim/baru/', TemplateView.as_view(template_name='miles/claim_miles.html'), name='klaim_create'),
    path('klaim/<int:pk>/hapus/', TemplateView.as_view(template_name='miles/claim_miles.html'), name='klaim_delete'),
    path('kelola/', TemplateView.as_view(template_name='miles/kelola_klaim.html'), name='kelola_klaim'),
    path('transfer/', TemplateView.as_view(template_name='miles/transfer_miles.html'), name='transfer_list'),
    path('transfer/baru/', TemplateView.as_view(template_name='miles/transfer_miles.html'), name='transfer_create'),

    path('redeem/', TemplateView.as_view(template_name='hadiah/redeem_hadiah.html'), name='redeem_list'), 
    path('package/', TemplateView.as_view(template_name='hadiah/beli_package.html'), name='package_list'),
    path('tier/', TemplateView.as_view(template_name='hadiah/info_tier.html'), name='tier_info'),
    path('laporan/', TemplateView.as_view(template_name='hadiah/laporan_transaksi.html'), name='laporan_transaksi'),

    path('redeem/create/', TemplateView.as_view(template_name='hadiah/redeem_hadiah.html'), name='redeem_create'),
    path('package/beli/', TemplateView.as_view(template_name='hadiah/beli_package.html'), name='package_beli'),
    path('laporan/hapus/', TemplateView.as_view(template_name='hadiah/laporan_transaksi.html'), name='laporan_hapus'),
]