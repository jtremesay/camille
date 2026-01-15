from django.urls import path

from . import views

app_name = "camille"
urlpatterns = [
    path("profile/", views.view_profile, name="view_profile"),
    path("logout/", views.view_logout, name="view_logout"),
]
