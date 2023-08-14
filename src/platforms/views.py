import copy
import os
import random
from datetime import datetime

from PIL import Image
from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils import formats
from django.utils.translation import ugettext_lazy as _
from eucs_platform import send_email
from rest_framework import status

from .forms import PlatformForm
from .models import Platform, Keyword, GeographicExtend


@staff_member_required(login_url='/login')
def newPlatform(request):
    user = request.user
    platformForm = PlatformForm()
    return render(request, 'platform_form.html', {'form': platformForm, 'user': user})


@staff_member_required(login_url='/login')
def editPlatform(request, pk):
    user = request.user
    platform = get_object_or_404(Platform, id=pk)

    if user != platform.creator and not user.is_staff:
        return redirect('../platforms', {})

    platformForm = PlatformForm(initial={
        'name': platform.name,
        'url': platform.url,
        'description': platform.description,
        'geoExtend': platform.geoExtend,
        'countries': platform.countries,
        'contactPoint': platform.contactPoint,
        'contactPointEmail': platform.contactPointEmail,
        'contactPhone': platform.contactPhone,
        'organisation': platform.organisation.all,
        'topic': platform.topic.all,
        'logo': platform.logo,
        'logoCredit': platform.logoCredit,
        'profileImage': platform.profileImage,
        'profileImageCredit': platform.profileImageCredit
    })
    return render(request, 'platform_form.html', {'form': platformForm, 'user': user, 'id': platform.id})




@staff_member_required(login_url='/login')
def deletePlatformAjax(request, pk):
    platform = get_object_or_404(Platform, id=pk)
    if request.user == platform.creator or request.user.is_staff:
        platform.delete()
        return JsonResponse({'Platform deleted': 'OK', 'Id': pk}, status=status.HTTP_200_OK)
    else:
        return JsonResponse({}, status=status.HTTP_403.FORBIDDEN)


@staff_member_required(login_url='/login')
def savePlatformAjax(request):
    form = PlatformForm(request.POST, request.FILES)
    if form.is_valid():
        images = setImages(request, form)
        pk = form.save(request, images)
        if request.POST.get('Id').isnumeric():
            return JsonResponse({'Platform updated': 'OK', 'Id': pk}, status=status.HTTP_200_OK)
        else:
            sendPlatformEmail(pk, request, form)
            return JsonResponse({'Platform created': 'OK', 'Id': pk}, status=status.HTTP_200_OK)
    else:
        return JsonResponse(form.errors, status=status.HTTP_406_NOT_ACCEPTABLE)


def sendPlatformEmail(id, request, form):
    to = copy.copy(settings.EMAIL_RECIPIENT_LIST)
    to.append(request.user.email)
    messages.success(request, _('Programme added correctly'))
    send_email(
        subject='Seu programa/curso "%s" foi submetido!' % form.cleaned_data['name'],
        message=render_to_string('emails/new_platform.html',
                                 {"domain": settings.DOMAIN, 'submissionName': form.cleaned_data['name'],
                                  'username': request.user.name}),
        reply_to=settings.EMAIL_CIVIS, to=to
    )

    # NOTIFICAÇÃO
    send_email(
        subject='Notification - A new programme "%s" was submitted' % form.cleaned_data['name'],
        message=render_to_string('emails/notify_platform.html', {"platformid": id, "domain": settings.DOMAIN,
                                                                 'submissionName': form.cleaned_data['name'],
                                                                 'username': request.user.name}),
        reply_to=to, to=settings.EMAIL_CIVIS
    )


def platform(request, pk):
    platform = get_object_or_404(Platform.objects.select_related('geoExtend'), id=pk)
    return render(request, 'platform.html', {'platform': platform})


