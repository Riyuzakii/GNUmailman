============
Installation
============

.. note::
    This installation guide covers Postorius, the web user interface for
    GNU Mailman 3. To install GNU Mailman follow the instructions in the `documentation`_.

    If you are looking for an easy way to set up the whole GNU Mailman 3
    suite (GNU Mailman 3, Postorius, Hyperkitty and mailmanclient), check
    out the `mailman-bundler`_ project on GitLab.

.. _mailman-bundler: https://gitlab.com/mailman/mailman-bundler
.. _documentation: http://mailman.readthedocs.org

Install Postorius
=================


Latest release
--------------

If you just want to install the latest release of Postorius, install it from
PyPi:

::

    $ pip install postorius


Latest dev version
------------------

If you want to always be up to date with the latest development version, you
should install Postorius using git:

::

    $ git clone https://gitlab.com/mailman/postorius.git
    $ cd postorius
    $ python setup.py develop

.. note::
    This note only pertains to development installs and should not be used when 
    doing production installs.
    
    When setting up or running your local dev environment, you may run into some 
    errors. You may want to consider installing mailman modules from source as 
    changes may not yet be published to PyPI. Example usage below:

::

    $ pip uninstall mailmanclient
    $ pip install git+https://gitlab.com/mailman/mailmanclient.git

Setup your django project
=========================

Since you have now installed the necessary packages to run Postorius, it's
time to setup your Django site.

You can find an example project in ``example_project`` in the root of
``postorius'`` git repository.

Change the database setting in ``example_project/settings.py`` to
your preferred database, if you want something other than SQlite.

.. note::
    Detailed information on how to use different database engines can be found
    in the `Django documentation`_.

.. _Django documentation: https://docs.djangoproject.com/en/1.9/ref/settings/#databases

Third, prepare the database:

::

    $ cd example_project
    $ python manage.py migrate

This will create the ``.db file`` (if you ar using SQLite) and will setup all the
necessary db tables.

To create a superuser which will act as an admin account for Postorius, run the
following commands::

    $ cd example_project
    $ python manage.py createsuperuser


Running the development server
==============================

The quickest way to run Postorius is to just start the development server:

::

    $ cd example_project
    $ python manage.py runserver


.. warning::
    You should use the development server only locally. While it's possible to
    make your site publicly available using the dev server, you should never
    do that in a production environment.
