# Copyright (C) 2015-2017 The Free Software Foundation, Inc.
#
# This file is part of mailman.client.
#
# mailman.client is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by the
# Free Software Foundation, version 3 of the License.
#
# mailman.client is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public
# License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with mailman.client.  If not, see <http://www.gnu.org/licenses/>.

"""Test domain corner cases."""

from __future__ import absolute_import, print_function, unicode_literals

import unittest

from mailmanclient import Client
from six.moves.urllib_error import HTTPError


__metaclass__ = type
__all__ = [
    'TestDomains',
    ]


class TestDomains(unittest.TestCase):
    def setUp(self):
        self._client = Client(
            'http://localhost:9001/3.0', 'restadmin', 'restpass')

    def test_no_domain(self):
        # Trying to get a non-existent domain returns a 404.
        #
        # We can't use `with self.assertRaises()` until we drop Python 2.6
        try:
            self._client.get_domain('example.org')
        except HTTPError as error:
            self.assertEqual(error.code, 404)
        else:
            raise AssertionError('Expected HTTPError 404')
