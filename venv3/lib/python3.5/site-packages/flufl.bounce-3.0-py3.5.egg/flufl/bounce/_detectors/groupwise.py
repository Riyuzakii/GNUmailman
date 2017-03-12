"""This appears to be the format for Novell GroupWise and NTMail

X-Mailer: Novell GroupWise Internet Agent 5.5.3.1
X-Mailer: NTMail v4.30.0012
X-Mailer: Internet Mail Service (5.5.2653.19)
"""

import re

from email.message import Message
from flufl.bounce.interfaces import (
    IBounceDetector, NoFailures, NoTemporaryFailures)
from io import BytesIO
from public import public
from zope.interface import implementer


acre = re.compile(b'<(?P<addr>[^>]*)>')


def find_textplain(msg):
    if msg.get_content_type() == 'text/plain':
        return msg
    if msg.is_multipart:
        for part in msg.get_payload():
            if not isinstance(part, Message):
                continue
            ret = find_textplain(part)
            if ret:
                return ret
    return None


@public
@implementer(IBounceDetector)
class GroupWise:
    """Parse Novell GroupWise and NTMail bounces."""

    def process(self, msg):
        """See `IBounceDetector`."""
        if msg.get_content_type() != 'multipart/mixed' or not msg['x-mailer']:
            return NoFailures
        if msg['x-mailer'][:3].lower() not in ('nov', 'ntm', 'int'):
            return NoFailures
        addresses = set()
        # Find the first text/plain part in the message.
        text_plain = find_textplain(msg)
        if text_plain is None:
            return NoFailures
        body = BytesIO(text_plain.get_payload(decode=True))
        for line in body:
            mo = acre.search(line)
            if mo:
                addresses.add(mo.group('addr'))
            elif b'@' in line:
                i = line.find(b' ')
                if i == 0:
                    continue
                if i < 0:
                    addresses.add(line)
                else:
                    addresses.add(line[:i])
        return NoTemporaryFailures, set(addresses)
