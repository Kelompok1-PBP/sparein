from django.urls import path

from diagnostics import views

app_name = "diagnostics"
urlpatterns = [
    path("diagnostics/", views.diagnose, name="list"),
    path("diagnostics/<slug:slug>/", views.symptom_detail, name="detail"),
    path("api/symptoms/", views.api_symptoms, name="api-symptoms"),
    path("api/diagnose/", views.api_diagnose, name="api-diagnose"),
]
