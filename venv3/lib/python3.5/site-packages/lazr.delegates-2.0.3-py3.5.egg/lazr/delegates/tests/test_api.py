# Copyright 2013-2015 Canonical Ltd.  All rights reserved.
#
# This file is part of lazr.delegates.
#
# lazr.delegates is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# lazr.delegates is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public
# License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with lazr.delegates.  If not, see <http://www.gnu.org/licenses/>.

"""Test the new API."""

import unittest

from lazr.delegates import delegate_to


class TestAPI(unittest.TestCase):
    """Test various corner cases in the API."""

    def test_no_interfaces(self):
        try:
            @delegate_to()
            class SomeClass(object):
                pass
        except TypeError:
            pass
        else:
            self.fail('TypeError expected')
