# Copyright (C) 2009-2017 The Free Software Foundation, Inc.
#
# This file is part of mailman.client
#
# mailman.client is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by the
# Free Software Foundation, version 3 of the License.
#
# mailman.client is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with mailman.client.  If not, see <http://www.gnu.org/licenses/>.

"""setup.py helper functions."""

from __future__ import absolute_import, print_function, unicode_literals

import os
import re
import sys
import codecs


__metaclass__ = type
__all__ = [
    'description',
    'find_doctests',
    'get_version',
    'long_description',
    'require_python',
    ]


DEFAULT_VERSION_RE = re.compile(r'(?P<version>\d+\.\d(?:\.\d+)?)')
NL = '\n'


def require_python(minimum):
    """Require at least a minimum Python version.

    The version number is expressed in terms of `sys.hexversion`.  E.g. to
    require a minimum of Python 2.6, use::

    >>> require_python(0x206000f0)

    :param minimum: Minimum Python version supported.
    :type minimum: integer
    """
    if sys.hexversion < minimum:
        hversion = hex(minimum)[2:]
        if len(hversion) % 2 != 0:
            hversion = '0' + hversion
        split = list(hversion)
        parts = []
        while split:
            parts.append(int(''.join((split.pop(0), split.pop(0))), 16))
        major, minor, micro, release = parts
        if release == 0xf0:
            print('Python {0}.{1}.{2} or better is required'.format(
                major, minor, micro))
        else:
            print('Python {0}.{1}.{2} ({3}) or better is required'.format(
                major, minor, micro, hex(release)[2:]))
        sys.exit(1)


def get_version(filename, pattern=None):
    """Extract the __version__ from a file without importing it.

    While you could get the __version__ by importing the module, the very act
    of importing can cause unintended consequences.  For example, Distribute's
    automatic 2to3 support will break.  Instead, this searches the file for a
    line that starts with __version__, and extract the version number by
    regular expression matching.

    By default, two or three dot-separated digits are recognized, but by
    passing a pattern parameter, you can recognize just about anything.  Use
    the `version` group name to specify the match group.

    :param filename: The name of the file to search.
    :type filename: string
    :param pattern: Optional alternative regular expression pattern to use.
    :type pattern: string
    :return: The version that was extracted.
    :rtype: string
    """
    if pattern is None:
        cre = DEFAULT_VERSION_RE
    else:
        cre = re.compile(pattern)
    with open(filename) as fp:
        for line in fp:
            if line.startswith('__version__'):
                mo = cre.search(line)
                assert mo, 'No valid __version__ string found'
                return mo.group('version')
    raise AssertionError('No __version__ assignment found')


def find_doctests(start='.', extension='.txt'):
    """Find separate-file doctests in the package.

    This is useful for Distribute's automatic 2to3 conversion support.  The
    `setup()` keyword argument `convert_2to3_doctests` requires file names,
    which may be difficult to track automatically as you add new doctests.

    :param start: Directory to start searching in (default is cwd)
    :type start: string
    :param extension: Doctest file extension (default is .txt)
    :type extension: string
    :return: The doctest files found.
    :rtype: list
    """
    doctests = []
    for dirpath, dirnames, filenames in os.walk(start):
        doctests.extend(os.path.join(dirpath, filename)
                        for filename in filenames
                        if filename.endswith(extension))
    return doctests


def long_description(*filenames):
    """Provide a long description."""
    res = []
    for value in filenames:
        base, ext = os.path.splitext(value)
        if ext in ('.txt', '.rst'):
            with codecs.open(value, 'r', encoding='utf-8') as fp:
                value = fp.read()
        res.append(value)
        if not value.endswith(NL):
            res.append('')
    return NL.join(res)


def description(filename):
    """Provide a short description."""
    with codecs.open(filename, 'r', encoding='utf-8') as fp:
        for line in fp:
            return line.strip()
