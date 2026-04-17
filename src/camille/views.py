from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView


class HomeView(LoginRequiredMixin, TemplateView):
    template_name = "camille/home.html"


class LogoutConfirmView(LoginRequiredMixin, TemplateView):
    template_name = "registration/logout_confirm.html"


class RegisterView(CreateView):
    template_name = "registration/register.html"
    form_class = UserCreationForm
    success_url = reverse_lazy("login")
