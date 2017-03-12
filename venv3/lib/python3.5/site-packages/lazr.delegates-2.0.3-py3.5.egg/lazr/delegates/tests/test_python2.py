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

"""Test the legacy API, which only works in Python 2.

All of these tests are copied almost verbatim from the old README.rst.
"""


from __future__ import absolute_import, print_function, unicode_literals


# Don't enable the following or we can't test classic class failures.
#__metaclass__ = type
__all__ = [
    'TestLegacyAPI',
    ]


import sys
import unittest

from zope.interface import Attribute, Interface, implements, providedBy

from lazr.delegates import delegate_to
if sys.version_info[0] == 2:
    from lazr.delegates import delegates


class IFoo0(Interface):
    spoo = Attribute('attribute in IFoo0')

class IFoo(IFoo0):
    def bar():
        'some method'
    baz = Attribute('some attribute')

class BaseFoo0:
    spoo = 'some spoo'

class BaseFoo(BaseFoo0):
    def bar(self):
        return 'bar'
    baz = 'hi baz!'

class IOther(Interface):
    another = Attribute('another attribute')

class BaseOtherFoo(BaseFoo):
    another = 'yes, another'


# Python 2.6 doesn't have skips.
def skip_python3(cls):
    if sys.version_info[0] > 2:
        return None
    return cls


@skip_python3
class TestLegacyAPI(unittest.TestCase):
    def test_basic_usage(self):
        class SomeClass(object):
            delegates(IFoo)
            def __init__(self, context):
                self.context = context

        f = BaseFoo()
        s = SomeClass(f)
        self.assertEqual(s.bar(), 'bar')
        self.assertEqual(s.baz, 'hi baz!')
        self.assertEqual(s.spoo, 'some spoo')
        self.assertTrue(IFoo.providedBy(s))

    def test_keyword_context(self):
        class SomeOtherClass(object):
            delegates(IFoo, context='myfoo')
            def __init__(self, foo):
                self.myfoo = foo
            spoo = 'spoo from SomeOtherClass'

        f = BaseFoo()
        s = SomeOtherClass(f)
        self.assertEqual(s.bar(), 'bar')
        self.assertEqual(s.baz, 'hi baz!')
        self.assertEqual(s.spoo, 'spoo from SomeOtherClass')

        s.baz = 'fish'
        self.assertEqual(s.baz, 'fish')
        self.assertEqual(f.baz, 'fish')

    def test_classic_is_error(self):
        try:
            class SomeClassicClass:
                delegates(IFoo)
        except TypeError:
            pass
        else:
            self.fail('TypeError expected')

    def test_use_outside_class_is_error(self):
        self.assertRaises(TypeError, delegates, IFoo)

    def test_multiple_interfaces(self):
        class SomeOtherClass(object):
            delegates([IFoo, IOther])

        s = SomeOtherClass()
        s.context = BaseOtherFoo()
        self.assertEqual(s.another, 'yes, another')
        self.assertEqual(s.baz, 'hi baz!')
        self.assertEqual(s.spoo, 'some spoo')
        self.assertTrue(IFoo.providedBy(s))
        self.assertTrue(IOther.providedBy(s))

    def test_decorate_existing_object(self):
        class MoreFoo(BaseFoo, BaseOtherFoo):
            implements([IFoo, IOther])

        foo = MoreFoo()

        class WithExtraTeapot(object):
            delegates(providedBy(foo))
            teapot = 'i am a teapot'

        foo_with_teapot = WithExtraTeapot()
        foo_with_teapot.context = foo

        self.assertEqual(foo_with_teapot.baz, 'hi baz!')
        self.assertEqual(foo_with_teapot.another, 'yes, another')
        self.assertEqual(foo_with_teapot.teapot, 'i am a teapot')
        self.assertTrue(IFoo.providedBy(foo_with_teapot))
        self.assertTrue(IOther.providedBy(foo_with_teapot))


@skip_python3
class TestNewAPI(unittest.TestCase):
    """Test corner cases in Python 2.

    Most of the new API is tested in the doctest.  The implementation of the
    new API is different between Python 2 and Python 3, so test these corner
    cases.
    """
    def test_type_error(self):
        # Too many arguments to @delegate_to() raises a TypeError.
        try:
            @delegate_to(IFoo0, context='myfoo', other='bogus')
            class SomeClass(object):
                pass
        except TypeError:
            pass
        else:
            self.fail('TypeError expected')
