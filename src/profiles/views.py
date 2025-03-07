from itertools import chain

from contact.models import Subscriber
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db import ProgrammingError
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import translation
from django.utils.translation import ugettext_lazy as _
from django.views import generic
from eucs_platform import set_language_preference
from events.models import Event
from organisations.models import Organisation, OrganisationPermission
from projects.models import Project, FollowedProjects, ProjectPermission
from resources.models import Resource, BookmarkedResources, ResourcePermission


from . import forms
from .models import Profile, InterestArea


class ShowProfile(LoginRequiredMixin, generic.TemplateView):
    template_name = "profiles/show_profile.html"
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        slug = self.kwargs.get("slug")
        if slug:
            profile = get_object_or_404(Profile, slug=slug)
            user = profile.user
            if user.profile.profileVisible is True:
                kwargs["show_user"] = user

        else:
            user = self.request.user
            kwargs["show_user"] = user

        if user == self.request.user:
            kwargs["editable"] = True

        return super().get(request, *args, **kwargs)


class EditProfile(LoginRequiredMixin, generic.TemplateView):
    template_name = "profiles/edit_profile.html"
    http_method_names = ["get", "post"]

    def get(self, request, *args, **kwargs):
        user = self.request.user
        if user.is_anonymous:
            return redirect("/login")

        if "user_form" not in kwargs:
            kwargs["user_form"] = forms.UserForm(instance=user)
        if "profile_form" not in kwargs:
            kwargs["profile_form"] = forms.ProfileForm(
                instance=user.profile,
                initial={
                    'interestAreas': user.profile.interestAreas.all(),
                    'country': user.profile.country})
        kwargs["show_user"] = user
        if user == self.request.user:
            kwargs["editable"] = True

        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        request.POST = request.POST.copy()
        request.POST = updateInterestAreas(request.POST)

        user = self.request.user
        user_form = forms.UserForm(request.POST, instance=user)
        profile_form = forms.ProfileForm(
            request.POST, request.FILES, instance=user.profile
        )
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save(request)
            user.refresh_from_db()
            translation.activate(user.profile.language)
            messages.success(request, _("Profile details saved!"))
            response = redirect("profiles:show_self")

            return set_language_preference(self.request, response, user.profile.language)
        else:
            messages.error(request, _("Please correct the error below."))
            return self.get(request, user_form=user_form, profile_form=profile_form)


class PrivacyCenter(LoginRequiredMixin, generic.TemplateView):
    template_name = "profiles/privacy_center.html"
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):

        user = self.request.user
        if "user_form" not in kwargs:
            kwargs["user_form"] = forms.UserForm(instance=user)
        if "profile_form" not in kwargs:
            kwargs["profile_form"] = forms.ProfileForm(
                instance=user.profile,
                initial={
                    'interestAreas': user.profile.interestAreas.all(),
                    'country': user.profile.country})
        if user == self.request.user:
            kwargs["editable"] = True

        kwargs["show_user"] = user
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['newsletter'] = Subscriber.objects.filter(email=self.request.user.email, opt_out=False).exists()
        return context


class Submissions(generic.TemplateView):
    template_name = "profiles/submissions.html"
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        slug = self.kwargs.get("slug")
        if slug:
            profile = get_object_or_404(Profile, slug=slug)
            user = profile.user
        else:
            user = self.request.user
            if user.is_anonymous:
                return redirect("/login")

        projectsSubmitted = Project.objects.filter(creator=user).order_by('-dateUpdated')
        resourcesSubmitted = Resource.objects.filter(creator=user).filter(isTrainingResource=False)
        trainingsSubmitted = Resource.objects.filter(creator=user).filter(isTrainingResource=True)
        organisationsSubmitted = Organisation.objects.all().filter(creator=user)
        eventsSubmitted = Event.objects.all().filter(creator=user)

        kwargs["show_user"] = user
        kwargs["projects_submitted"] = projectsSubmitted
        kwargs["resources_submitted"] = resourcesSubmitted
        kwargs["trainings_submitted"] = trainingsSubmitted
        kwargs["organisations_submitted"] = organisationsSubmitted
        kwargs["event_submitted"] = eventsSubmitted
        if user == self.request.user:
            kwargs["editable"] = True
        return super().get(request, *args, **kwargs)


class Bookmarks(LoginRequiredMixin, generic.TemplateView):
    template_name = "profiles/bookmarks.html"
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        user = self.request.user
        if user.is_anonymous:
            return redirect("/login")

        kwargs["show_user"] = user
        # User Bookmarks
        projects = FollowedProjects.objects.filter(user_id=user.pk).select_related('project')
        bookmarks = BookmarkedResources.objects.filter(user_id=user.pk).select_related('resource')
        resources = bookmarks.filter(resource__isTrainingResource=False)
        training = bookmarks.filter(resource__isTrainingResource=True)

        if user == self.request.user:
            kwargs["editable"] = True
        kwargs["projects_followed"] = projects
        kwargs["resources_followed"] = resources
        kwargs["trainings_followed"] = training
        # This view shows only current user bookmarks, so it's safe to send followed True to change follow icon color
        kwargs["followed"] = True

        return super().get(request, *args, **kwargs)


