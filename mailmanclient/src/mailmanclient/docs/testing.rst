========================
Developing MailmanClient
========================


Running Tests
=============

The test suite is run with the `tox`_ tool, which allows it to be run against
multiple versions of Python.  There are two modes to the test suite:

 * *Record mode* which is used to record the HTTP traffic against a live
   Mailman 3 REST server.
 * *Replay mode* which allows you to run the test suite off-line, without
   running the REST server.

Whenever you add tests for other parts of the REST API, you need to run the
suite once in record mode to generate the YAML file of HTTP requests and
responses.

Then you can run the test suite in replay mode as often as you want, and
Mailman 3 needn't even be installed on your system.

Since this branch ships with a recording file, you don't need to run in record
mode to start with.


Replay mode
===========

To run the test suite in replay mode (the default), just run the following::

    $ tox

This will attempt to run the test suite against Python 2.6, 2.7, 3.2, 3.3, and
3.4, or whatever combination of those that are available on your system.


Record mode
===========

Start by branching the Mailman 3 code base, then you should install it into a
virtual environment.  The easiest way to do this is with `tox`::

    $ tox --notest -r

Now, use the virtual environment that `tox` creates to create a template `var`
directory in the current directory::

    $ .tox/py34/bin/mailman info

Now you need to modify the ``var/etc/mailman.cfg`` configuration file, so that
it contains the following::

    [devmode]
    enabled: yes
    testing: yes
    recipient: you@yourdomain.com

    [mta]
    smtp_port: 9025
    lmtp_port: 9024
    incoming: mailman.testing.mta.FakeMTA

    [webservice]
    port: 9001

Now you can start Mailman 3::

    $ .tox/py34/bin/mailman start

Back in your ``mailmanclient`` branch, run the test suite in record mode::

    $ tox -e record

You should now have an updated recording file (``tape.yaml``).

If you find you need to re-run the test suite, you *must* first stop the
Mailman REST server, and then delete the ``mailman.db`` file, since it
contains state that will mess up the ``mailmanclient`` test suite::

    $ cd <mailman3-branch>
    $ .tox/py34/bin/mailman stop
    $ rm -f var/data/mailman.db
    $ .tox/py34/bin/mailman start

    $ cd <mailmanclient-branch>
    $ tox -e record

Once you're done recording the HTTP traffic, you can stop the Mailman 3 server
and you won't need it again.  It's a good idea to commit the ``tape.yaml``
changes for other users of your branch.


.. _`tox`: https://testrun.org/tox/latest/
