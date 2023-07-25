from django.contrib import admin
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import ugettext as _

from .models import *


class SubscriberAdmin(admin.ModelAdmin):
    list_filter = ('valid', 'opt_out')
    search_fields = ('name', 'email','organisation')
    list_display = ('name', 'email', 'valid', 'opt_out', 'organisation', 'dateCreated', )
    exclude = ('last_newsletter',)


class NewsletterAdmin(admin.ModelAdmin):
    list_display = ('title', 'dateCreated', 'status',)

    def get_view_on_site_url(self, obj):
        self.view_on_site = obj and obj.html
        return super().get_view_on_site_url(obj)

admin.site.register(Subscriber, SubscriberAdmin)
admin.site.register(Newsletter, NewsletterAdmin)
