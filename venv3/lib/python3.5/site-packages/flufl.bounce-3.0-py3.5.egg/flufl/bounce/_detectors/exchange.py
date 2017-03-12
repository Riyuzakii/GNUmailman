"""Recognizes (some) Microsoft Exchange formats."""

import re

from email.iterators import body_line_iterator
from flufl.bounce.interfaces import (
    IBounceDetector, NoFailures, NoTemporaryFailures)
from public import public
from zope.interface import implementer


scre = re.compile('did not reach the following recipient')
ecre = re.compile('MSEXCH:')
a1cre = re.compile('SMTP=(?P<addr>[^;]+); on ')
a2cre = re.compile('(?P<addr>[^ ]+) on ')


@public
@implementer(IBounceDetector)
class Exchange:
    """Recognizes (some) Microsoft Exchange formats."""

    def process(self, msg):
        """See `IBounceDetector`."""
        addresses = set()
        it = body_line_iterator(msg)
        # Find the start line.
        for line in it:
            if scre.search(line):
                break
        else:
            return NoFailures
        # Search each line until we hit the end line.
        for line in it:
            if ecre.search(line):
                break
            mo = a1cre.search(line)
            if not mo:
                mo = a2cre.search(line)
            if mo:
                # For Python 3 compatibility, the API requires bytes
                address = mo.group('addr').encode('us-ascii')
                addresses.add(address)
        return NoTemporaryFailures, set(addresses)
