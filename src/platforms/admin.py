from django.contrib import admin
from utilities.admin import TranslationInline

from .models import GeographicExtend, Platform


@admin.register(Platform)
class PlatformAdmin(admin.ModelAdmin):
    list_filter = ('active', 'organisation',)
    list_display = ('name', 'creator', 'organizations', 'dateCreated', 'dateUpdated', 'active', 'safe_url')
    exclude = ('geographicExtend',)
    ordering = ('-name',)


@admin.register(GeographicExtend)
class GeographicExtendAdmin(admin.ModelAdmin):
    list_display = ('description',)
    search_fields = ('description',)
    inlines = [TranslationInline]


