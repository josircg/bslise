# Interface com a plataforma Visão
import json
from base64 import b64encode

import requests
from datetime import datetime, timezone
from django.conf import settings


# Retorna o header de autorização ou nulo
def authenticate(username=None):
    if username or settings.VISAO_USERNAME:
        username = username or settings.VISAO_USERNAME
        password = settings.VISAO_PASSWORD
        endpoint = settings.VISAO_URL
        token = b64encode(f"{username}:{password}".encode('utf-8')).decode("ascii")
        token = f'Basic {token}'
        headers = { 'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Authorization': token}
        try:
            requests.packages.urllib3.disable_warnings()
            response = requests.post(f'{endpoint}/visao2/api2/session/getAccessTokenVisaoMonolitico',
                                    verify=False, timeout=20, headers=headers)
            if response.status_code == 200:
                token = response.content.decode('utf-8')
                if token:
                    return {'Authorization': 'Bearer %s' % token}
            else:
                detail = response.json()
                if type(detail) == dict and detail.get('detail'):
                    return '%s: %s' % (response.status_code, detail['detail'])
                else:
                    return 'Status Code:%s' % response.status_code
        except Exception as e:
            return e.__str__()


# Insert or Update the Project on a Visão Dataset (based on Project Name)
# A Dataset in Visão is registered as "Group layer" and each project is registered as a layer.
def save_project(project, auth_header, dataset_id=None):
    dt_created = None
    dataset_id = dataset_id or settings.VISAO_LAYER
    today = datetime.now(timezone.utc).replace(tzinfo=timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    if not project.latitude or not project.longitude:
        print('Latitude or Longitude not filled: %d' % project.id)
        return
    else:
        if type(project.latitude) == str:
            geojson = "[%s,%s]" % (project.latitude, project.longitude)
        else:
            geojson = "[%f,%f]" % (project.latitude, project.longitude)
    query = {'groupId.equals': dataset_id, 'name.equals': project.name}
    endpoint = settings.VISAO_URL
    response = requests.get(f'{endpoint}/app/api/layers', params=query, verify=False, headers=auth_header)
    if response.status_code == 200:
        # A data tem que estar no formato TMZ "2022-08-23T12:45:00.000Z"
        result = json.loads(response.text)
        if len(result) > 0:
            for item in result:
                dt_created = item['date']
                item_id = item['id']
                if item_id:
                    response = requests.delete(f'{endpoint}/app/api/layers/{item_id}',
                                               verify=False, headers=auth_header)

    domain = settings.DOMAIN
    record = {
        "name": project.name,
        "geoJson": geojson,
        "type": "MARKER",
        "description": '\"<a href=\'%s/project/%s\' target=\'blank\'>'
                       'Visualize a iniciativa</a>\"' % (domain, project.id),
        "date": dt_created or today,
        "source": project.organisation.name or 'Civis',
        "latitude": project.latitude,
        "longitude": project.longitude,
        "dateChange": today,
        "group": {"id": dataset_id}
    }
    response = requests.post(f'{endpoint}/app/api/layers', json=record, timeout=20,
                             verify=False, headers=auth_header)
    if response.status_code == 201:
        result = 'OK'
    else:
        result = 'Post error'
    return result


def delete_project(project, auth_header, dataset_id=None):
    endpoint = settings.VISAO_URL
    dataset_id = dataset_id or settings.VISAO_LAYER
    query = {'groupId.equals': dataset_id, 'name.equals': project.name}
    response = requests.get(f'{endpoint}/app/api/layers', params=query, verify=False,
                            headers=auth_header)
    if response.status_code == 200:
        result = json.loads(response.text)
        if len(result) > 0:
            for item in result:
                item_id = item['id']
                response = requests.delete(f'{endpoint}/app/api/layers/{item_id}', verify=False, headers=auth_header)
    return 'OK'


def delete_all(auth_header, dataset_id=None):
    tot_excluidos = 0
    endpoint = settings.VISAO_URL
    query = {'groupId.equals': dataset_id}
    response = requests.get(f'{endpoint}/app/api/layers', params=query, verify=False,
                            headers=auth_header)
    if response.status_code == 200:
        result = json.loads(response.text)
        if len(result) > 0:
            for item in result:
                item_id = item['id']
                response = requests.delete(f'{endpoint}/app/api/layers/{item_id}', verify=False, headers=auth_header)
                if response.status_code == 200:
                    tot_excluidos += 1
                else:
                    print('API error %d' % response.status_code)
    return tot_excluidos
