"""Microsoft's `SMTPSVC' nears I kin tell."""

import re

from enum import Enum
from flufl.bounce.interfaces import (
    IBounceDetector, NoFailures, NoTemporaryFailures)
from io import BytesIO
from public import public
from zope.interface import implementer


scre = re.compile(br'transcript of session follows', re.IGNORECASE)


class ParseState(Enum):
    start = 0
    tag_seen = 1


@public
@implementer(IBounceDetector)
class Microsoft:
    """Microsoft's `SMTPSVC' nears I kin tell."""

    def process(self, msg):
        if msg.get_content_type() != 'multipart/mixed':
            return NoFailures
        # Find the first subpart, which has no MIME type.
        try:
            subpart = msg.get_payload(0)
        except IndexError:
            # The message *looked* like a multipart but wasn't.
            return NoFailures
        data = subpart.get_payload(decode=True)
        if isinstance(data, list):
            # The message is a multi-multipart, so not a matching bounce.
            return NoFailures
        body = BytesIO(data)
        state = ParseState.start
        addresses = set()
        for line in body:
            if state is ParseState.start:
                if scre.search(line):
                    state = ParseState.tag_seen
            elif state is ParseState.tag_seen:
                if '@' in line:
                    addresses.add(line.strip())
        return NoTemporaryFailures, set(addresses)