class UsersSearch(generic.TemplateView):
    template_name = "profiles/usersSearch.html"
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):

        orderBy = request.GET.get('orderby')
        filters = {}

        if request.GET.get('orderby'):
            if "name" in orderBy:
                users = Profile.objects.all().filter(profileVisible=True).filter(user__is_active=True).order_by(
                    'user__name')
                filters['orderby'] = 'name'
        else:
            users = Profile.objects.all().filter(profileVisible=True).filter(user__is_active=True).order_by(
                '-user__date_joined')
            filters['orderby'] = ''

            # TODO: Add surname (needs to be added algo in the autocomplete search
        if request.GET.get('keywords'):
            users = users.filter(
                Q(user__name__icontains=request.GET['keywords']) |
                Q(interestAreas__interestArea__icontains=request.GET['keywords'])).distinct()
            filters['keywords'] = request.GET['keywords']

        try:
            counter = len(users)
        except ProgrammingError:
            counter = 0
            users = Profile.objects.none()

        paginator = Paginator(users, 42)
        page = request.GET.get('page')
        users = paginator.get_page(page)

        kwargs["users"] = users
        kwargs["isSearchPage"] = True
        kwargs["counter"] = counter
        kwargs["filters"] = filters
        return super().get(request, *args, **kwargs)


class ProjectPermissions(ShowProfile):
    template_name = 'profiles/project_permissions.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = kwargs.get('show_user')
        context['project_permissions'] = ProjectPermission.objects.project_permissions_by_user(user)
        return context


def resources(request):
    user = request.user
    resourcesCreated = Resource.objects.all().filter(creator=user)
    resourcesWithPermission = getResourcesWithPermission(user)
    resourcesWithPermission = Resource.objects.all().filter(id__in=resourcesWithPermission)
    resources = chain(resourcesCreated, resourcesWithPermission)
    approvedResources = Resource.objects.filter(approved=True).values_list('resource_id', flat=True)
    unApprovedResources = Resource.objects.exclude(approved=True).values_list('resource_id', flat=True)
    return render(request, 'profiles/my_resources.html', {
        'show_user': user,
        'resources': resources,
        'approvedResources': approvedResources,
        'unApprovedResources': unApprovedResources})


def followedProjects(request):
    user = request.user
    followedProjects = FollowedProjects.objects.all().filter(user_id=user.id).values_list('project_id', flat=True)
    projects = Project.objects.filter(id__in=followedProjects)
    projects = projects.filter(~Q(hidden=True))
    return render(request, 'profiles/followed_projects.html', {
        'show_user': user,
        'projects': projects,
        'followedProjects': followedProjects})


def getProjectsWithPermission(user):
    projects = list(ProjectPermission.objects.all().filter(user_id=user).values_list('project', flat=True))
    return projects


def getResourcesWithPermission(user):
    resources = list(ResourcePermission.objects.all().filter(user_id=user).values_list('resource', flat=True))
    return resources


def organisations(request):
    user = request.user
    organisationsCreated = Organisation.objects.all().filter(creator=user)
    organisationsWithPermission = getOrganisationsWithPermission(user)
    organisationsWithPermission = Organisation.objects.all().filter(id__in=organisationsWithPermission)
    organisations = chain(organisationsCreated, organisationsWithPermission)
    return render(request, 'profiles/my_organisations.html', {'show_user': user, 'organisations': organisations})


def getOrganisationsWithPermission(user):
    organisations = list(
        OrganisationPermission.objects.all().filter(user_id=user).values_list('organisation', flat=True))
    return organisations


def updatePrivacy(request):
    user = request.user
    if 'subscribedtoDigest' in request.POST:
        user.profile.digest = (request.POST['subscribedtoDigest']).capitalize()
    if 'profileVisible' in request.POST:
        user.profile.profileVisible = (request.POST['profileVisible']).capitalize()
    if 'contentVisible' in request.POST:
        user.profile.contentVisible = (request.POST['contentVisible']).capitalize()

    user.profile.save()

    if 'newsletter' in request.POST:
        checked = (request.POST['newsletter']).capitalize() == 'True'
        Subscriber.objects.subscribe(user.name, user.email, opt_out=not checked, valid=True)

    return JsonResponse("0", safe=False)


def updateInterestAreas(dictio):
    interestAreas = dictio.pop('interestAreas', None)
    if interestAreas:
        for ia in interestAreas:
            if not ia.isdecimal():
                # This is a new interestArea
                InterestArea.objects.get_or_create(interestArea=ia)
                interestArea_id = InterestArea.objects.get(interestArea=ia).id
                dictio.update({'interestAreas': interestArea_id})
            else:
                # This keyword is already in the database
                dictio.update({'interestAreas': ia})
    return dictio


def usersAutocompleteSearch(request):
    if request.GET.get('q'):
        text = request.GET['q']
        users = getProfilesAutocomplete(text)
        users = list(users)
        return JsonResponse(users, safe=False)
    else:
        return HttpResponse("No cookies")


def getProfilesAutocomplete(text):
    profiles = Profile.objects.all().filter(
        Q(user__name__icontains=text)).filter(profileVisible=True).values_list('user__id', 'user__name', 'slug')
    interestAreas = InterestArea.objects.filter(
        interestArea__icontains=text).values_list('interestArea', flat=True).distinct()
    report = []
    for profile in profiles:
        report.append({"type": "profile", "id": profile[0], "text": profile[1], "slug": profile[2]})
    for interestArea in interestAreas:
        numberElements = Profile.objects.filter(
            profileVisible=True).filter(Q(interestAreas__interestArea__icontains=interestArea)).count()
        report.append({"type": "profileInterestArea", "text": interestArea, "numberElements": numberElements})
    return report
