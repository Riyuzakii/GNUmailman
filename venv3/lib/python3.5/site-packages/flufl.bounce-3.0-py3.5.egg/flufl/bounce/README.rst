=======================================
 flufl.bounce - Email bounce detectors
=======================================

The `flufl.bounce` library provides a set of heuristics and an API for
detecting the original bouncing email addresses from a bounce message.  Many
formats found in the wild are supported, as are VERP_ and RFC 3464 (DSN_).


Requirements
============

`flufl.bounce` requires Python 3.4 or newer.


Documentation
=============

A `simple guide`_ to using the library is available within this package.


Project details
===============

 * Project home: https://gitlab.com/warsaw/flufl.bounce
 * Report bugs at: https://gitlab.com/warsaw/flufl.bounce/issues
 * Code: https://gitlab.com/warsaw/flufl.bounce.git
 * Documentation: http://fluflbounce.readthedocs.io/

you can install it with ``pip``::

    % pip install flufl.bounce

You can grab the latest development copy of the code using git.  The master
repository is hosted on GitLab.  If you have git installed, you can grab
your own branch of the code like this::

    $ git clone https://gitlab.com/warsaw/flufl.bounce.git

You may contact the author via barry@python.org.


Copyright
=========

Copyright (C) 2004-2017 Barry A. Warsaw

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.


Table of Contents
=================

.. toctree::

    docs/using.rst
    NEWS.rst

.. _DSN: http://www.faqs.org/rfcs/rfc3464.html
.. _VERP: http://en.wikipedia.org/wiki/Variable_envelope_return_path
.. _`simple guide`: docs/using.html
.. _`virtualenv`: http://www.virtualenv.org/en/latest/index.html
.. _`zope.interface`: https://pypi.python.org/pypi/zope.interface
