import csv

from django.conf import settings
from django.core.management.base import BaseCommand
from projects.models import *


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
        file = open(filename, 'r')
        for record in csv.DictReader(file, delimiter=';'):
            print(record)
            tot_records += 1

        print(f'Records read {tot_records}')
        print(f'Projects saved {tot_saved}')