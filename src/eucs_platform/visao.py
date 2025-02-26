# Interface com a plataforma Visão
import json
from base64 import b64encode
from datetime import datetime, timezone

import requests
from django.conf import settings
from django.utils.translation import ugettext_lazy as _


# Return formatted exception
def error_detail(response):
    try:
        detail = response.json()
    except Exception:
        detail = None
    if type(detail) is dict and detail.get('detail'):
        return Exception('%s: %s' % (response.status_code, detail['detail']))
    else:
        return Exception('Status Code:%s' % response.status_code)


# Retorna o header de autorização ou mensagem de erro
def authenticate2(username=None):
    if username or settings.VISAO_USERNAME:
        username = username or settings.VISAO_USERNAME
        password = settings.VISAO_PASSWORD
        endpoint = settings.VISAO_URL
        token = b64encode(f"{username}:{password}".encode('utf-8')).decode("ascii")
        token = f'Basic {token}'
        headers = {'Content-Type': 'application/json',
                   'Access-Control-Allow-Origin': '*',
                   'Authorization': token}
        requests.packages.urllib3.disable_warnings()
        response = requests.post(f'{endpoint}/visao2/api2/session/getAccessToken',
                                 verify=False, timeout=20, headers=headers)
        if response.status_code == 200:
            return response.cookies
        else:
            raise error_detail(response)


# Return the dataset ID on Visão from the map URL
def get_topic_id(external_url):
    return external_url.split('l=')[-1]


# Return project layers
def get_project_layers(project, auth_header, dataset_id=None):
    endpoint = settings.VISAO_URL
    domain = settings.DOMAIN
    if not dataset_id:
        query = {'name.contains': f'{domain}/project/{project.id}'}
    else:
        query = {'groupId.equals': dataset_id, 'name.contains': f'civis.ibict.br/project/{project.id}'}

    layers = []
    response = requests.get(f'{endpoint}/app/api/layers', params=query, verify=False,
                            headers=auth_header)
    if response.status_code == 200:
        result = json.loads(response.text)
        if len(result) > 0:
            for item in result:
                layers.append(item['id'])

    return layers


def get_organisation_layers(platform, auth_header, dataset_id=None):
    endpoint = settings.VISAO_URL
    domain = settings.DOMAIN
    if not dataset_id:
        query = {'name.contains': f'{domain}/platform/{platform.id}'}
    else:
        query = {'groupId.equals': dataset_id, 'name.contains': f'{domain}/platform/{platform.id}'}

    layers = []
    response = requests.get(f'{endpoint}/app/api/layers', params=query, verify=False,
                            headers=auth_header)
    if response.status_code == 200:
        result = json.loads(response.text)
        if len(result) > 0:
            for item in result:
                layers.append(item['id'])

    return layers


# Cria um layer - API 2
def create_project_layer(project):
    if not project.latitude or not project.longitude:
        print('Latitude or Longitude not filled: %d' % project.id)
        return None
    else:
        if type(project.latitude) is str:
            geojson = "[%s,%s]" % (project.latitude, project.longitude)
        else:
            geojson = "[%f,%f]" % (project.latitude, project.longitude)
    domain = settings.DOMAIN
    description = 'Visualizar Projeto'
    return {
        "name": project.name,
        "geoJson": geojson,
        "type": "CIRCLE",
        "description": f'<a href=\'{domain}/project/{project.id}\' target=\'blank\'>{description}</a>',
        "source": project.organisation.name or settings.SITE_NAME,
        "latitude": project.latitude,
        "longitude": project.longitude,
    }


