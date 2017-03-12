"""Yahoo! has its own weird format for bounces."""

import re

from email.iterators import body_line_iterator
from email.utils import parseaddr
from enum import Enum
from flufl.bounce.interfaces import (
    IBounceDetector, NoFailures, NoTemporaryFailures)
from public import public
from zope.interface import implementer


tcre = (re.compile(r'message\s+from\s+yahoo\.\S+', re.IGNORECASE),
        re.compile(r'Sorry, we were unable to deliver your message to '
                   r'the following address(\(es\))?\.',
                   re.IGNORECASE),
        )
acre = re.compile(r'<(?P<addr>[^>]*)>:')
ecre = (re.compile(r'--- Original message follows'),
        re.compile(r'--- Below this line is a copy of the message'),
        )


class _ParseState(Enum):
    start = 0
    tag_seen = 1
    all_done = 2


@public
@implementer(IBounceDetector)
class Yahoo:
    """Yahoo! bounce detection."""

    def process(self, msg):
        """See `IBounceDetector`."""
        # Yahoo! bounces seem to have a known subject value and something
        # called an x-uidl: header, the value of which seems unimportant.
        sender = parseaddr(msg.get('from', '').lower())[1] or ''
        if not sender.startswith('mailer-daemon@yahoo'):
            return NoFailures
        addresses = set()
        state = _ParseState.start
        for line in body_line_iterator(msg):
            line = line.strip()
            if state is _ParseState.start:
                for cre in tcre:
                    if cre.match(line):
                        state = _ParseState.tag_seen
                        break
            elif state is _ParseState.tag_seen:
                mo = acre.match(line)
                if mo:
                    addresses.add(mo.group('addr').encode('us-ascii'))
                    continue
                for cre in ecre:
                    mo = cre.match(line)
                    if mo:
                        # We're at the end of the error response.
                        state = _ParseState.all_done
                        break
                if state is _ParseState.all_done:
                    break
        return NoTemporaryFailures, addresses
