import six
from braces import views as bracesviews
from django.contrib.admin.models import ADDITION

from contact.models import Subscriber
from django.conf import settings
from django.contrib import auth
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth import views as authviews
from django.contrib.auth.views import INTERNAL_RESET_SESSION_TOKEN
from django.shortcuts import redirect, get_object_or_404, resolve_url
from django.shortcuts import render
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils import translation
from django.utils.encoding import force_bytes, force_text
from django.utils.functional import lazy
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.translation import ugettext_lazy as _, get_language
from django.views import generic
from eucs_platform import send_email, set_language_preference
from eucs_platform.logger import log_message
from profiles.models import Profile

from . import forms
from .models import ActivationTask
from .tokens import account_activation_token

User = get_user_model()


def _safe_resolve_url(url):
    """
    Previously, resolve_url_lazy would fail if the url was a unicode object.
    See <https://github.com/fusionbox/django-authtools/issues/13> for more
    information.

    Thanks to GitHub user alanwj for pointing out the problem and providing
    this solution.
    """
    return six.text_type(resolve_url(url))


resolve_url_lazy = lazy(_safe_resolve_url, six.text_type)


def send_activation_email(user):
    if user.profile:
        language = user.profile.language
    else:
        language = get_language()

    if not language:
        language = 'en'

    template = f'accounts/emails/{language}/acc_active_email.html'
    html_message = render_to_string(template, {
        'user': user,
        'domain': settings.DOMAIN,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': account_activation_token.make_token(user),
    })
    send_email(subject=_('Activate your account!'), to=[user.email], reply_to=settings.EMAIL_RECIPIENT_LIST, message=html_message)


class LoginView(bracesviews.AnonymousRequiredMixin, authviews.LoginView):
    template_name = "accounts/login.html"
    form_class = forms.LoginForm

    def form_valid(self, form):
        user = form.get_user()
        translation.activate(user.profile.language)
        redirect = super().form_valid(form)
        remember_me = form.cleaned_data.get("remember_me")
        if remember_me is True:
            ONE_MONTH = 30 * 24 * 60 * 60
            expiry = getattr(settings, "KEEP_LOGGED_DURATION", ONE_MONTH)
            self.request.session.set_expiry(expiry)

        return set_language_preference(self.request, redirect, user.profile.language)


class LogoutView(authviews.LogoutView):
    next_page = reverse_lazy("home")


class SignUpView(
    bracesviews.AnonymousRequiredMixin,
    bracesviews.FormValidMessageMixin,
    generic.CreateView,
):
    form_class = forms.SignupForm
    model = User
    template_name = "accounts/signup.html"
    success_url = reverse_lazy("home")
    form_valid_message = _("Account created successfully")

    def form_valid(self, form):
        super().form_valid(form)
        user = form.save(commit=False)
        user.is_active = False
        user.save()
        log_message(user, 'Created via sign in form', action_flag=ADDITION)

        orcid = form.cleaned_data.get('orcid')
        newsletter = form.cleaned_data.get('newsletter')
        profile = get_object_or_404(Profile, user_id=user.id)
        profile.orcid = orcid
        profile.language = form.cleaned_data.get('language')
        profile.save()

        if newsletter:
            subscriber = Subscriber.objects.subscribe(form.cleaned_data['name'], form.cleaned_data['email'], valid=False)
            log_message(subscriber, 'Opt-in via sign in form')

        with translation.override(profile.language):
            send_activation_email(user)

        with translation.override(settings.LANGUAGE_CODE):
            notify_message = render_to_string(
                f'accounts/emails/{settings.LANGUAGE_CODE}/notify_new_user.html',
                {'user': user, 'site': settings.SITE_NAME}
            )

            send_email(subject=_('New user registration'), to=settings.EMAIL_RECIPIENT_LIST, message=notify_message)

        return render(self.request, f'accounts/confirm-email.html', {})


def send_activate_email_view(request, user_id):
    user = User.objects.get(pk=user_id)
    send_activation_email(user)
    messages.success(request, _("Email sent"))
    return redirect('/admin/authtools/user/')


class PasswordChangeView(authviews.PasswordChangeView):
    form_class = forms.PasswordChangeForm
    template_name = "accounts/password-change.html"
    success_url = reverse_lazy("accounts:logout")

    def form_valid(self, form):
        form.save()
        messages.success(
            self.request,
            _('Your password has been changed, therefore you have been logged out. Please log in again.')
        )

        return super().form_valid(form)


class PasswordResetView(authviews.PasswordResetView):
    form_class = forms.PasswordResetForm
    template_name = "accounts/password-reset.html"
    success_url = reverse_lazy("accounts:password-reset-done")
    subject_template_name = "accounts/emails/password-reset-subject.txt"
    tag = getattr(settings, 'EMAIL_TAG', 'XXX')
    extra_email_context = {'PASSWORD_RESET_TIMEOUT_HOURS': settings.PASSWORD_RESET_TIMEOUT_DAYS * 24,
                           'domain': settings.DOMAIN,
                           'tag': tag}

    def form_valid(self, form):
        self.email_template_name = f'accounts/emails/{get_language()}/password-reset-email.html'
        return super().form_valid(form)


class PasswordResetDoneView(authviews.PasswordResetDoneView):
    template_name = "accounts/password-reset-done.html"


# TODO: Rever se realmente é utilizado. Se for, retirar o comentário abaixo
class PasswordResetConfirmAndLoginView(authviews.PasswordResetConfirmView):
    """View removed from django-authtools"""
    success_url = resolve_url_lazy(settings.LOGIN_REDIRECT_URL)

    def form_valid(self, form):
        self.user = form.save()
        del self.request.session[INTERNAL_RESET_SESSION_TOKEN]
        if self.user.is_active:
            auth.login(self.request, self.user, self.post_reset_login_backend)
        else:
            send_activation_email(self.user, f'accounts/emails/{get_language()}/acc-reactive.html')

            messages.success(
                self.request,
                _('Your password has been successfully reset! Please check your email to activate your account.')
            )

        return redirect(self.get_success_url())

    def get_success_url(self):
        if self.user.is_active:
            return resolve_url_lazy(settings.LOGIN_REDIRECT_URL)
        else:
            return resolve_url_lazy(settings.LOGIN_URL)


class PasswordResetConfirmView(PasswordResetConfirmAndLoginView):
    template_name = "accounts/password-reset-confirm.html"
    form_class = forms.SetPasswordForm


def activate(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        language = user.profile.language
        subscriber = Subscriber.objects.filter(email=user.email)
        if subscriber:
            subscriber[0].valid = True
            subscriber[0].save()
            log_message(subscriber[0], 'Validated via activation email')

        with translation.override(language):
            # Do not send welcome email when reacvitating a blocked account
            if 'reactivate' not in request.GET:
                send_email(
                    subject=_('Welcome!'),
                    message=render_to_string(
                        f'accounts/emails/{language}/welcome_email.html',
                        {'user': user, "domain": settings.DOMAIN, 'reply_to': settings.EMAIL_RECIPIENT_LIST}
                    ),
                    to=[user.email])
            auth.login(request, user)

            response = None

            try:
                # Execute a task after user activation
                task = ActivationTask.objects.get(email=user.email)
                # Task must be a function with request param
                response = task.execute_task(request=request)

                task.delete()
            except ActivationTask.DoesNotExist:
                pass

            if response is None:
                response = render(request, 'accounts/confirmation-account.html', {})

            response = set_language_preference(request, response, language)

            return response
    else:
        return render(request, 'accounts/confirm-error.html', {})
