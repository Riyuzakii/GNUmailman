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

from __future__ import absolute_import, print_function, unicode_literals


__metaclass__ = type
__all__ = [
    'Passthrough',
    ]


class Passthrough:
    """Call the delegated class for the decorator class.

    If the ``adaptation`` argument is not None, it should be a callable. It
    will be called with the context, and should return an object that will
    have the delegated attribute. The ``adaptation`` argument is expected to
    be used with an interface, to adapt the context.
    """
    def __init__(self, name, contextvar, adaptation=None):
        self.name = name
        self.contextvar = contextvar
        self.adaptation = adaptation

    def __get__(self, inst, cls=None):
        if inst is None:
            return self
        else:
            context = getattr(inst, self.contextvar)
            if self.adaptation is not None:
                context = self.adaptation(context)
            return getattr(context, self.name)

    def __set__(self, inst, value):
        context = getattr(inst, self.contextvar)
        if self.adaptation is not None:
            context = self.adaptation(context)
        setattr(context, self.name, value)

    def __delete__(self, inst):
        raise NotImplementedError
