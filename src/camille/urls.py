"""
URL configuration for proj project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import include, path

from camille import views

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    # Personality management
    path(
        "personalities/create/",
        views.PersonalityCreateView.as_view(),
        name="personality_create",
    ),
    path(
        "personalities/<int:pk>/update/",
        views.PersonalityUpdateView.as_view(),
        name="personality_update",
    ),
    path(
        "personalities/<int:pk>/delete/",
        views.PersonalityDeleteView.as_view(),
        name="personality_delete",
    ),
    # Mattermost integration
    path(
        "mattermost/bind/",
        views.MattermostBindCreateView.as_view(),
        name="mattermost_bind",
    ),
    path(
        "mattermost/unbind/",
        views.MattermostBindDeleteView.as_view(),
        name="mattermost_unbind",
    ),
    # Account management
    path("accounts/register/", views.RegisterView.as_view(), name="register"),
    path(
        "accounts/logout_confirm/",
        views.LogoutConfirmView.as_view(),
        name="logout_confirm",
    ),
    path(
        "accounts/update/",
        views.ProfileUpdateView.as_view(),
        name="profile_update",
    ),
    path("accounts/", include("django.contrib.auth.urls")),
    # Admin site
    path("admin/", admin.site.urls),
]
