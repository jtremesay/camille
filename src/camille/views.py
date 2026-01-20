from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


@login_required
def view_profile(request: HttpRequest) -> HttpResponse:
    return render(request, "camille/profile.html")


@login_required
def view_logout(request: HttpRequest) -> HttpResponse:
    return render(request, "camille/logout.html")
