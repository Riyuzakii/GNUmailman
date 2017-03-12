"""Something which claims
X-Mailer: <SMTP32 vXXXXXX>

What the heck is this thing?  Here's a recent host:

% telnet 207.51.255.218 smtp
Trying 207.51.255.218...
Connected to 207.51.255.218.
Escape character is '^]'.
220 X1 NT-ESMTP Server 208.24.118.205 (IMail 6.00 45595-15)
"""

import re

from email.iterators import body_line_iterator
from flufl.bounce.interfaces import (
    IBounceDetector, NoFailures, NoTemporaryFailures)
from public import public
from zope.interface import implementer


ecre = re.compile('original message follows', re.IGNORECASE)
acre = re.compile(r'''
    (                                             # several different prefixes
    user\ mailbox[^:]*:                           # have been spotted in the
    |delivery\ failed[^:]*:                       # wild...
    |unknown\ user[^:]*:
    |undeliverable\ +to
    |delivery\ userid[^:]*:
    )
    \s*                                           # space separator
    (?P<addr>[^\s]*)                              # and finally, the address
    ''', re.IGNORECASE | re.VERBOSE)


@public
@implementer(IBounceDetector)
class SMTP32:
    """Something which claims

    X-Mailer: <SMTP32 vXXXXXX>
    """

    def process(self, msg):
        mailer = msg.get('x-mailer', '')
        if not mailer.startswith('<SMTP32 v'):
            return NoFailures
        addresses = set()
        for line in body_line_iterator(msg):
            if ecre.search(line):
                break
            mo = acre.search(line)
            if mo:
                addresses.add(mo.group('addr').encode('us-ascii'))
        return NoTemporaryFailures, addresses
