# Copyright 2014-2015 Canonical Ltd.  All rights reserved.
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

"""Class decorator definition for Python 2."""

from zope.interface import classImplements

from lazr.delegates._passthrough import Passthrough


def delegate_to(*interfaces, **kws):
    context = kws.pop('context', 'context')
    if len(kws) > 0:
        raise TypeError('Too many arguments')
    if len(interfaces) == 0:
        raise TypeError('At least one interface is required')
    def _decorator(cls):
        missing = object()
        for interface in interfaces:
            classImplements(cls, interface)
            for name in interface:
                if getattr(cls, name, missing) is missing:
                    setattr(cls, name, Passthrough(name, context))
        return cls
    return _decorator
