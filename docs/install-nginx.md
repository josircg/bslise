Tutorial de Instalação de um servidor do CIVIS para ambiente de produção:

1) Instalação dos pacotes básicos (logado como root) e configuração do timezone:

````
apt-get install -y nginx build-essential libssl-dev python3-dev python-setuptools libxml2-dev supervisor git libfreetype6 libfreetype6-dev python3-virtualenv libpq-dev
dpkg-reconfigure tzdata
````

2) Criação do usuário webapp e permissões de uso (logado como root)

````
adduser  --gecos "" webapp
usermod -a -G www-data webapp
cd /var
mkdir webapp
chown root:www-data webapp
chmod g+ws webapp
cd /etc/nginx/
sudo chown root:www-data sites-enabled
sudo chown root:www-data sites-available
sudo chmod 775 sites-*
sudo chown root:www-data /var/log/nginx
sudo chmod 775 /var/log/nginx
sudo chown webapp:www-data /etc/supervisor/conf.d
sudo chmod 775 /etc/supervisor/conf.d
````

3) Criação da chave pública para enviar para o gitlab

````
su - webapp
ssh-keygen -N ''
cd .ssh
cat id_rsa.pub
````

4) Ainda logado como webapp, instalar o ambiente:

> virtualenv civis

Outra opção é utilizar: mkvirtualenv civis -p python3

5)Ativar virtualenv
```
cd civis
source bin/activate
mkdir logs
```

6) Clonar o repositório (Não é necessário nenhuma senha pois a chave já foi incluida gitlab)
> git clone  git@git.ibict.br:cgti/civis.git

7) Entrar no repositório e instalar as bibliotecas do python

```
cd civis
pip install -r requirements.txt
```

8) Novamente logado como root, configurar o NGINX

* copiar o arquivo nginx.conf para /etc/nginx/sites-available/ e alterar os parâmetros necessários
* para testar se a configuração foi bem sucedida, executar: nginx -t 
* para aplicar os ajustes: sudo systemctl restart nginx

9) Configurar o supervisor

* Copiar o arquivo supervisor.conf para /etc/supervisor/conf.d/ e alterar os parâmetros necessários
* aplicar as alterações: systemctl restart supervisor

10) Banco de Dados utiliza PostGIS [*] (Logado como superuser)

```
sudo apt install postgis postgresql-12-postgis-3
sudo apt-get install postgresql-12-postgis-3-scripts
```
[*] https://www.vultr.com/docs/install-the-postgis-extension-for-postgresql-on-ubuntu-linux/

```
su - postgres psql
create user eucitizenscience_usr with encrypted password 'mypass';
create database civis with owner=eucitizenscience_usr;
\connect civis;
create extension postgis;
GRANT ALL on public.spatial_ref_sys TO eucitizenscience_usr;
```
