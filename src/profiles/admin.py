from __future__ import unicode_literals
from django.contrib import admin
from authtools.admin import NamedUserAdmin
from .models import Profile, InterestArea
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.html import format_html

User = get_user_model()


class UserProfileInline(admin.StackedInline):
    model = Profile


class NewUserAdmin(NamedUserAdmin):
    inlines = [UserProfileInline]
    list_display = (
        "is_active",
        "email",
        "name",
        "view_profile",
        "activate",
        "is_superuser",
        "is_staff",
    )

    # 'View on site' didn't work since the original User model needs to
    # have get_absolute_url defined. So showing on the list display
    # was a workaround.
    def view_profile(self, obj):
        url = reverse("profiles:show", kwargs={"slug": obj.profile.slug})
        # Unicode hex b6 is the Pilcrow sign
        return format_html('<a href="{}">{}</a>'.format(url, "\xb6"))

    def activate(self, obj):
        url = reverse("accounts:send_activate_email", kwargs={"user_id": obj.id})
        # Unicode hex b6 is the Pilcrow sign
        return format_html('<a href="{}">{}</a>'.format(url, "\xb6"))
    activate.short_description = "Send activation email"


admin.site.unregister(User)
admin.site.register(User, NewUserAdmin)
admin.site.register(InterestArea)
