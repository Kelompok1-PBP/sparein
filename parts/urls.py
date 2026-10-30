from django.urls import path

from parts import views

app_name = "parts"
urlpatterns = [
    path("parts/", views.part_list, name="list"),
    # create dan sync harus di atas <slug> biar ga dianggap slug
    path("parts/create/", views.part_create, name="create"),
    path("parts/sync/", views.part_sync, name="sync"),
    path("parts/<slug:slug>/", views.part_detail, name="detail"),
    path("parts/<slug:slug>/edit/", views.part_edit, name="edit"),
    path("parts/<slug:slug>/delete/", views.part_delete, name="delete"),
    path("api/parts/", views.part_api, name="api"),
]
