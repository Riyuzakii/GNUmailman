##############################################################################
#
# Copyright (c) 2004 Zope Foundation and Contributors.
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
"""I18n Messages and factories.
"""
__docformat__ = "reStructuredText"

try:
    unicode
except NameError: #pragma NO COVER Python3
    unicode = str


class Message(unicode):
    """Message (Python implementation)

    This is a string used as a message.  It has a domain attribute that is
    its source domain, and a default attribute that is its default text to
    display when there is no translation.  domain may be None meaning there is
    no translation domain.  default may also be None, in which case the
    message id itself implicitly serves as the default text.
    """

    __slots__ = ('domain', 'default', 'mapping', '_readonly')

    def __new__(cls, ustr, domain=None, default=None, mapping=None):
        self = unicode.__new__(cls, ustr)
        if isinstance(ustr, self.__class__):
            domain = ustr.domain and ustr.domain[:] or domain
            default = ustr.default and ustr.default[:] or default
            mapping = ustr.mapping and ustr.mapping.copy() or mapping
            ustr = unicode(ustr)
        self.domain = domain
        if default is None:
            # MessageID does: self.default = ustr
            self.default = default
        else:
            self.default = unicode(default)
        self.mapping = mapping
        self._readonly = True
        return self

    def __setattr__(self, key, value):
        """Message is immutable

        It cannot be changed once the message id is created.
        """
        if getattr(self, '_readonly', False):
            raise TypeError('readonly attribute')
        else:
            return unicode.__setattr__(self, key, value)

    def __getstate__(self):
        return unicode(self), self.domain, self.default, self.mapping

    def __reduce__(self):
        return self.__class__, self.__getstate__()

# Name the fallback Python implementation to make it easier to test.
pyMessage = Message

try:
    from _zope_i18nmessageid_message import Message
except ImportError: # pragma: no cover
    pass

class MessageFactory(object):
    """Factory for creating i18n messages."""

    def __init__(self, domain):
        self._domain = domain

    def __call__(self, ustr, default=None, mapping=None):
        return Message(ustr, self._domain, default, mapping)
