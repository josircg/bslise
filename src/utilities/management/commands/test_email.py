from django.conf import settings
from eucs_platform import send_email
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    label = 'Test Email configuration'

    def handle(self, *args, **options):
        print(f'Sending to {settings.ADMINS}')
        send_email('Test', 'Test email', settings.ADMINS)
        print('Message sent!')
