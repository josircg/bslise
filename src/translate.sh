#!/bin/bash
# $1/python manage.py makemessages --no-location
# msgattrib locale/pt_BR/LC_MESSAGES/django.po --clear-fuzzy --clear-previous -o locale/pt_BR/LC_MESSAGES/django.po
# msgattrib locale/es/LC_MESSAGES/django.po --clear-fuzzy --clear-previous -o locale/es/LC_MESSAGES/django.po
$1/python manage.py makemessages
$1/python utilities/clean.py
$1/python manage.py compilemessages