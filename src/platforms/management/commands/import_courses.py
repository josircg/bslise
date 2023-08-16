import csv
import re
import requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.admin.models import ADDITION
from django.core.management.base import BaseCommand
from django.db import transaction
from django_countries import countries as countries_list
from eucs_platform.logger import log_message
from platforms.models import *
from organisations.models import *
from utilities.file import save_image_with_path, assign_image


def remove_parenthesis(x):
    return re.sub("\(.*?\)|\[.*?\]","",x)


# remove all script and style elements from HTML
# input: html string
# output: soup object
def extract_scripts_and_styles(html):
    soup = BeautifulSoup(html, features="html.parser")
    for script in soup(["script", "style", "noscript"]):
        script.extract()
    return soup


# obtem o HTML retirado da URL e retorna um soup object
# se use_cache=False, a rotina irá buscar da URL original mesmo que já exista um cache
def load_html(url):
    try:
        headers = {'user-agent':
                       'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:23.0) Gecko/20100101 Firefox/23.0'}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = extract_scripts_and_styles(response.content)
            return soup
        else:
            return
    except Exception as e:
        return


# Busca a imagem mais relevante no objeto Soup
# Busca pelo og:image, twitter:image ou imagem dentro das tags de notícia
def scrap_best_image(soup):
    imagem = None
    tag = soup.find("meta", property="og:image")
    if tag:
        imagem = tag['content']
    else:
        tag = soup.find("meta", property="”twitter:image”")
        if tag:
            imagem = tag['content']

    if not imagem:
        for line in soup.find_all("div", {"class": ["entry-body",
                                                    "content-text", "content-noticia", "post-item-wrap"]}):
            link = line.find('img')
            if link:
                imagem = link['src']
                break

    if not imagem:
        for link in soup.find_all('img'):
            imagem = link['src']
            break

    return imagem


# Rotina salva a imagem indicada na URL no path indicado.
# A tipo da imagem é "calculado" e incluído ao path
def save_image(url, id, full_path):
    server_filename = url.split('/')[-1]
    file_ext = server_filename.split('.')[-1].split('?')[0]
    if len(file_ext) > 4 or len(file_ext) == 0 or file_ext == 'img':
        file_ext = 'jpeg'
    full_path += '%s.%s' % (id, file_ext)
    try:
        headers = {'user-agent':
                   'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:23.0) Gecko/20100101 Firefox/23.0'}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            with open(full_path, 'wb') as file:
                file.write(response.content)
            relative_path = 'images/' + full_path.split('/')[-1]
        else:
            relative_path = None
    except Exception as e:
        relative_path = None
    return relative_path


def load_and_get_image(url, id):
    soup = load_html(url)
    if not soup:
        return False, None
    imagem_url = scrap_best_image(soup)
    if imagem_url:
        if imagem_url[0] == '/':
            parse_url = urlparse(url)
            root_url = url.replace(parse_url.path, '')
            imagem_url = root_url + imagem_url
        imagem_path = save_image(imagem_url, id, settings.MEDIA_ROOT+'/images/')
        return True, imagem_path
    else:
        return True, None


class Command(BaseCommand):
    label = 'Import Courses based on pre-defined spreadsheet'

    def add_arguments(self, parser):
        parser.add_argument('--filename', type=str, help='Filename to import')

    def handle(self, *args, **options):
        filename = options['filename']
        if not filename:
            print('Filename is required')

        tot_records = 0
        tot_saved = 0
        tot_new_org = 0
        tot_images_saved = 0

        User = get_user_model()
        sys_user = User.objects.get_or_create(name='sys')[0]
        org_type_unknown = OrganisationType.objects.get_or_create(type='Private Organisation')[0]
        org_type_public = OrganisationType.objects.get_or_create(type='Public University')[0]
        default_extend = GeographicExtend.objects.filter(description='Regional')[0]

        transaction.set_autocommit(False)
        file = open(filename, 'r')
        for record in csv.DictReader(file, delimiter=';'):
            tot_records += 1
            org_name = record['Institution'].strip()[:200]
            course_name = record['Academic unit'].strip()[:200]
            country_code = record['Code']
            country = countries_list.countries.get(country_code, None)
            if not country:
                print('Country %s not found (%s)' % (country_code, record['Country']))
                country_code = None

            root_url = record['Web address'].lower()
            if root_url:
                if not root_url.startswith('http'):
                    root_url = 'http://'+root_url
                parse_url = urlparse(root_url)
                parent_url = parse_url.scheme+'://'+parse_url.netloc
            else:
                parent_url = ''

            org = Organisation.objects.filter(name=org_name)
            if org.count() == 0:
                org = Organisation()
                org.name = org_name[:200]
                if record['Address'] and record['Address'] != record['Country']:
                    org.description = record['Address']
                else:
                    org.description = record['Contact information'].split(';')[0]
                    org.description = org.description.replace(course_name,'').strip()[:200]
                    if org.description[:2] == ', ':
                        org.description = org.description[2:]
                org.country = country_code
                org.url = parent_url
                org.creator = sys_user
                if 'FEDERAL' in org_name.upper():
                    org.org_type = org_type_public
                else:
                    org.orgType = org_type_unknown
                org.latitude = round(float(record['Latitude'].replace(',','.')),5)
                org.longitude = round(float(record['Longitude'].replace(',','.')),5)
                org.approved = True
                try:
                    org.save()
                except:
                    print(org_name)
                    raise
                log_message(org, 'Imported', sys_user, ADDITION)
                tot_new_org += 1
            else:
                org = org[0]

            if org.url != parent_url:
                org.url = parent_url
                org.save()

            if not org.logo and org.approved:
                valid, candidate_image = load_and_get_image(org.url, f'org_{org.id}')
                if not valid:
                    org.approved = False
                    org.save()
                else:
                    if candidate_image:
                        assign_image(candidate_image, org.logo, 600, 400)
                        org.save()

            course = Platform.objects.filter(name=course_name, organisation=org)
            if course.count() == 0:
                course = Platform()
                course.name = course_name
                course.description = record['Programme specification'].strip()
                course.url = root_url
                if country_code:
                    course.countries = [country_code]
                course.contactPhone = record['Telephone'][:20]
                course.contactPointEmail = record['E-mail'].split(',')[0]
                course.qualification = record['Qualification required']
                course.creator = sys_user
                course.geoExtend = default_extend
                course.approved = True
                course.active = True
                course.save()
                course.organisation.add(org)
                log_message(course, 'Imported', sys_user, ADDITION)
                type = remove_parenthesis(record['Type of program'])
                for candidate in type.split(','):
                    topic_name = candidate.replace("'s", "").strip().capitalize()
                    if len(topic_name) > 0:
                        topic, topic_inserted = Topic.objects.get_or_create(topic=topic_name)
                        if topic_inserted:
                            print(f'Topic created {topic_name}')
                        course.topic.add(topic)

                valid, candidate_image = load_and_get_image(root_url, f'course_{course.id}')
                if not valid:
                    print('URL not valid %s' % root_url)
                    course.approved = False
                    course.save()
                else:
                    if candidate_image:
                        assign_image(candidate_image, course.logo, 600, 400)
                        assign_image(candidate_image, course.profileImage, 1320, 400)
                        course.save()
                        tot_images_saved += 1

                tot_saved += 1

            transaction.commit()

        print(f'Records read: {tot_records}')
        print(f'Organisations saved: {tot_new_org}')
        print(f'Schools saved: {tot_saved}')