def platforms(request):
    platforms = Platform.objects.select_related('geoExtend').filter(active=True)
    countries = Platform.objects.all().values_list('countries', flat=True).distinct()
    geographicExtend = GeographicExtend.objects.translated().order_by('translated_text')

    # I think this is not needded
    filters = {'keywords': '', 'geographicExtend': '', 'country': ''}

    platforms = applyFilters(request, platforms)
    platforms = platforms.distinct()
    filters = setFilters(request, filters)
    # Distinct list of countries
    countriesWithContent = [country for gcountry in countries for country in gcountry.split(',')]
    countriesWithContent = list(set(countriesWithContent))

    # Ordering
    if request.GET.get('orderby'):
        orderBy = request.GET.get('orderby')
        if "name" in orderBy:
            platforms = platforms.order_by('name')
    else:
        platforms = platforms.order_by('-dateUpdated')

    counter = len(platforms)

    paginator = Paginator(platforms, 16)
    page = request.GET.get('page')
    platforms = paginator.get_page(page)

    return render(request, 'platforms.html', {
        'platforms': platforms,
        'filters': filters,
        'countriesWithContent': countriesWithContent,
        'counter': counter,
        'geographicExtend': geographicExtend,
        'isSearchPage': True})


def applyFilters(request, platforms):
    # approvedProjects = ApprovedProjects.objects.all().values_list('project_id', flat=True)
    if request.GET.get('keywords'):
        platforms = platforms.filter(
            Q(name__icontains=request.GET['keywords']) |
            Q(keywords__keyword__icontains=request.GET['keywords'])).distinct()

    if request.GET.get('country'):
        platforms = platforms.filter(countries__contains=request.GET['country'])

    if request.GET.get('geographicExtend'):
        platforms = platforms.filter(geoExtend__pk=request.GET['geographicExtend'])

    return platforms


def setFilters(request, filters):
    if request.GET.get('keywords'):
        filters['keywords'] = request.GET['keywords']
    if request.GET.get('orderby'):
        filters['orderby'] = request.GET['orderby']
    if request.GET.get('country'):
        filters['country'] = request.GET['country']
    if request.GET.get('geographicExtend'):
        filters['geographicExtend'] = request.GET['geographicExtend']
    return filters


def platformsAutocompleteSearch(request):
    if request.GET.get('q'):
        text = request.GET['q']
        platforms = getPlatformsAutocomplete(text)
        platforms = list(platforms)
        return JsonResponse(platforms, safe=False)
    else:
        return HttpResponse("No cookies")


def getPlatformsAutocomplete(text):
    platforms = Platform.objects.filter(name__icontains=text).values_list('id', 'name').distinct()
    keywords = Keyword.objects.filter(keyword__icontains=text).values_list('keyword', flat=True).distinct()
    report = []
    for platform in platforms:
        report.append({"type": "platform", "id": platform[0], "text": platform[1]})
    for keyword in keywords:
        numberElements = Platform.objects.filter(Q(keywords__keyword__icontains=keyword)).count()
        report.append({"type": "platformKeyword", "text": keyword, "numberElements": numberElements})
    return report


def setImages(request, form):
    images = {}
    for key, value in request.FILES.items():
        if '.svg' in value.lower():
            x = 0
        else:
            x = form.cleaned_data.get('x' + key)
            y = form.cleaned_data.get('y' + key)
            w = form.cleaned_data.get('width' + key)
            h = form.cleaned_data.get('height' + key)
            image = Image.open(value)
            if x and y and w and h:
                image = image.crop((x, y, w + x, h + y))
                if key == 'profileImage':
                    finalsize = (1100, 400)
                else:
                    finalsize = (600, 400)
                image = image.resize(finalsize, Image.ANTIALIAS)
            imagePath = getImagePath(value.name)
            image.save(os.path.join(settings.MEDIA_ROOT, imagePath))
            images[key] = imagePath
    return images


def getImagePath(imageName):
    _datetime = formats.date_format(datetime.now(), 'Y-m-d_hhmmss')
    random_num = random.randint(0, 1000)
    return "images/" + _datetime + '_' + str(random_num) + '_' + imageName
