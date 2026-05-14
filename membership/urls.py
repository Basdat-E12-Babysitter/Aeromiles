from django.urls import path
from . import views

app_name = "membership"

urlpatterns = [
    # Kelola Member (Staf)
    path("kelola/", views.kelola_member, name="kelola_member"),
    path("kelola/list/", views.get_members, name="get_members"),
    path("kelola/tambah/", views.tambah_member, name="tambah_member"),
    path("kelola/<str:email>/edit/", views.edit_member, name="edit_member"),
    path("kelola/<str:email>/hapus/", views.hapus_member, name="hapus_member"),

    # Identitas (Member)
    path("identitas/", views.identitas, name="identitas"),
    path("identitas/list/", views.get_identitas, name="get_identitas"),
    path("identitas/tambah/", views.tambah_identitas, name="tambah_identitas"),
    path("identitas/<str:nomor>/edit/", views.edit_identitas, name="edit_identitas"),
    path("identitas/<str:nomor>/hapus/", views.hapus_identitas, name="hapus_identitas"),
]