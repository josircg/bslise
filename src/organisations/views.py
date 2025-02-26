import copy

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import ProgrammingError
from django.db.models import ProtectedError, Q
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.template.loader import render_to_string
from django.utils import translation
from django.utils.translation import ugettext_lazy as _, get_language

from django_countries import countries as countries_list
from eucs_platform import send_email
from eucs_platform.logger import log_message
from profiles.models import Profile
from projects.models import Project
from resources.models import Resource
from utilities.file import crop_and_save

from .forms import OrganisationForm, OrganisationPermissionForm
from .models import Organisation, OrganisationType, OrganisationPermission

User = get_user_model()


@login_required(login_url='/login')
def new_organisation(request):
    form = OrganisationForm()
    error = ''
    if request.method == 'POST':
        form = OrganisationForm(request.POST, request.FILES)
        if form.is_valid():
            image_path = crop_and_save(request, form, 'logo')
            organisation = form.save(request, image_path)
            messages.success(request, _('Organisation added'))
            log_message(organisation, _('Organisation added'), request.user)
            to = copy.copy(settings.EMAIL_RECIPIENT_LIST)
            to.append(request.user.email)

            context = {
                'submissionName': form.cleaned_data['name'], 'username': request.user.name,
                'domain': settings.DOMAIN, 'id': organisation.pk,
                'site_name': settings.SITE_NAME,
            }

            language = organisation.creator.profile.language

            send_email(
                _('Your organisation "%s" has been submitted!') % form.cleaned_data['name'],
                render_to_string(f'emails/{language}/new_organisation.html', context),
                to=to,
                reply_to=settings.EMAIL_RECIPIENT_LIST,)

            send_email(
                subject=_('Notification - New organisation "%s" submitted') % form.cleaned_data['name'],
                message=render_to_string(f'emails/{language}/notify_organisation.html', context),
                to=settings.EMAIL_RECIPIENT_LIST,
                reply_to=to
            )
            return redirect('/organisation/' + str(organisation.id), {})
        else:
            if 'latitude' in form.errors:
                error = form.errors['latitude'].data[0].message
                del form.errors['latitude']

    return render(
        request,
        'organisation_form.html',
        {'form': form, 'user': request.user, 'error': error})


def organisation(request, pk):
    organisation = get_object_or_404(Organisation, id=pk)
    user = request.user
    cooperatorsPK = getCooperators(pk)
    if user != organisation.creator and not user.is_staff and not (user.id in cooperatorsPK):
        editable = False
    else:
        editable = True
    mainProjects = Project.objects.all().filter(mainOrganisation__id=pk)
    associatedProjects = Project.objects.all().filter(organisation__id=pk)
    associatedProjects |= mainProjects
    associatedProjects = associatedProjects.distinct()
    associatedResources = Resource.objects.all().filter(organisation__id=pk).filter(isTrainingResource=False)
    associatedTrainingResources = Resource.objects.all().filter(organisation__id=pk).filter(isTrainingResource=True)
    members = Profile.objects.all().filter(profileVisible=True).filter(organisation__id=pk)
    users = getOtherUsers(organisation.creator, members)
    cooperators = getCooperatorsEmail(pk)
    permissionForm = OrganisationPermissionForm(
        initial={'usersCollection': users, 'selectedUsers': cooperators})

    return render(request, 'organisation.html', {
        'organisation': organisation,
        'associatedProjects': associatedProjects,
        'cooperators': cooperatorsPK,
        'associatedResources': associatedResources,
        'associatedTrainingResources': associatedTrainingResources,
        'members': members,
        'permissionForm': permissionForm,
        'editable': editable,
        'isSearchPage': True})


@login_required(login_url='/login')
def edit_organisation(request, pk):
    organisation = get_object_or_404(Organisation, id=pk)
    user = request.user
    cooperatorsPK = getCooperators(pk)
    if user != organisation.creator and not user.is_staff and not (user.id in cooperatorsPK):
        return redirect('../organisations', {})

    form = OrganisationForm(initial={
        'name': organisation.name,
        'url': organisation.url,
        'description': organisation.description,
        'orgType': organisation.orgType,
        'country': organisation.country,
        'logo': organisation.logo,
        'withLogo': (True, False)[organisation.logo == ""],
        'contact_point': organisation.contactPoint,
        'contact_point_email': organisation.contactPointEmail,
        'latitude': organisation.latitude,
        'longitude': organisation.longitude
    })

    if request.method == 'POST':
        form = OrganisationForm(request.POST, request.FILES)
        if form.is_valid():
            image_path = crop_and_save(request, form, 'logo')
            form.save(request, image_path)
            return redirect('/organisation/' + str(organisation.id), {})
        else:
            if '__all__' in form.errors:
                form.errors['logo'] = form.errors['__all__']
                del form.errors['__all__']

    return render(request, 'organisation_form.html', {
        'form': form,
        'organisation': organisation,
        'user': user})


