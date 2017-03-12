..
    This file is part of mailmanclient.

    mailmanclient is free software: you can redistribute it and/or modify it
    under the terms of the GNU Lesser General Public License as published by
    the Free Software Foundation, version 3 of the License.

    mailmanclient is distributed in the hope that it will be useful, but
    WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
    or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public
    License for more details.

    You should have received a copy of the GNU Lesser General Public License
    along with mailman.client.  If not, see <http://www.gnu.org/licenses/>.


==============
Mailman Client
==============

The ``mailmanclient`` library provides official Python bindings for the GNU
Mailman 3 REST API.

Note that the test suite current requires that a Mailman 3 server be running.
It should be running using a dummy or throw-away database, as this will make
changes to the running system.  TBD: mock the real Mailman engine so that it
is not necessary in order to run these tests.


Requirements
============

``mailmanclient`` requires Python 2.6 or newer.


Project details
===============

You may download the latest version of the package from the Python
`Cheese Shop`_ or from GitLab_.

You can also install it via ``pip``::

    $ sudo pip install mailmanclient

See the GitLab project page for access to the development branch, issues, etc.


Acknowledgements
================

Many thanks to Florian Fuchs for his contribution of an initial REST client.


.. toctree::
   :maxdepth: 1
   :caption: Table of Contents

   using.rst
   apiref.rst
   testing.rst
   src/mailmanclient/NEWS.rst


.. _`Cheese Shop`: https://pypi.python.org/pypi/mailmanclient
.. _GitLab: https://gitlab.com/mailman/mailmanclient
