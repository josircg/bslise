from authtools import forms as authtoolsforms
from crispy_forms.bootstrap import StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, HTML, Field
from django import forms
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth import forms as authforms
from django.contrib.auth.forms import AuthenticationForm
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

User = get_user_model()


class LoginForm(AuthenticationForm):
    remember_me = forms.BooleanField(required=False, initial=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.fields["username"].widget.input_type = "email"  # ugly hack
        self.fields["username"].label = ""
        self.fields["password"].label = ""
        reset_pwd_msg = _('Forgot password?')
        reset_pwd_url = reverse("accounts:password-reset")
        self.helper.layout = Layout(
            Field("username", label="", placeholder=_("Enter Email"), autofocus=""),
            HTML('<div class="m-4"></div>'),
            Field("password", placeholder=_("Enter Password")),
            HTML(f'<div class="mt-3 mb-4"><a href="{reset_pwd_url}" class="pt-1 mb-5">{reset_pwd_msg}</a></div>'),
            StrictButton(_("Log in"), css_class="btn btn-submit-account", type="Submit")

        )

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        if username is not None and password:
            self.user_cache = authenticate(self.request, username=username, password=password)
            if self.user_cache is None:
                try:
                    user_temp = User.objects.get(email=username)
                except User.DoesNotExist:
                    user_temp = None

                if user_temp is not None:
                    if not user_temp.is_active:
                        raise forms.ValidationError(
                            _("We see that your email address is already in our database, but that you have not "
                              "yet confirmed your address. Please search for the confirmation email in your "
                              "inbox(or spam) to activate your account")
                        )
                    else:
                        raise forms.ValidationError(
                            self.error_messages['invalid_login'],
                            code='invalid_login',
                            params={'username': self.username_field.verbose_name},
                        )

                else:
                    raise forms.ValidationError(
                        self.error_messages['invalid_login'],
                        code='invalid_login',
                        params={'username': self.username_field.verbose_name},
                    )

        return self.cleaned_data


class SignupForm(authtoolsforms.UserCreationForm):
    language = forms.ChoiceField(
        label=_('Language'),
        help_text=_('Select your preferred language to browse and receive emails upon logging in.'),
        choices=settings.TRANSLATED_LANGUAGES)
    newsletter = forms.BooleanField(label=_('I want to receive the BSLISE newsletter'), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.fields["email"].widget.input_type = "email"  # ugly hack
        self.fields["email"].label = ""
        self.fields["name"].label = ""
        self.fields["password1"].label = ""
        self.fields["password2"].label = ""
        #       self.fields["captcha"] = ReCaptchaField()
        #       self.fields["captcha"].label = ""
        self.helper.layout = Layout(
            Field("email", placeholder=_("Enter Email"), autofocus=""),
            HTML('<div class="m-4"></div>'),
            Field("name", placeholder=_("Enter your first name and surname")),
            HTML('<div class="m-4"></div>'),
            Field("language", placeholder=_("Enter your prefered language")),
            HTML('<div class="m-4"></div>'),
            Field("orcid", placeholder=_("Enter your ORCID")),
            HTML('<div class="m-4"></div>'),
            Field("password1", placeholder=_("Enter Password")),
            HTML('<div class="m-4"></div>'),
            Field("password2", placeholder=_("Re-enter Password")),
            HTML('<div class="m-4"></div>'),
            Field("newsletter"),
            StrictButton(_("Sign up"), css_class="btn btn-submit-account mt-3", type="Submit"),
        )


class PasswordChangeForm(authforms.PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field("old_password", placeholder=_("Enter old password"), autofocus=""),
            Field("new_password1", placeholder=_("Enter new password")),
            Field("new_password2", placeholder=_("Enter new password (again)")),
            StrictButton(_("Change Password"), css_class="btn-submit-account mt-4", type="Submit"),
        )


class PasswordResetForm(authtoolsforms.FriendlyPasswordResetForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()

        self.helper.layout = Layout(
            Field("email", placeholder=_("Enter email"), autofocus=""),
            StrictButton(_("Reset Password"), css_class="btn-submit-account mt-4", type="Submit"),
        )


class SetPasswordForm(authforms.SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()

        self.helper.layout = Layout(
            Field("new_password1", placeholder=_("Enter new password"), autofocus=""),
            Field("new_password2", placeholder=_("Enter new password (again)")),
            Submit("pass_change", _("Change Password"), css_class="btn-submit-account mt-4"),
        )
