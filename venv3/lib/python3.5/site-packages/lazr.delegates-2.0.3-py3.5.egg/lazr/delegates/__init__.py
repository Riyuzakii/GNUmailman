# Copyright 2008-2015 Canonical Ltd.  All rights reserved.
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

"""Decorator helpers that simplify class composition."""

__all__ = [
    'delegate_to',
    ]


import pkg_resources
__version__ = pkg_resources.resource_string(
    "lazr.delegates", "version.txt").strip()

from lazr.delegates._passthrough import Passthrough

# The class decorator syntax is different in Python 2 vs. Python 3.
import sys
if sys.version_info[0] == 2:
    from lazr.delegates._python2 import delegate_to
    # The legacy API is only compatible with Python 2.
    from lazr.delegates._delegates import delegates
    __all__.append('delegates')
else:
    from lazr.delegates._python3 import delegate_to
