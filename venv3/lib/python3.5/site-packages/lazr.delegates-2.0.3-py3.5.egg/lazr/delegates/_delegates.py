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

from __future__ import absolute_import, print_function, unicode_literals


__metaclass__ = type
__all__ = [
    'delegates',
    ]


import sys
from types import ClassType

from zope.interface.advice import addClassAdvisor
from zope.interface import classImplements
from zope.interface.interfaces import IInterface

from lazr.delegates._passthrough import Passthrough


def delegates(interface_spec, context='context'):
    """Make an adapter into a decorator.

    Use like:

        class RosettaProject:
            implements(IRosettaProject)
            delegates(IProject)

            def __init__(self, context):
                self.context = context

            def methodFromRosettaProject(self):
                return self.context.methodFromIProject()

    If you want to use a different name than "context" then you can explicitly
    say so:

        class RosettaProject:
            implements(IRosettaProject)
            delegates(IProject, context='project')

            def __init__(self, project):
                self.project = project

            def methodFromRosettaProject(self):
                return self.project.methodFromIProject()

    The adapter class will implement the interface it is decorating.

    The minimal decorator looks like this:

    class RosettaProject:
        delegates(IProject)

        def __init__(self, context):
            self.context = context

    """
    # pylint: disable-msg=W0212
    frame = sys._getframe(1)
    locals = frame.f_locals

    # Try to make sure we were called from a class def
    if (locals is frame.f_globals) or ('__module__' not in locals):
        raise TypeError(
            "delegates() can be used only from a class definition.")

    locals['__delegates_advice_data__'] = interface_spec, context
    addClassAdvisor(_delegates_advice, depth=2)


def _delegates_advice(cls):
    """Add a Passthrough class for each missing interface attribute.

    This function connects the decorator class to the delegate class.
    Only new-style classes are supported.
    """
    interface_spec, contextvar = cls.__dict__['__delegates_advice_data__']
    del cls.__delegates_advice_data__
    if isinstance(cls, ClassType):
        raise TypeError(
            'Cannot use delegates() on a classic class: %s.' % cls)
    if IInterface.providedBy(interface_spec):
        interfaces = [interface_spec]
    else:
        interfaces = interface_spec
    not_found = object()
    for interface in interfaces:
        classImplements(cls, interface)
        for name in interface:
            if getattr(cls, name, not_found) is not_found:
                setattr(cls, name, Passthrough(name, contextvar))
    return cls