@login_required(login_url='/login')
def approve_organisation(request, pk, status):
    organisation = get_object_or_404(Organisation, id=pk)
    if request.user.is_staff:
        organisation.approved = status == 1
        organisation.save()
        if organisation.approved:
            message = _('Organisation approved')
        else:
            message = _('Organisation not approved')
        log_message(organisation, message, request.user)
        messages.success(request, message)
        return redirect('/admin/organisations/organisation/')
    else:
        messages.success(request, _('Only staff can approve object'))
        return redirect('../organisations', {})


def organisations(request):
    organisations = Organisation.objects.all()
    org_types = OrganisationType.objects.translated_sorted_by_text()

    if not (request.user and request.user.is_staff):
        organisations = organisations.filter(approved=True)

    existing_countries = organisations.values_list('country', flat=True).distinct()
    # Distinct list of countries
    countries = []
    for country_code in existing_countries:
        if country_code:
            countries.append({'code': country_code,
                              'name': countries_list.countries.get(country_code, country_code)})
    countries = sorted(countries, key=lambda d: d['name'])

    filters = {'keywords': '', 'orgTypes': '', 'country': ''}
    if request.GET.get('keywords'):
        organisations = organisations.filter(
                Q(name__icontains=request.GET['keywords'])).distinct()
        filters['keywords'] = request.GET['keywords']
    if request.GET.get('country'):
        organisations = organisations.filter(country=request.GET['country'])
        filters['country'] = request.GET['country']
    if request.GET.get('orgTypes'):
        organisationtype_qs = OrganisationType.objects.translated().filter(
            translated_text=request.GET['orgTypes']
        ).values_list('pk')
        organisations = organisations.filter(orgType__pk__in=organisationtype_qs)
        filters['orgTypes'] = request.GET['orgTypes']

    try:
        counter = len(organisations)
    except ProgrammingError:
        counter = 0
        organisations = Organisation.objects.none()

    # Ordering
    order_by = request.GET.get('orderby', '-dateUpdated')
    organisations = organisations.order_by(order_by)

    filters['orderby'] = order_by

    paginator = Paginator(organisations, 12)
    page = request.GET.get('page')
    organisations = paginator.get_page(page)

    return render(request, 'organisations.html', {
        'organisations': organisations,
        'counter': counter,
        'filters': filters,
        'countries': countries,
        'orgTypes': org_types,
        'isSearchPage': True})


def delete_organisation(request, pk):
    organisation = get_object_or_404(Organisation, id=pk)
    user = request.user

    if user != organisation.creator and not user.is_staff:
        return redirect('../organisations', {})

    try:
        organisation.delete()
        return redirect('../organisations', {})
    except ProtectedError:
        messages.error(request, _('The Organisation cannot be removed because there are projects associated to it'))
        return redirect('organisation', pk=pk)


def organisationsAutocompleteSearch(request):
    if request.GET.get('q'):
        text = request.GET['q']
        is_admin = request.user and request.user.is_staff
        organisations = getOrganisationAutocomplete(text, is_admin)
        organisations = list(organisations)
        return JsonResponse(organisations, safe=False)
    else:
        return HttpResponse("No cookies")


def getOrganisationAutocomplete(text, is_admin):
    organisations = Organisation.objects.filter(name__icontains=text)
    if not is_admin:
        organisations = organisations.filter(approved=True)
    organisations = organisations.values_list('id', 'name')
    report = []
    for organisation in organisations:
        report.append({"type": "organisation", "id": organisation[0], "text": organisation[1]})
    return report


def preFilteredOrganisations(request):
    organisations = Organisation.objects.get_queryset().order_by('id')
    return applyFilters(request, organisations)


def applyFilters(request, organisations):
    if request.GET.get('country'):
        organisations = organisations.filter(country=request.GET['country'])
    if request.GET.get('orgType'):
        organisations = organisations.filter(orgType=request.GET['orgType'])
    return organisations


def getOtherUsers(creator, members):
    users = []
    for member in members:
        user = get_object_or_404(User, id=member.user_id)
        users.append(user.id)
    users = list(
        User.objects.filter(id__in=users).exclude(
            is_superuser=True).exclude(id=creator.id).values_list('name', 'email'))
    return users


def getCooperators(organisationID):
    users = list(
        OrganisationPermission.objects.all().filter(organisation_id=organisationID).values_list('user', flat=True))
    return users


def getCooperatorsEmail(organisationID):
    users = getCooperators(organisationID)
    cooperators = ""
    for user in users:
        userObj = get_object_or_404(User, id=user)
        cooperators += userObj.email + ", "
    return cooperators


def allowUserOrganisation(request):
    response = {}
    organisationID = request.POST.get("organisation_id")
    users = request.POST.get("users")
    organisation = get_object_or_404(Organisation, id=organisationID)
    if request.user != organisation.creator and not request.user.is_staff:
        # TODO return JsonResponse with error code
        return redirect('../organisations', {})

    # Delete all
    objs = OrganisationPermission.objects.all().filter(organisation_id=organisationID)
    for obj in objs:
        obj.delete()

    # Insert all
    users = users.split(',')
    for user in users:
        fUser = User.objects.filter(email=user)[:1].get()
        organisationPermission = OrganisationPermission(organisation=organisation, user=fUser)
        organisationPermission.save()

    return JsonResponse(response, safe=False)
