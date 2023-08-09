from captcha.fields import CaptchaField
from django import forms
from django.utils.translation import ugettext_lazy as _

class ContactForm(forms.Form):
    from_email = forms.EmailField(
        label=_('From email'),
        required=True
    )
    name = forms.CharField(label=_('Name'), required=True)
    surname = forms.CharField(label=_('Surname'), required=False)
    message = forms.CharField(label=_('Message'), widget=forms.Textarea(attrs={'rows': 5,'cols': 40}), required=True)
    newsletter = forms.BooleanField(label=_('I want to receive the monthly newsletter'), required=False)
    message = forms.CharField(label=_('Message'), widget=forms.Textarea(attrs={'rows': 5, 'cols': 40}), required=True)
    captcha = CaptchaField()


class SubmitterContactForm(forms.Form):
    subject = forms.CharField(label=_('Subject'), required=True)
    message = forms.CharField(label=_('Message'), widget=forms.Textarea(attrs={'rows': 5,'cols': 40}), required=True)


class SubscribeForm(forms.Form):
    name = forms.CharField(label=_('Name'), required=True)
    email = forms.EmailField(label=_('Email'), required=True)
    organisation = forms.CharField(label=_('Organisation'), required=False)


class ImportForm(forms.Form):
    file = forms.FileField(label='', widget=forms.ClearableFileInput(attrs={'accept': '.csv'}), required=True)
    source = forms.CharField(label=_('Origin'), required=True, help_text=_('Describe the file origin'))
