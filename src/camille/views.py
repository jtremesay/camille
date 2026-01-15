from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


def view_profile(request: HttpRequest) -> HttpResponse:
    return render(request, "camille/profile.html")


def view_logout(request: HttpRequest) -> HttpResponse:
    return render(request, "camille/logout.html")
