# Copyright (C) 2007-2017 The Free Software Foundation, Inc.
#
# This file is part of GNU Mailman.
#
# GNU Mailman is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# GNU Mailman is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# GNU Mailman.  If not, see <http://www.gnu.org/licenses/>.

"""Harness for testing Mailman's documentation.

Note that doctest extraction does not currently work for zip file
distributions.  doctest discovery currently requires file system traversal.
"""

from __future__ import absolute_import, print_function, unicode_literals

from inspect import isfunction, ismethod


__metaclass__ = type
__all__ = [
    'setup',
    'teardown'
    ]


def stop():
    """Call into pdb.set_trace()"""
    # Do the import here so that you get the wacky special hacked pdb instead
    # of Python's normal pdb.
    import pdb
    pdb.set_trace()


def dump(results):
    if results is None:
        print(None)
        return
    for key in sorted(results):
        if key == 'entries':
            for i, entry in enumerate(results[key]):
                # entry is a dictionary.
                print('entry %d:' % i)
                for entry_key in sorted(entry):
                    print('    {0}: {1}'.format(entry_key, entry[entry_key]))
        else:
            print('{0}: {1}'.format(key, results[key]))


def setup(testobj):
    """Test setup."""
    # Make sure future statements in our doctests are the same as everywhere
    # else.
    testobj.globs['absolute_import'] = absolute_import
    testobj.globs['print_function'] = print_function
    testobj.globs['unicode_literals'] = unicode_literals
    # In general, I don't like adding convenience functions, since I think
    # doctests should do the imports themselves.  It makes for better
    # documentation that way.  However, a few are really useful, or help to
    # hide some icky test implementation details.
    testobj.globs['stop'] = stop
    testobj.globs['dump'] = dump
    # Add this so that cleanups can be automatically added by the doctest.
    testobj.globs['cleanups'] = []


def teardown(testobj):
    for cleanup in testobj.globs['cleanups']:
        if isfunction(cleanup) or ismethod(cleanup):
            cleanup()
        else:
            cleanup[0](*cleanup[1:])
