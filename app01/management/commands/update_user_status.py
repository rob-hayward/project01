from django.core.management.base import BaseCommand
from app01.models import UserProfile


class Command(BaseCommand):
    help = 'Updates user status based on last visit'

    def handle(self, *args, **options):
        for profile in UserProfile.objects.all():
            profile.check_user_status()
        self.stdout.write(self.style.SUCCESS('Successfully updated user statuses'))
