from datetime import datetime, timedelta

from captcha.management.commands.captcha_clean import Command as CaptchaCommand
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import EmailMessage
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils import timezone
from django_cron import CronJobBase, Schedule
from django.core import management

User = get_user_model()


class CleanExpiredCaptchaCronJob(CronJobBase):
    """Clean expired captcha every day"""
    RUN_EVERY_MINS = 24 * 60

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'eucs_platform.clean_expired_captcha'

    def do(self):
        CaptchaCommand().handle()


class ClearSessions(CronJobBase):
    """Clear sessions expired every day"""
    RUN_EVERY_MINS = 24 * 60

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'django.clearsessions'

    def do(self):
        management.call_command("clearsessions", verbosity=2)


