from django.urls import path

from devices import views

app_name = "devices"
urlpatterns = [
    path("devices/", views.device_list, name="list"),
]
