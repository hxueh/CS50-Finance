# CS50 Finance in MySQL

Rewrite [CS50 Finance's](https://finance.cs50.net) background. Instead of SQLite, using MySQL. Just for fun🙃

## Requirements
MySQL
PyMySQL
Flask
Flask_Session
mod_wsgi

## Get ready.
```
$ pip3 install -r requirements.txt

$ mysql

$ CREATE DATABASE IF NOT EXISTS cs50_finance
```

Create a mysql.txt file containing your MySQL database name, username and password.
The first line is your database name, second line is the username and the third is your password. If your password is empty, just leave it blank.

e.g.
```
cs50_finance
username
yourpassword
```

If you don't create mysql.txt, the default db, username and password is "cs50_finance", "root" and ""(blank).

## Run the app
```
python3 application.py
```

## Put it onto server

We will need [LAMP](https://linode.com/docs/web-servers/lamp/install-lamp-stack-on-ubuntu-16-04/) deployed.

```
$ sudo apt-get install apache2-dev
$ sudo pip3 install pymysql flask flask_session mod_wsgi
```

In `/etc/apache2/sites-available`, create a conf file. e.g. finance.conf
Change the below example.com and pathto to your domain and path to the Finance folder.

```
<VirtualHost *:80>
        ServerName example.com
        ServerAdmin mail@example.com
        WSGIScriptAlias / /pathto/Finance/finance.wsgi
        <Directory /pathto/Finance/>
                Order allow,deny
                Allow from all
        </Directory>
        <Directory /pathto/Finance>
                Order deny,allow
                Allow from all
        </Directory>
        Alias /static /pathto/Finance/static
        <Directory /pathto/Finance/static/>
                Order allow,deny
                Allow from all
        </Directory>
        ErrorLog ${APACHE_LOG_DIR}/error.log
        LogLevel warn
        CustomLog ${APACHE_LOG_DIR}/access.log combined
</VirtualHost>
```

```
$ sudo a2ensite finance
```

We should also enable mod_wsgi

```
$ mod_wsgi-express module-config
```
Put the output into wsgi.load in /etc/apache2/mods-available/

Then

```
$ sudo a2enmod wsgi
$ sudo service apache2 restart
```