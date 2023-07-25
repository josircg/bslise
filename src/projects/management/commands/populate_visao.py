# -*- coding: utf-8 -*-
import requests
import json
from django.conf import settings

from django.core.management.base import BaseCommand

from projects.models import *
from eucs_platform import visao


def create_dataset(auth_header, id, name):
    endpoint = settings.VISAO_URL
    record = {"name": name,
              "active": True, "keyWord": f"Tema {id}",
              "description": "Tema registrado na Civis",
              "bigArea": {"id": 12, "name": "Informação e Comunicação"}
              }
    response = requests.put(f'{endpoint}/app/api/group-layers',
                             json=record, timeout=20,
                             verify=False, headers=auth_header)
    if response.status_code == 201:
        record = json.loads(response.content)
        return record['id']
    else:
        try:
            record = json.loads(response.content)
            return record['detail']
        except:
            return response.status_code


class Command(BaseCommand):
    label = 'Populate Visão with Project info'

    def populate_projects(self):
        # Remove todos os projetos existentes
        auth_header = visao.authenticate()
        tot_projects = visao.delete_all(auth_header)
        print(f'Projects removed: {tot_projects}')
        tot_projects = 0
        for project in Project.objects.filter(approved=True):
            visao.save_project(project, auth_header)
            tot_projects += 1
        print(f'Projects added: {tot_projects}')

    # Cria os datasets dos tópicos
    def populate_topics(self):
        auth_header = visao.authenticate()
        for topic in Topic.objects.all():
            if topic.project_set.count() > 0:
                dataset_id = create_dataset(auth_header, topic.id, topic.topic)
                if dataset_id:
                    topic.external_url = f'grupCategory={dataset_id}&l=191&e=f'
                    topic.save()
                    for project in topic.project_set.all():
                        visao.save_project(project, auth_header, dataset_id)

    def add_arguments(self, parser):
        parser.add_argument('--function', type=str, help='Function to execute')

    def handle(self, *args, **options):
        if options['function'] == 'auth':
            auth_header = visao.authenticate()
            print('Auth ok')
            query = {'groupId.equals': settings.VISAO_LAYER}
            endpoint = settings.VISAO_URL
            response = requests.get(f'{endpoint}/app/api/layers', params=query, headers=auth_header)
            print('Records found: %s' % len(response.json()))

        elif options['function'] == 'topics':
            record = {'name': 'Agriculture & Veterinary science',
                      'active': True,
                      'keyWord': 1,
                      'description': 'Tema registrado na Civis',
                      'bigArea': {'id': 12, 'name': 'Informação e Comunicação'}}
            auth_header = visao.authenticate()
            print('Auth ok')
            endpoint = settings.VISAO_URL
            response = requests.put(f'{endpoint}/app/api/group-layer', json=record, headers=auth_header)
            print(response.status_code)

            # self.populate_topics()

        elif options['function'] == 'projects':
            self.populate_projects()

        else:
            print('Function not defined')
