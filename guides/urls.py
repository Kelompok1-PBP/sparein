from django.urls import path

from . import views

app_name = "guides"
urlpatterns = [
    path("import/", views.guide_import, name="import"),
    path("", views.guide_list, name="list"),
    path("create/", views.guide_create, name="create"),
    path("<slug:slug>/", views.guide_detail, name="detail"),
    path("<slug:slug>/edit/", views.guide_edit, name="edit"),
    path("<slug:slug>/delete/", views.guide_delete, name="delete"),
]
