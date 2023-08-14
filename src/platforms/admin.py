from django.contrib import admin
from utilities.admin import TranslationInline

from .models import *


@admin.register(Platform)
class PlatformAdmin(admin.ModelAdmin):
    list_search = ('organisation',)
    list_display = ('name', 'organizations', 'creator',  'dateCreated', 'dateUpdated', 'approved', 'safe_url')
    exclude = ('geographicExtend', 'keywords')
    readonly_fields = ('creator', )
    ordering = ('-dateCreated',)
    autocomplete_fields = ('organisation', 'topic' )


@admin.register(GeographicExtend)
class GeographicExtendAdmin(admin.ModelAdmin):
    list_display = ('description',)
    search_fields = ('description',)
    inlines = [TranslationInline]


