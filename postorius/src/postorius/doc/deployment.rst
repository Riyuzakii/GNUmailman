============
Deployment
============

.. note::
    This guide covers deployment options of Postorius.


Nginx with uwsgi
================

.. note::
    Please refer to nginx and uwsgi documentation for explanation of the shown
    snippets.

Below is an example uwsgi configuration file:

::

    [uwsgi]

    chdir           = /srv/django/mailman
    module          = example_project.wsgi
    virtualenv      = /srv/django/mailman/env

    master          = true
    processes       = 4
    socket          = /run/uwsgi/mailman.sock
    #chmod-socket   = 666

    vacuum          = true
    plugin          = python2

    uid             = http
    gid             = http

And a nginx server section to with it:

::

		upstream mailman {
				server unix:///run/uwsgi/mailman.sock;
		}

		server {
				listen      80;
				# TODO Replace with your domain
				server_name lists.example.com;
				return 301	https://$server_name$request_uri;

		}

		## Config for server secured with https
		server {
			listen   443;

			# TODO Replace with your domain
			server_name lists.example.com;


			ssl			on;
			# TODO Replace with your crt and key
			ssl_certificate		/etc/nginx/keys/lists.example.com.crt;
			ssl_certificate_key  	/etc/nginx/keys/lists.example.com.key;
			ssl_session_timeout 	5m;
			ssl_ciphers 		'AES128+EECDH:AES128+EDH';
			ssl_protocols TLSv1 TLSv1.1 TLSv1.2;
			ssl_prefer_server_ciphers 	on;
			add_header Strict-Transport-Security "max-age=63072000; includeSubdomains; preload";

			charset     utf-8;

			# max upload size
			client_max_body_size 75M;   # adjust to taste

			location /static {
					# TODO Adjust to your static location
					alias /srv/django/mailman/public/static;
			}

			# Finally, send all non-media requests to the Django server.
			location / {
					uwsgi_pass  mailman;
					include     /etc/nginx/uwsgi_params; # the uwsgi_params file you installed
			}
		}


Apache with mod_wsgi
====================

.. note::
    This guide assumes that you know how to setup a VirtualHost with Apache.
    If you are using SQLite, the ``.db`` file as well as its folder need to be
    writable by the web server.

These settings need to be added to your Apache VirtualHost:

::

    Alias /static /srv/django/mailman/public/static
    <Directory "/srv/django/mailman/public/static">
        Order deny,allow
        Allow from all
    </Directory>

    WSGIScriptAlias / /srv/django/mailman/srv/postorius.wsgi
    <Directory "/srv/django/mailman/srv">
        Order deny,allow
        Allow from all
    </Directory>

The first Alias serves the static files (CSS, JS, Images, etc.). The
WSGIScriptAlias serves the Django application. The paths need to be changed
depending on which location you have your postorius project in.

Final setup instructions
========================

We're almost ready. But you need to create translations and collect the static
files from Postorius (which resides somewhere on your pythonpath) to be able to
serve them from the site directory. All you have to do is to change into the
postorius project directory and run:

::

    $ python manage.py compilemessages
    $ python manage.py collectstatic

After reloading the webserver Postorius should be running!
