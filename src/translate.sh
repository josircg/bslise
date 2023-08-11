#!/bin/bash
$1/python manage.py makemessages --no-location
$1/python utilities/clean.py
$1/python manage.py compilemessages