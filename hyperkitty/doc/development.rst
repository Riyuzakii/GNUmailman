===========
Development
===========

Building documentation
======================

The full documentation is located in the "doc" subfolder. It can be generated
in various formats once you have installed `Sphinx`_. To generate the HTML documentation,
run the following command::

    make -C doc html

The HTML files will be available in the ``doc/_build/html`` directory.

The documentation can also be browsed online at:
https://hyperkitty.readthedocs.org.

.. _Sphinx: http://sphinx-doc.org


Communication channels
======================

Hang out on IRC and ask questions on ``#mailman`` or join the `mailing list`_
``hyperkitty-devel@lists.fedorahosted.org``.

.. _mailing list: https://lists.fedorahosted.org/mailman/listinfo/hyperkitty-devel


Setting up HyperKitty for development
=====================================

The recommended way to develop on HyperKitty is to use VirtualEnv. It will
create an isolated Python environment where you can add HyperKitty and its
dependencies without messing up your system Python install.

First, create the virtualenv and activate it::

    virtualenv venv_hk
    source venv_hk/bin/activate

Then download the components of HyperKitty::

    git clone https://gitlab.com/mailman/hyperkitty.git
    cd hyperkitty
    python setup.py develop

.. include:: _sass.rst

Configuration
=============

For a development setup, you should create a
``example_project/settings_local.py`` file with at least the following
content::

    DEBUG = True
    TEMPLATE_DEBUG = DEBUG
    USE_SSL = False

It's also recommended to change the database access paths in the ``DATABASES``
and ``HAYSTACK_CONNECTIONS`` variables. Absolute paths are required.

If you ever want to turn the ``DEBUG`` variable to ``False`` (by removing it
from ``settings_local.py``), you'll have to run two additional commands then
and each time you change the static files::

    django-admin collectstatic --pythonpath example_project --settings settings
    django-admin compress --pythonpath example_project --settings settings

Normally, to generate compressor content, you'll need to set ``COMPRESS_ENABLED`` to ``TRUE``
and ``COMPRESS_OFFLINE`` to ``TRUE`` in ``settings_local.py``. However, you can force the generation of
compressor content by adding the ``--force`` switch to the ``django-admin compress`` command, which
will run the compressor even if the ``COMPRESS`` settings are not ``TRUE``.

But for development purposes, it's better to keep ``DEBUG = True``.

.. note::
    Your ``django-admin`` command may be called ``django-admin.py`` depending
    on your installation method.


.. Setting up the databases

.. include:: database.rst


Running HyperKitty
==================

If you're coding on HyperKitty, you can use Django's integrated web server.
It can be run with the following command::

    django-admin runserver --pythonpath example_project --settings settings

.. warning::
    You should use the development server only locally. While it's possible to
    make your site publicly available using the dev server, you should never
    do that in a production environment.


Testing
=======

Use the following command::

    django-admin test --pythonpath example_project --settings settings hyperkitty

All test modules reside in the ``hyperkitty/tests`` directory
and this is where you should put your own tests, too. To make the django test
runner find your tests, make sure to add them to the folder's ``__init__.py``:
