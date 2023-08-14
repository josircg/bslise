import csv
import re
import requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from PIL import Image

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.admin.models import ADDITION
from django.core.files.images import ImageFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django_countries import countries as countries_list
from eucs_platform.logger import log_message
from platforms.models import *
from organisations.models import *
from utilities.file import save_image_with_path


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
        org_type_unknown = OrganisationType.objects.get_or_create(type='Unknown')[0]
        default_extend = GeographicExtend.objects.filter(description='Regional')[0]

        transaction.set_autocommit(False)
        file = open(filename, 'r')
        for record in csv.DictReader(file, delimiter=';'):
            tot_records += 1
            org_name = record['Institution'].strip()
            course_name = record['Academic unit'].strip()
            country_code = record['Code']
            country = countries_list.countries.get(country_code, None)
            root_url = record['Web address']
            parse_url = urlparse(root_url)
            root_url = root_url.replace(parse_url.path,'')
            if not country:
                print('Country %s not found (%s)' % (record['Code'], record['Country']))

            org = Organisation.objects.filter(name=org_name)
            if org.count() == 0:
                org = Organisation()
                org.name = org_name
                if record['Address'] and record['Address'] != record['Country']:
                    org.description = record['Address']
                else:
                    org.description = record['Contact information'].split(';')[0]
                    org.description = org.description.replace(course_name,'').strip()[:200]
                org.country = country_code
                org.url = root_url
                org.creator = sys_user
                org.orgType = org_type_unknown
                org.latitude = round(float(record['Latitude'].replace(',','.')),5)
                org.longitude = round(float(record['Longitude'].replace(',','.')),5)
                org.approved = True
                try:
                    org.save()
                except:
                    from django.db import connection
                    result = connection.queries
                    raise
                log_message(org, 'Imported', sys_user, ADDITION)
                tot_new_org += 1
            else:
                org = org[0]

            course = Platform.objects.filter(name=course_name, organisation=org)
            if course.count() == 0:
                course = Platform()
                course.name = course_name
                course.description = record['Programme specification'].strip()
                course.url = record['Web address']
                course.countries = [country_code]
                course.contactPhone = record['Telephone']
                course.contactPointEmail = record['E-mail']
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

                valid, candidate_image = load_and_get_image(record['Web address'], f'course_{course.id}')
                if not valid:
                    print('URL not valid %s' % record['Web address'])
                    course.approved = False
                    course.save()
                else:
                    if candidate_image:
                        course.profileImage.name = candidate_image
                        course.save()
                        if '.svg' not in candidate_image:
                            image = Image.open(course.profileImage.file)
                            resized_image = image.resize((600, 400), Image.ANTIALIAS)
                            save_image_with_path(resized_image, course.profileImage.name)
                            resized_image = image.resize((1320, 400), Image.ANTIALIAS)
                            save_image_with_path(resized_image, course.profileImage.name)
                        else:
                            print(f'SVG {candidate_image}')
                        tot_images_saved += 1

                tot_saved += 1

            transaction.commit()

        print(f'Records read: {tot_records}')
        print(f'Organisations saved: {tot_new_org}')
        print(f'Schools saved: {tot_saved}')