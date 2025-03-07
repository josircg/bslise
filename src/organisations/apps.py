from django.apps import AppConfig
from django.db.models.signals import pre_save, post_save, post_delete
from django.utils.translation import ugettext_lazy as _

from .signals import notify_approved_organisation


class OrganisationsConfig(AppConfig):
    name = 'organisations'
    verbose_name = _('Organisations')

    def ready(self):
        super().ready()
        pre_save.connect(notify_approved_organisation, 'organisations.Organisation',
                         dispatch_uid='notify_approved_organisation')
