from ckeditor.widgets import CKEditorWidget
from django import forms
from django.contrib.admin.models import ADDITION
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django_countries import countries
from django_select2 import forms as s2forms
from django_select2.forms import Select2MultipleWidget

from eucs_platform.logger import log_message

from organisations.models import Organisation
from projects.models import Topic

from .models import Platform, GeographicExtend


class PlatformForm(forms.Form):
    name = forms.CharField(
        max_length=200,
        help_text=_('Please write the name of the programme.'),
        label=_('Programme name'),
        widget=forms.TextInput())

    description = forms.CharField(
        max_length=3000,
        label=_('Description'),
        help_text=_('Please briefly describe the programme (max 3000 characters).'),
        widget=CKEditorWidget(config_name='frontpage'))

    url = forms.URLField(
        max_length=200,
        label=_('URL'),
        help_text=_('Please provide the URL of the programme.'),
        widget=forms.TextInput())

    qualification = forms.CharField(
        max_length=200,
        help_text=_('Please write the qualification required.'),
        label=_('Qualification'),
        widget=forms.TextInput())

    geoExtend = forms.ModelChoiceField(
        queryset=GeographicExtend.objects.none(),
        widget=s2forms.Select2Widget,
        help_text=_('Please indicate the spatial scale of the programme.'),
        label=_('Geographic extent'))

    countries = forms.MultipleChoiceField(
        widget=s2forms.Select2MultipleWidget,
        label=_("Countries"),
        help_text=_('Please select the country(ies) related to the programme.')
    )
    # platformLocality = forms.CharField(
    #         label=_("Network / platform locality"),
    #         max_length=300,
    #         widget=forms.TextInput(),
    #         required=False,
    #         help_text=_('Please describe the locality of the network or platform. For example: City of Lisbon.'))

    contactPoint = forms.CharField(
        label=_('Contact point'),
        max_length=100,
        help_text=_('Please name the contact person or contact point.'),
        widget=forms.TextInput(),
        required=False)

    contactPointEmail = forms.EmailField(
        label=_('Contact point email'),
        max_length=100,
        help_text=_(
            'Please provide the email address of the contact person or '
            'contact point. Note you will need permission to do that.'),
        widget=forms.TextInput(),
        required=False)

    contactPhone = forms.CharField(
        label=_('Contact Phone'),
        max_length=100,
        help_text=_('Insert a contact phone'),
        widget=forms.TextInput(),
        required=False)

    organisation = forms.ModelMultipleChoiceField(
        label=_("Organisation(s)"),
        help_text=_(
            "Please select the organisation(s) coordinating the platform. "
            "If not listed, please add <a href='/new_organisation' "
            "target='_blank'>here</a> before submitting the network or platform."),
        queryset=Organisation.objects.all(),
        widget=s2forms.ModelSelect2MultipleWidget(
            model=Organisation,
            search_fields=['name__icontains']),
        required=False)

    topic = forms.ModelMultipleChoiceField(
        queryset=Topic.objects.none(),
        widget=Select2MultipleWidget(),
        help_text=_('Please select the programme types.'),
        required=False,
        label=_("Topic"))

    logo = forms.ImageField(
        required=False,
        label=_("Logo of your network or platform"),
        help_text=_('This image will be resized to 600x400 pixels.'),
        widget=forms.FileInput)
    xlogo = forms.FloatField(widget=forms.HiddenInput(), required=False)
    ylogo = forms.FloatField(widget=forms.HiddenInput(), required=False)
    widthlogo = forms.FloatField(widget=forms.HiddenInput(), required=False)
    heightlogo = forms.FloatField(widget=forms.HiddenInput(), required=False)
    logoCredit = forms.CharField(
        max_length=300,
        required=False,
        label=_("Logo credit, if applicable"))

    profileImage = forms.ImageField(
        required=False,
        label=_("Network or platform profile image"),
        help_text=_('This image will be resized to 1100x400 pixels.'),
        widget=forms.FileInput)
    xprofileImage = forms.FloatField(widget=forms.HiddenInput(), required=False)
    yprofileImage = forms.FloatField(widget=forms.HiddenInput(), required=False)
    widthprofileImage = forms.FloatField(widget=forms.HiddenInput(), required=False)
    heightprofileImage = forms.FloatField(widget=forms.HiddenInput(), required=False)
    profileImageCredit = forms.CharField(
        max_length=300,
        required=False,
        label=_("Profile image credit, if applicable."))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set queryset here to reflect language change results
        self.fields['topic'].queryset = Topic.objects.translated().order_by('translated_text')

    def save(self, args, images):
        """Save function"""
        pk = self.data.get('Id', '')
        if pk:
            platform = get_object_or_404(Platform, id=pk)
            self.updatePlatform(platform, args)
        else:
            platform = self.createPlatfom(args)
            log_message(platform, [{'added': {}}], platform.creator, ADDITION)

        platform.save()
        platform.organisation.set(self.data.getlist('organisation'))
        platform.countries = self.data.getlist('countries')
        # I don't like it
        for key in images:
            if key == 'logo':
                platform.logo = images[key]
            if key == 'profileImage':
                platform.profileImage = images[key]
        platform.save()
        return platform.id

    def createPlatfom(self, args):
        """Create function"""
        return Platform(
            creator=args.user,
            name=self.data['name'],
            url=self.cleaned_data['url'],
            description=self.data['description'],
            qualification=self.data['qualification'],
            contactPoint=self.data['contactPoint'],
            contactPointEmail=self.data['contactPointEmail'],
            contactPhone=self.data['contactPhone'],
            geoExtend=self.cleaned_data['geoExtend'],
            logoCredit=self.data['logoCredit'],
            profileImageCredit=self.data['profileImageCredit'])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Countries and geoExtend must be set here to handle language change
        self.fields['countries'].choices = countries
        self.fields['topic'].queryset = Topic.objects.translated().order_by('translated_text')
        self.fields['geoExtend'].queryset = GeographicExtend.objects.translated().order_by('translated_text')

    def updatePlatform(self, platform, args):
        """Update function"""
        platform.name = self.data['name']
        platform.url = self.cleaned_data['url']
        platform.description = self.data['description']
        platform.qualification = self.data['qualification']
        platform.contactPoint = self.data['contactPoint']
        platform.contactPointEmail = self.data['contactPointEmail']
        platform.contactPhone = self.data['contactPhone']
        platform.geoExtend = self.cleaned_data['geoExtend']
        platform.logoCredit = self.data['logoCredit']
        platform.profileImageCredit = self.data['profileImageCredit']
