from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from camille.ai import create_pai_agent


class Command(BaseCommand):
    def handle(self, *args, **options):
        user = User.objects.get(username="jtremesay")
        agent = user.profile.default_agent
        pai_agent = create_pai_agent(agent)

        r = pai_agent.run_sync("bonjour")
        print(r.output)
