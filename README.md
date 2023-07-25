# CIVIS

CIVIS is a web platform to register and maintain Citizen Science initiatives and project in Latin America. 
It is a fork of [EU-CS_platform][0] and it's built with [Python][1] using the [Django Web Framework][2]. 

## Requirements

    sudo apt install python3-venv python3-pip libpq-dev gettext

## Configure postgres

1) If you are going to install postgresql in the app server:

   ```
   sudo apt install postgresql postgis postgresql-12-postgis-3
   ```
   
2) Open psql console:
```
create database eucitizenscience;
create user eucitizenscience_usr with password 'XXX';
grant all on database eucitizenscience to eucitizenscience_usr;
\connect eucitizenscience;
create extension postgis;
```
## Python Installation

1) In source directory:

```
python3 -m venv venv
source venv/bin/activate
git clone git@git.ibict.br:cgti/civis.git
cd civis
pip install -r requirements.txt
cd src
cp eucs_platform/settings/local.sample.reference.env eucs_platform/settings/local.env
```

2) Edit local.env with database and email configuration and test your configuration

```
python manage.py check
```

3) To install a empty database, run: 

```
python manage.py migrate
python manage.py loaddata projects/fixtures/topics.json
python manage.py loaddata projects/fixtures/status.json
python manage.py loaddata projects/fixtures/participationtasks.json
python manage.py loaddata projects/fixtures/geographicextend.json
python manage.py loaddata resources/fixtures/categories.json
python manage.py loaddata resources/fixtures/themes.json
python manage.py loaddata resources/fixtures/audiences.json
python manage.py loaddata organisations/fixtures/organisation_types.json
```

4) To restore a existing database:

```

python manage.py migrate
```

## Launch
```
python manage.py runserver
```

## Cron jobs commands [4]
```
python manage.py runcrons
python manage.py runcrons --force
```

And to do this automatically:
```
python manage.py crontab add
```

## Running on a production server

1) Install NGINX and Supervisor

sudo apt install -y libssl-dev nginx supervisor 

2) Copy default configuration (assuming you installed on /opt/civis)

```
cd /opt/civis
cp docs/nginx.conf /etc/nginx/sites-enabled/civis.conf
cp docs/supervisor.conf /etc/supervisor/conf.d/civis.conf  
```

3) Adjust the files with the correct path and domain

4) Restart nginx: systemctl restart nginx

5) Verify supervisor configuration: supervisorctl reload

6) Verify the wsgi.py setttings configuration 

[1]: https://eu-citizen.science/
[2]: https://www.python.org/
[3]: https://www.djangoproject.com/
[4]: https://pypi.org/project/django-crontab/ 