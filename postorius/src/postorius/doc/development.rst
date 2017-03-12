===========
Development
===========

This is a short guide to help you get started with Postorius development.


Development Workflow
====================

The source code is hosted on GitLab_, which means that we are using
Git for version control.

.. _GitLab: https://gitlab.com/mailman/postorius

Changes are not made directly in the project's master branch, but in
feature-related personal branches, which get reviewed and then merged into
the master branch. There is a contribution guide here_, that mentions the basics
about contributing to any mailman project.

.. _here: http://wiki.list.org/DEV/HowToContributeGit

An ideal workflow would be like this:

1. File a bug to suggest a new feature or report a bug (or just pick one of
   the existing bugs).
2. Create a new branch with your code changes.
3. Make a "merge request" to get your code reviewed and merged.


Installing and running the tests
================================

After checkout you can run the tests using ``tox``:

::

    $ tox

By default this will test against a couple of different environments.
If you want to only run the tests in a specific environment or a single
module, you can specify this using the ``-e`` option and/or a double
dash:

::

    # List all currently configured envs:
    $ tox -l
    py27-django18
    py27-django19

    # Test Django 1.8 on Python2.7 only:
    $ tox -e py27-django18

    # Run only tests in ``test_address_activation``:
    $ tox -- postorius.tests.test_address_activation

    # You get the idea...
    $ tox -e py27-django18 -- postorius.tests.test_address_activation


All test modules reside in the ``postorius/src/postorius/tests``
directory. Please have a look at the existing examples.


Mocking calls to Mailman's REST API
===================================

A lot of Postorius' code involves calls to Mailman's REST API (through
the mailman.client library). Running these tests against a real instance
of Mailman would be bad practice and slow, so ``vcrpy`` *cassettes* are
used instead (see the `vcrpy Documentation`_ for details). These files
contain pre-recorded HTTP responses.

.. _`vcrpy Documentation`: https://github.com/kevin1024/vcrpy

If you write new tests, it's advisable to add a separate fixture file
for each test case, so the cached responses don't interfere with other
tests. The cassette files are stored in the
``tests/fixtures/vcr_cassettes`` directory. Check out the existing test
cases for examples.

In order to record new API responses for your test case, you need  to
first start the mailman core, with the API server listening on port
9001. You can use the ``example_project/mailman.cfg`` file from the
Postorius source.

.. note::
    Make sure, you use a fresh mailman.db file.

Once the core is running, you can record the new cassette file defined
in your test case by running tox with the `record` test env:

::

    # This will only record the cassette files defined in my_new_test_module:
    $ tox -e record -- postorius.tests.my_new_test_module

    # This will re-record all cassette files:
    $ tox -e record


View Auth
=========

Three of Django's default User roles are relvant for Postorius:

- Superuser: Can do everything.
- AnonymousUser: Can view list index and info pages.
- Authenticated users: Can view list index and info pages. Can (un)subscribe
  from lists.

Apart from these default roles, there are two others relevant in Postorius:

- List owners: Can change list settings, moderate messages and delete their
  lists.
- List moderators: Can moderate messages.

There are a number of decorators to protect views from unauthorized users.

- ``@user_passes_test(lambda u: u.is_superuser)`` (redirects to login form)
- ``@login_required`` (redirects to login form)
- ``@list_owner_required`` (returns 403 if logged-in user isn't the
  list's owner)
- ``@list_moderator_required`` (returns 403 if logged-in user isn't the
  list's moderator)


Accessing the Mailman API
=========================

Postorius uses mailmanclient to connect to Mailman's REST API. In order to
directly use the client, ``cd`` to the ``example_project`` folder and execute
``python manage.py mmclient``. This will open a python shell (IPython, if
that's available) and provide you with a client object connected to to your
local Mailman API server (it uses the credentials from your settings.py).

A quick example:

::

    $ python manage.py mmclient

    >>> client
    <Client (user:pwd) http://localhost:8001/3.0/>

    >>> print(client.system['mailman_version'])
    GNU Mailman 3.0.0b2+ (Here Again)

    >>> mailman_dev = client.get_list('mailman-developers@python.org')
    >>> print(mailman_dev.settings)
    {u'description': u'Mailman development',
     u'default_nonmember_action': u'hold', ...}

For detailed information how to use mailmanclient, check out its documentation_.

.. _documentation: http://docs.mailman3.org/projects/mailmanclient/en/latest/using.html
