from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, TemplateView, UpdateView

from camille.models import AgentConfig, AgentPersonality, MattermostBinding


class HomeView(LoginRequiredMixin, TemplateView):
    template_name = "camille/home.html"


class AgentConfigEditView(LoginRequiredMixin, UpdateView):
    model = AgentConfig
    fields = ["model", "personality", "instructions", "notes"]
    # template_name = "camille/agent_config_form.html"
    success_url = reverse_lazy("home")

    def get_object(self, queryset=None):
        return AgentConfig.objects.get(user=self.request.user)


class AgentPersonalityCreateView(LoginRequiredMixin, CreateView):
    model = AgentPersonality
    fields = ["name", "description", "prompt_template"]
    success_url = reverse_lazy("home")

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class AgentPersonalityUpdateView(LoginRequiredMixin, UpdateView):
    model = AgentPersonality
    fields = ["name", "description", "prompt_template"]
    success_url = reverse_lazy("home")

    def get_queryset(self):
        return AgentPersonality.objects.filter(user=self.request.user)


class AgentPersonalityDeleteView(LoginRequiredMixin, DeleteView):
    model = AgentPersonality
    success_url = reverse_lazy("home")

    def get_queryset(self):
        return AgentPersonality.objects.filter(user=self.request.user)


class MattermostBindCreateView(LoginRequiredMixin, TemplateView):
    template_name = "camille/mattermost_bind.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["mattermost_user_id"] = kwargs.get("mattermost_user_id")
        return context

    def get(self, request, *args, **kwargs):
        # Check if user is already bound to a Mattermost account
        if MattermostBinding.objects.filter(user=self.request.user).exists():
            kwargs["error"] = "Your account is already linked to a Mattermost account."
            return super().get(request, *args, **kwargs)

        # Get token from query parameters
        token = request.GET.get("token")
        if token is None:
            kwargs["error"] = "No token provided. Please use the link sent by the bot."
            return super().get(request, *args, **kwargs)

        # Validate token
        signer = TimestampSigner()
        try:
            mm_id = signer.unsign_object(token, max_age=60 * 5)["mm_id"]
        except SignatureExpired:
            kwargs["error"] = (
                "Token has expired. Please request a new link from the bot."
            )
            return super().get(request, *args, **kwargs)
        except BadSignature:
            kwargs["error"] = "Invalid token. Please use the link sent by the bot."
            return super().get(request, *args, **kwargs)

        # Check if mm_id is already used
        if MattermostBinding.objects.filter(mm_id=mm_id).exists():
            kwargs["error"] = (
                "This Mattermost account is already linked to another user account."
            )
            return super().get(request, *args, **kwargs)

        # Create binding
        MattermostBinding.objects.create(user=self.request.user, mm_id=mm_id)

        return super().get(request, *args, **kwargs)


class MattermostBindDeleteView(LoginRequiredMixin, DeleteView):
    model = MattermostBinding
    success_url = reverse_lazy("home")

    def get_object(self, queryset=None):
        return MattermostBinding.objects.get(user=self.request.user)


class LogoutConfirmView(LoginRequiredMixin, TemplateView):
    template_name = "registration/logout_confirm.html"


class RegisterView(CreateView):
    template_name = "registration/register.html"
    form_class = UserCreationForm
    success_url = reverse_lazy("login")


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    fields = ["first_name", "last_name"]
    template_name = "registration/update.html"
    success_url = reverse_lazy("home")

    def get_object(self, queryset=None):
        return self.request.user
