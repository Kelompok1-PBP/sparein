from django.urls import path

from . import views

app_name = "journal"

urlpatterns = [
    path("", views.journal_list, name="list"), # melihat daftar jurnal
    path("create/", views.journal_create, name="create"), # membuat jurnal
    path("<int:pk>/", views.journal_detail, name="detail"), # melihat detail jurnal
    path("<int:pk>/edit/", views.journal_edit, name="edit"), # mengedit jurnal 
    path("<int:pk>/delete/", views.journal_delete, name="delete"), # menghapus jurnal
    path("<int:pk>/status/", views.journal_status, name="status"), # mengubah status catatan perbaikan dengan response JSON -> fitur fetch()
]
