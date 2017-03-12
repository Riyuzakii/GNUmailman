===================================
Postorius - web ui for GNU Mailman
===================================
.. image:: https://gitlab.com/mailman/postorius/badges/master/build.svg
    :target: https://gitlab.com/mailman/postorius/commits/master

.. image:: https://readthedocs.org/projects/postorius/badge
    :target: https://postorius.readthedocs.io

.. image:: http://img.shields.io/pypi/v/postorius.svg
    :target: https://pypi.python.org/pypi/postorius

.. image:: http://img.shields.io/pypi/dm/postorius.svg
    :target: https://pypi.python.org/pypi/postorius

Copyright (C) 1998-2016 by the Free Software Foundation, Inc.

The Postorius Django app provides a web user interface to
access GNU Mailman.

Postorius is free software: you can redistribute it and/or
modify it under the terms of the GNU Lesser General Public License as
published by the Free Software Foundation, version 3 of the License.

Postorius is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser
General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with mailman.client. If not, see <http://www.gnu.org/licenses/>.


Requirements
============

Postorius requires Python 2.7 or newer and mailmanclient,
the official Python bindings for GNU Mailman.
The minimum Django version is 1.8.
Postorius needs a running version of GNU Mailman version 3.


NEWS/Changelog
==============

News and the changelog can be found in the package documentation:

src/postorius/doc/news.rst


Installation
============

To install GNU Mailman follow the instructions in the documentation:
http://mailman.readthedocs.org/

A description how to run Postorius on Django's dev server or deploying it 
using Apache/mod_wsgi or Nginx/uwsig, can be found in the package documentation: 

src/postorius/doc/setup.rst
src/postorius/doc/deployment.rst


Acknowledgements
================

Many thanks go out to Anna Senarclens de Grancy and Benedict Stein for
developing the initial versions of this Django app during the Google Summer of
Code 2010 and 2011.
