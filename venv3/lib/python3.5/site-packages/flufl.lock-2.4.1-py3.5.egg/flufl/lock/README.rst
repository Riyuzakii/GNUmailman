==================================
flufl.lock - An NFS-safe file lock
==================================

This package is called ``flufl.lock``.  It is an NFS-safe file-based lock with
timeouts for POSIX systems.


Requirements
============

``flufl.lock`` requires Python 2.6 or newer, and is compatible with Python 3.


Documentation
=============

A `simple guide`_ to using the library is available within this package, in
the form of doctests.


Project details
===============

 * Project home: https://gitlab.com/warsaw/flufl.lock
 * Report bugs at: https://gitlab.com/warsaw/flufl.lock/issues
 * Code hosting: git@gitlab.com:warsaw/flufl.lock.git
 * Documentation: http://flufllock.readthedocs.org/

You can install it with ``pip``::

    % pip install flufl.lock

You can grab the latest development copy of the code using git.  The master
repository is hosted on GitLab.  If you have git installed, you can grab
your own branch of the code like this::

    $ git clone git@gitlab.com:warsaw/flufl.lock.git

You may contact the author via barry@python.org.


Copyright
=========

Copyright (C) 2004-2015 Barry A. Warsaw

This file is part of flufl.lock.

flufl.lock is free software: you can redistribute it and/or modify it under
the terms of the GNU Lesser General Public License as published by the Free
Software Foundation, either version 3 of the License, or (at your option) any
later version.

flufl.lock is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
details.

You should have received a copy of the GNU Lesser General Public License along
with flufl.lock.  If not, see <http://www.gnu.org/licenses/>.


Table of Contents
=================

.. toctree::
    :glob:

    docs/using
    NEWS

.. _`simple guide`: docs/using.html
.. _`virtualenv`: http://www.virtualenv.org/en/latest/index.html
