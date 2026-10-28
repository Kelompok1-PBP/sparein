from django.urls import path

from parts import views

app_name = "parts"
urlpatterns = [
    path("parts/", views.part_list, name="list"),
    path("parts/<slug:slug>/", views.part_detail, name="detail"),
]
