=====================
NEWS for flufl.bounce
=====================

3.0 (2017-02-17)
================
 * Drop Python 2 support.
 * Switch to the Apache Software License v2.
 * Fixed a bug where the Groupwise detector looks at more messages than it
   should.  (LP: #1548983)
 * Update documentation links to point to fluflbounce.readthedocs.io.
 * Switch to the nose2 test runner.


2.3 (2014-08-18)
================
 * Added recognition for a kundenserver.de warning to simplewarning.py.
   (LP: #1263247)
 * Stop using the deprecated `distribute` package in favor of the now-merged
   `setuptools` package.
 * Stop using the deprecated `flufl.enum` package in favor of the enum34
   package (for Python 2) or built-in enum package (for Python 3).


2.2.1 (2013-06-21)
==================
 * Prune some artifacts unintentionally leaked into the release tarball.


2.2 (2013-06-20)
================
 * Added recognition for a bogus Dovecot over-quota rejection sent as an MDN
   rather than a DSN.  (LP: #693134)
 * Tweaked a simplematch regexp that didn't always work.  (LP: #1079254)
 * Added recognition for bounces from mail.ru.  Thanks to Andrey
   Rahmatullin.  (LP: #1079249)
 * Fixed UnicodeDecodeError in qmail.py with non-ascii message.  Thanks
   to Theo Spears.  (LP: #1074592)
 * Added recognition for another Yahoo bounce format.  Thanks to Mark
   Sapiro. (LP: #1157961)
 * Fix documentation bug.  (LP: #1026403)
 * Document the zope.interface requirement. (LP: #1021383)


2.1.1 (2012-04-19)
==================
 * Add classifiers to setup.py and make the long description more compatible
   with the Cheeseshop.
 * Other changes to make the Cheeseshop page look nicer.  (LP: #680136)
 * setup_helper.py version 2.1.


2.1 (2012-01-19)
================
 * Fix TypeError thrown when None is returned by Caiwireless.  Given by Paul
   Egan. (LP: #917720)


2.0 (2012-01-04)
================
 * Port to Python 3 without the use of `2to3`.  Switch to class decorator
   syntax for declaring that a class implements an interface.  The functional
   form doesn't work for Python 3.
 * All returned addresses are bytes objects in Python 3 and 8-bit strings in
   Python 2 (no change there).
 * Add an additional in-the-wild example of a qmail bounce.  Given by Mark
   Sapiro.
 * Export `all_failures` in the package's namespace.
 * Fix `python setup.py test` so that it runs all the tests exactly once.
   There seems to be no portable way to support that and unittest discovery
   (i.e. `python -m unittest discover`) and since the latter requires
   virtualenv, just disable it for now.  (LP: #911399)
 * Add full copy of LGPLv3 to source tarball. (LP: #871961)


1.0.2 (2011-10-10)
==================
 * Fixed MANIFEST.in to exclude the .egg.


1.0.1 (2011-10-07)
==================
 * Fixed licenses.  All code is LGPLv3.


1.0 (2011-08-22)
================
 * Initial release.


0.91 (2011-07-15)
=================
 * Provide a nicer interface for detector modules.  Instead of using the magic
   empty tuple returns, provide three convenience constants in the interfaces
   module: NoFailures, NoTemporaryFailures, and NoPermanentFailures.
 * Add logging support.  Applications can initialize the `flufl.bounce`
   logger.  The test suite does its own logging.basicConfig(), which can be
   influenced by the environment variable $FLUFL_LOGGING.  See
   flufl/bounce/tests/helpers.py for details.


0.90 (2011-07-02)
=================
 * Initial refactoring from Mailman 3.
