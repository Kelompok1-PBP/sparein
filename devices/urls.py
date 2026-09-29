from django.urls import path

from devices import views

app_name = "devices"
urlpatterns = [
    path("devices/", views.device_list, name="list"),
    path("devices/create/", views.device_create, name="create"),
    path("devices/<slug:slug>/", views.device_detail, name="detail"),
]
