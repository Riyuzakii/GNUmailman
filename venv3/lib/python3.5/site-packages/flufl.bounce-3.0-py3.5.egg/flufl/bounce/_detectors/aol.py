"""Recognizes a class of messages from AOL that report only Screen Name."""

import re

from email.utils import parseaddr
from flufl.bounce.interfaces import (
    IBounceDetector, NoFailures, NoTemporaryFailures)
from public import public
from zope.interface import implementer


scre = re.compile(b'mail to the following recipients could not be delivered')


@public
@implementer(IBounceDetector)
class AOL:
    """Recognizes a class of messages from AOL that report only Screen Name."""

    def process(self, msg):
        if msg.get_content_type() != 'text/plain':
            return NoFailures
        if not parseaddr(msg.get('from', ''))[1].lower().endswith('@aol.com'):
            return NoFailures
        addresses = set()
        found = False
        for line in msg.get_payload(decode=True).splitlines():
            if scre.search(line):
                found = True
                continue
            if found:
                local = line.strip()
                if local:
                    if re.search(b'\\s', local):
                        break
                    if b'@' in local:
                        addresses.add(local)
                    else:
                        addresses.add(local + b'@aol.com')
        return NoTemporaryFailures, addresses
