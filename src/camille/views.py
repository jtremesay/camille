from django.views.generic import TemplateView


class MattermostLinkView(TemplateView):
    template_name = "camille/mattermost_link.html"
