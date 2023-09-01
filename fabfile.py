import os

from fabric import task, Connection
from io import BytesIO
from datetime import datetime


def deploy(connection):
    with connection.cd('/var/webapp/bslise/bslise/src/'):
        connection.run('git pull')
        connection.run('/home/webapp/bslise/bin/python manage.py migrate')
        connection.run('/home/webapp/bslise/bin/python manage.py compilemessages --use-fuzzy')
        connection.run('/home/webapp/bslise/bin/python manage.py collectstatic --noinput')
        connection.run('supervisorctl restart bslise')
        print('Atualização efetuada com sucesso!')


def upgrade_requirements(connection):
    with connection.cd('/var/webapp/bslise/bslise/src'):
        connection.run('git pull')
        # connection.run('/home/webapp/bslise/bin//pip install django_select2 --upgrade')
        connection.run('/home/webapp/bslise/bin/pip install -r ../requirements.txt')
        print('Atualização efetuada')


@task
def upgrade_producao(context):
    upgrade_requirements(Connection('webapp@172.16.16.246', port=25000))


@task
def deploy_producao(context):
    deploy(Connection('webapp@172.16.16.246', port=25000))


#@task
# def deploy_hml(context):
#    deploy(Connection('webapp@172.16.17.126', port=25000))


#@task
#def connect_hml(context):
#    connection = Connection('webapp@172.16.17.126', port=25000)
#    with connection.cd('/var/webapp/'):
#        result = connection.run('ls', hide=True)
#    msg = "Ran {0.command!r} on {0.connection.host}, got stdout:\n{0.stdout}"
#    print(msg.format(result))


def read_var(connection, file_path, encoding='utf-8'):
    io_obj = BytesIO()
    connection.get(file_path, io_obj)
    return io_obj.getvalue().decode(encoding)


def get_database(connection, banco, path):
    with connection.cd(path):
        print('Conectado')
        filename = path + '/bd.pwd'
        print('Lendo %s' % filename)
        senha = read_var(connection, filename).strip()
        print('Senha encontrada')
        filename = path + '/backup%s.gz' % datetime.strftime(datetime.now(),'%Y%m%d')
        connection.run('pg_dump postgresql://bslise:%s@%s | gzip > %s' %
                       (senha, banco, filename))
        print(f'Backup PostgreSQL gerado em {filename}')
        connection.get(filename)
        print(f'Backup copiado na pasta local')
        connection.run(f'rm {filename}')


def get_mediafiles(connection, path):
    with connection.cd(path):
        filename = os.path.join(path, 'media%s.zip' % datetime.strftime(datetime.now(),'%Y%m%d'))
        print(filename)
        connection.run(f'zip -r {filename} bslise/src/media')
        connection.get(filename)

@task
def backup_local(context):
    get_database(Connection('supervisor@192.168.0.24'), 'bslise', '')


@task
def backup_hml(context):
    connection = Connection('webapp@172.16.17.126', port=25000)
    #get_database(connection,
    #       banco='localhost/civis',
    #       path='/var/webapp/backup')
    get_mediafiles(connection, '/var/webapp/bslise')


@task
def backup_producao(context):
    get_database(Connection('webapp@172.16.16.126', port=25000),
           banco='localhost/xxxx',
           path='/var/webapp/backup')
    get_mediafiles(Connection('webapp@directory.bslise.org'), '/var/webapp/bslise')