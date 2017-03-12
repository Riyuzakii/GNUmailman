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

"""Test the Passthrough implementation."""

import unittest

from lazr.delegates import Passthrough


class Base:
    foo = 'foo from Base'

    @classmethod
    def clsmethod(cls):
        return cls.__name__


class TestPassthrough(unittest.TestCase):
    def setUp(self):
        self.p = Passthrough('foo', 'mycontext')
        self.p2 = Passthrough('clsmethod', 'mycontext')

        self.base = Base()
        class Adapter:
            mycontext = self.base
        self.Adapter = Adapter
        self.adapter = Adapter()

    def test_get(self):
        self.assertEqual(self.p.__get__(self.adapter), 'foo from Base')
        self.assertTrue(self.p.__get__(None, self.Adapter) is self.p)
        self.assertEqual(self.p2.__get__(self.adapter)(), 'Base')

    def test_set(self):
        self.p.__set__(self.adapter, 'new value')
        self.assertEqual(self.base.foo, 'new value')

    def test_no_delete(self):
        self.assertRaises(NotImplementedError,
                          self.p.__delete__, self.adapter)

    def test_adaptation(self):
        # Passthrough's third argument (adaptation) is optional and, when
        # provided, should be a zope.interface.Interface subclass (although in
        # practice any callable will do) to which the instance is adapted
        # before getting/setting the delegated attribute.
        class HasNoFoo(object):
            _foo = 1
        no_foo = HasNoFoo()
        # ... but IHasFooAdapter uses HasNoFoo._foo to provide its own .foo,
        # so it works like an adapter for HasNoFoo into some interface that
        # provides a 'foo' attribute.
        class IHasFooAdapter(object):
            def __init__(self, inst):
                self.inst = inst
            @property
            def foo(self):
                return self.inst._foo
            @foo.setter
            def foo(self, value):
                self.inst._foo = value

        class Example(object):
            context = no_foo

        p = Passthrough('foo', 'context', adaptation=IHasFooAdapter)
        e = Example()

        self.assertEqual(p.__get__(e), 1)
        p.__set__(e, 2)
        self.assertEqual(p.__get__(e), 2)
