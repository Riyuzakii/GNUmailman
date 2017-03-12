# Copyright (C) 2004-2015 Barry A. Warsaw
#
# This file is part of flufl.lock.
#
# flufl.lock is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# flufl.lock is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License
# for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with flufl.lock.  If not, see <http://www.gnu.org/licenses/>.

"""Test harness for doctests."""

from __future__ import absolute_import, print_function, unicode_literals

__metaclass__ = type
__all__ = [
    'additional_tests',
    ]


import os
import errno
import atexit
import doctest
import logging
import tempfile
import unittest

from datetime import timedelta
from io import StringIO

from pkg_resources import (
    resource_filename, resource_exists, resource_listdir, cleanup_resources)


COMMASPACE = ', '
DOT = '.'
DOCTEST_FLAGS = (
    doctest.ELLIPSIS |
    doctest.NORMALIZE_WHITESPACE |
    doctest.REPORT_NDIFF)

# For logging debugging.
log_stream = StringIO()


def stop():
    """Call into pdb.set_trace()"""
    # Do the import here so that you get the wacky special hacked pdb instead
    # of Python's normal pdb.
    import pdb
    pdb.set_trace()


def make_temporary_lockfile(testobj):
    """Make a temporary lock file for the tests."""
    def lockfile_creator():
        fd, testobj._lockfile = tempfile.mkstemp()
        os.close(fd)
        os.remove(testobj._lockfile)
        return testobj._lockfile
    return lockfile_creator


def setup(testobj):
    """Test setup."""
    # Truncate the log.
    log_stream.truncate()
    # Note that the module has a default built-in *clock slop* of 10 seconds
    # to handle differences in machine clocks. Since this test is happening on
    # the same machine, we can bump the slop down to a more reasonable number.
    from flufl.lock import _lockfile
    testobj._slop = _lockfile.CLOCK_SLOP
    _lockfile.CLOCK_SLOP = timedelta(seconds=0)
    # Make sure future statements in our doctests match the Python code.  When
    # run with 2to3, the future import gets removed and these names are not
    # defined.
    try:
        testobj.globs['absolute_import'] = absolute_import
        testobj.globs['print_function'] = print_function
        testobj.globs['unicode_literals'] = unicode_literals
    except NameError:
        pass
    testobj.globs['temporary_lockfile'] = make_temporary_lockfile(testobj)
    testobj.globs['log_stream'] = log_stream
    testobj.globs['stop'] = stop


def teardown(testobj):
    """Test teardown."""
    # Restore the original clock slop.
    from flufl.lock import _lockfile
    _lockfile.CLOCK_SLOP = testobj._slop
    try:
        os.remove(testobj._lockfile)
    except OSError as error:
        if error.errno != errno.ENOENT:
            raise
    except AttributeError:
        # lockfile_creator() was never called.
        pass


def additional_tests():
    "Run the doc tests (README.rst and docs/*, if any exist)"
    # Initialize logging for testing purposes.
    logging.basicConfig(stream=log_stream,
                        level=logging.DEBUG,
                        datefmt='%b %d %H:%M:%S %Y',
                        format='%(asctime)s (%(process)d) %(message)s',
                        )
    doctest_files = [
        os.path.abspath(resource_filename('flufl.lock', 'README.rst'))]
    if resource_exists('flufl.lock', 'docs'):
        for name in resource_listdir('flufl.lock', 'docs'):
            if name.endswith('.rst'):
                doctest_files.append(
                    os.path.abspath(
                        resource_filename('flufl.lock', 'docs/%s' % name)))
    kwargs = dict(module_relative=False,
                  optionflags=DOCTEST_FLAGS,
                  setUp=setup, tearDown=teardown,
                  )
    atexit.register(cleanup_resources)
    return unittest.TestSuite((
        doctest.DocFileSuite(*doctest_files, **kwargs)))
