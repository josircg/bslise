from django.conf import settings
from eucs_platform import send_email
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    label = 'Test Email configuration'

    def handle(self, *args, **options):
        if settings.EMAIL_TAG == 'DEV':
            print('Dummy test - DEV TAG enabled')
        print(f'Trying to send to {settings.ADMIN_EMAIL}')
        send_email('Test', 'Test email', [settings.ADMIN_EMAIL])
        print('Message sent!')
