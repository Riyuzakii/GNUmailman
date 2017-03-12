"""sina.com bounces"""

import re

from email.iterators import body_line_iterator
from flufl.bounce.interfaces import (
    IBounceDetector, NoFailures, NoTemporaryFailures)
from public import public
from zope.interface import implementer


acre = re.compile(r'<(?P<addr>[^>]*)>')


@public
@implementer(IBounceDetector)
class Sina:
    """sina.com bounces"""

    def process(self, msg):
        """See `IBounceDetector`."""
        if msg.get('from', '').lower() != 'mailer-daemon@sina.com':
            return NoFailures
        if not msg.is_multipart():
            return NoFailures
        # The interesting bits are in the first text/plain multipart.
        part = None
        try:
            part = msg.get_payload(0)
        except IndexError:
            pass
        if not part:
            return NoFailures
        addresses = set()
        for line in body_line_iterator(part):
            mo = acre.match(line)
            if mo:
                addresses.add(mo.group('addr').encode('us-ascii'))
        return NoTemporaryFailures, addresses
