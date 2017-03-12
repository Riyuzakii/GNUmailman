##############################################################################
#
# Copyright (c) 2003 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Message ID tests.
"""
import unittest

class PyMessageTests(unittest.TestCase):

    _TEST_REAOONLY = True

    def _getTargetClass(self):
        from zope.i18nmessageid.message import pyMessage
        return pyMessage

    def _makeOne(self, *args, **kw):
        return self._getTargetClass()(*args, **kw)

    def test_ctor_defaults(self):
        message = self._makeOne('testing')
        self.assertEqual(message, 'testing')
        self.assertEqual(message.domain, None)
        self.assertEqual(message.default, None)
        self.assertEqual(message.mapping, None)
        if self._TEST_REAOONLY:
            self.assertTrue(message._readonly)

    def test_ctor_explicit(self):
        mapping = {'key': 'value'}
        message = self._makeOne('testing', 'domain', 'default', mapping)
        self.assertEqual(message, 'testing')
        self.assertEqual(message.domain, 'domain')
        self.assertEqual(message.default, 'default')
        self.assertEqual(message.mapping, mapping)
        if self._TEST_REAOONLY:
            self.assertTrue(message._readonly)

    def test_ctor_copy(self):
        mapping = {'key': 'value'}
        source = self._makeOne('testing', 'domain', 'default', mapping)
        message = self._makeOne(source)
        self.assertEqual(message, 'testing')
        self.assertEqual(message.domain, 'domain')
        self.assertEqual(message.default, 'default')
        self.assertEqual(message.mapping, mapping)
        if self._TEST_REAOONLY:
            self.assertTrue(message._readonly)

    def test_ctor_copy_w_overrides(self):
        mapping = {'key': 'value'}
        source = self._makeOne('testing')
        message = self._makeOne(source, 'domain', 'default', mapping)
        self.assertEqual(message, 'testing')
        self.assertEqual(message.domain, 'domain')
        self.assertEqual(message.default, 'default')
        self.assertEqual(message.mapping, mapping)
        if self._TEST_REAOONLY:
            self.assertTrue(message._readonly)

    def test_domain_immutable(self):
        message = self._makeOne('testing')
        def _try():
            message.domain = 'domain'
        self.assertRaises(TypeError, _try)

    def test_default_immutable(self):
        message = self._makeOne('testing')
        def _try():
            message.default = 'default'
        self.assertRaises(TypeError, _try)

    def test_mapping_immutable(self):
        mapping = {'key': 'value'}
        message = self._makeOne('testing')
        def _try():
            message.mapping = mapping
        self.assertRaises(TypeError, _try)

    def test_unknown_immutable(self):
        message = self._makeOne('testing')
        def _try():
            message.unknown = 'unknown'
        # C version raises AttributeError, Python version TypeError
        self.assertRaises((TypeError, AttributeError), _try)

    def test___reduce__(self):
        mapping = {'key': 'value'}
        source = self._makeOne('testing')
        message = self._makeOne(source, 'domain', 'default', mapping)
        klass, state = message.__reduce__()
        self.assertTrue(klass is self._getTargetClass())
        self.assertEqual(state, ('testing', 'domain', 'default', mapping))


class MessageTests(PyMessageTests):

    _TEST_REAOONLY = False

    def _getTargetClass(self):
        from zope.i18nmessageid.message import Message
        return Message


class MessageFactoryTests(unittest.TestCase):

    def _getTargetClass(self):
        from zope.i18nmessageid.message import MessageFactory
        return MessageFactory

    def _makeOne(self, *args, **kw):
        return self._getTargetClass()(*args, **kw)

    def test___call___defaults(self):
        from zope.i18nmessageid.message import Message
        factory = self._makeOne('domain')
        message = factory('testing')
        self.assertTrue(isinstance(message, Message))
        self.assertEqual(message, 'testing')
        self.assertEqual(message.domain, 'domain')
        self.assertEqual(message.default, None)
        self.assertEqual(message.mapping, None)

    def test___call___explicit(self):
        from zope.i18nmessageid.message import Message
        mapping = {'key': 'value'}
        factory = self._makeOne('domain')
        message = factory('testing', 'default', mapping)
        self.assertTrue(isinstance(message, Message))
        self.assertEqual(message, 'testing')
        self.assertEqual(message.domain, 'domain')
        self.assertEqual(message.default, 'default')
        self.assertEqual(message.mapping, mapping)


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(PyMessageTests),
        unittest.makeSuite(MessageTests),
        unittest.makeSuite(MessageFactoryTests),
    ))
