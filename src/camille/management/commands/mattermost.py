from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Mattermost agent"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Mattermost agent executed successfully."))
