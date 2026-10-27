from django.urls import path

from diagnostics import views

app_name = "diagnostics"
urlpatterns = [
    path("diagnostics/", views.diagnose, name="list"),
    path("diagnostics/my/sessions/", views.history, name="history"),
    path("diagnostics/symptoms/create/", views.symptom_create, name="create"),
    path("diagnostics/<slug:slug>/", views.symptom_detail, name="detail"),
    path("diagnostics/<slug:slug>/edit/", views.symptom_edit, name="edit"),
    path("diagnostics/<slug:slug>/delete/", views.symptom_delete, name="delete"),
    path("api/symptoms/", views.api_symptoms, name="api-symptoms"),
    path("api/diagnose/", views.api_diagnose, name="api-diagnose"),
    path("api/diagnose/save/", views.api_save, name="save"),
]