# Insert or Update the Project on a Visão Dataset - API Versão 1
# A Dataset in Visão is registered as "Group layer" and each project is registered as a layer.
def save_project(project, auth_header, dataset_id=None):
    dt_created = None
    all_layers = dataset_id is None
    dataset_id = dataset_id or settings.VISAO_LAYER
    if all_layers:
        layers_list = get_project_layers(project, auth_header)

    map_id = get_project_layers(project, auth_header, dataset_id)

    today = datetime.now(timezone.utc).replace(tzinfo=timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    if not project.latitude or not project.longitude:
        print('Latitude or Longitude not filled: %d' % project.id)
        return
    else:
        if type(project.latitude) is str:
            geojson = "[%s,%s]" % (project.latitude, project.longitude)
        else:
            geojson = "[%f,%f]" % (project.latitude, project.longitude)

    domain = settings.DOMAIN
    endpoint = settings.VISAO_URL
    description = _('View Project')
    record = {
        "name": project.name,
        "geoJson": geojson,
        "type": "CIRCLE",
        "description": f'<a href=\'{domain}/project/{project.id}\' target=\'blank\'>{description}</a>',
        "date": dt_created or today,
        "source": project.organisation.name or settings.SITE_NAME,
        "latitude": project.latitude,
        "longitude": project.longitude,
        "dateChange": today,
        "group": {"id": dataset_id}
    }
    if map_id:
        record['id'] = map_id[0]
        response = requests.put(f'{endpoint}/app/api/layers', json=record, timeout=20,
                                verify=False, headers=auth_header)
        if response.status_code == 201:
            result = 'OK'
        else:
            raise error_detail(response)
    else:
        response = requests.post(f'{endpoint}/app/api/layers', json=record, timeout=20,
                                 verify=False, headers=auth_header)
        if response.status_code == 201:
            result = 'OK'
        else:
            raise Exception(response)

    if all_layers:
        for topic in project.topic.filter(external_url__isnull=False):
            dataset_id = get_topic_id(topic.external_url)
            save_project(project, auth_header, dataset_id=dataset_id)
            layers_list.remove(dataset_id)

        # those not inserted or updated, should be deleted
        for dataset_id in layers_list:
            delete_project(project, auth_header, dataset_id=dataset_id)

    return result


def delete_project(project, auth_header, dataset_id=None):
    endpoint = settings.VISAO_URL
    if not dataset_id:
        query = {'name.contains': f'civis.ibict.br/project/{project.id}'}
    else:
        query = {'groupId.equals': dataset_id, 'name.contains': f'civis.ibict.br/project/{project.id}'}
    response = requests.get(f'{endpoint}/app/api/layers', params=query, verify=False,
                            headers=auth_header)
    if response.status_code == 200:
        result = json.loads(response.text)
        if len(result) > 0:
            for item in result:
                item_id = item['id']
                response = requests.delete(f'{endpoint}/app/api/layers/{item_id}', verify=False, headers=auth_header)
    return 'OK'


def save_organisation(organisation, auth_header, dataset_id=None):
    dt_created = None
    all_layers = dataset_id is None
    dataset_id = dataset_id or settings.VISAO_LAYER
    if all_layers:
        layers_list = get_organisation_layers(organisation, auth_header)

    map_id = get_organisation_layers(organisation, auth_header, dataset_id)

    today = datetime.now(timezone.utc).replace(tzinfo=timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    if not organisation.latitude or not organisation.longitude:
        print('Latitude or Longitude not filled: %d' % organisation.id)
        return
    else:
        if type(organisation.organisation.latitude) is str:
            geojson = "[%s,%s]" % (organisation.organisation.latitude, organisation.organisation.longitude)
        else:
            geojson = "[%f,%f]" % (organisation.organisation.latitude, organisation.organisation.longitude)

    domain = settings.DOMAIN
    endpoint = settings.VISAO_URL
    description = _('View Project')
    record = {
        "name": organisation.name,
        "geoJson": geojson,
        "type": "CIRCLE",
        "description": f'<a href=\'{domain}/project/{organisation.id}\' target=\'blank\'>{description}</a>',
        "date": dt_created or today,
        "source": organisation.organisation.name or settings.SITE_NAME,
        "latitude": organisation.organisation.latitude,
        "longitude": organisation.organisation.longitude,
        "dateChange": today,
        "group": {"id": dataset_id}
    }
    if map_id:
        record['id'] = map_id[0]
        response = requests.put(f'{endpoint}/app/api/layers', json=record, timeout=20,
                                verify=False, headers=auth_header)
        if response.status_code == 201:
            result = 'OK'
        else:
            raise error_detail(response)
    else:
        response = requests.post(f'{endpoint}/app/api/layers', json=record, timeout=20,
                                 verify=False, headers=auth_header)
        if response.status_code == 201:
            result = 'OK'
        else:
            raise Exception(response)

    if all_layers:
        for topic in organisation.topic.filter(external_url__isnull=False):
            dataset_id = get_topic_id(topic.external_url)
            save_project(organisation, auth_header, dataset_id=dataset_id)
            layers_list.remove(dataset_id)

        # those not inserted or updated, should be deleted
        for dataset_id in layers_list:
            delete_project(organisation, auth_header, dataset_id=dataset_id)

    return result


