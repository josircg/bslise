from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.gis.db import models
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django_countries.fields import CountryField
from organisations.models import Organisation
from projects.models import Topic
from utilities.models import AbstractTranslatedModel

from .managers import GeographicExtendQuerySet


class Keyword(models.Model):
    keyword = models.TextField()

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return f'{self.keyword}'


class GeographicExtend(AbstractTranslatedModel):
    description = models.CharField(verbose_name=_('Description'), max_length=40, unique=True)

    str_field = 'description'

    objects = GeographicExtendQuerySet.as_manager()

    class Meta:
        verbose_name = _('Geographic extent')
        verbose_name_plural = _('Geographic extents')


class Platform(models.Model):
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=3000)
    url = models.URLField(max_length=200)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='platform_creator')
    dateCreated = models.DateTimeField('Created date', auto_now=True)
    dateUpdated = models.DateTimeField('Updated date', auto_now=True)
    geoExtend = models.ForeignKey(GeographicExtend, on_delete=models.PROTECT)
    countries = CountryField(multiple=True)
    keywords = models.ManyToManyField(Keyword, blank=True)

    # Contact information
    contactPoint = models.CharField(max_length=100, null=True, blank=True)
    contactPointEmail = models.EmailField(max_length=100, null=True, blank=True)
    contactPhone = models.CharField(_('Telephone'), max_length=20, null=True, blank=True)
    organisation = models.ManyToManyField(Organisation, blank=True)

    # Images
    logo = models.ImageField(upload_to='images/', max_length=300, null=True, blank=True)
    logoCredit = models.CharField(max_length=300, null=True, blank=True)
    profileImage = models.ImageField(upload_to='images/', max_length=300, null=True, blank=True)
    profileImageCredit = models.CharField(max_length=300, null=True, blank=True)

    topic = models.ManyToManyField(Topic, verbose_name=_('Topic'), blank=True)
    qualification = models.CharField(_('Qualification Required'), max_length=100, null=True, blank=True)

    approved = models.BooleanField(_('Approved'), null=True)
    active = models.BooleanField(blank=True, default=False)

    class Meta:
        verbose_name = _('Program')
        verbose_name_plural = _('Programmes')

    def __str__(self):
        return f'{self.name}'

    def safe_url(self):
        return mark_safe(f'<a href="/editPlatform/{self.id}" target="_blank">URL</a>')

    safe_url.allow_tags = True
    safe_url.short_description = 'Site URL'

    def organizations(self):
        return ",".join([p.name for p in self.organisation.all()])

    def save(self, *args, **kwargs):
        if not self.pk:
            self.active = self.creator.is_staff

        super().save(*args, **kwargs)
