from django.apps import AppConfig

from django.utils.translation import ugettext_lazy as _


class PlatformsConfig(AppConfig):
    name = 'platforms'
    verbose_name = _('Programmes')
