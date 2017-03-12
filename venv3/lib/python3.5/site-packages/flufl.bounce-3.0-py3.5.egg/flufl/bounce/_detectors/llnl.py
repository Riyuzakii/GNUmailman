"""LLNL's custom Sendmail bounce message."""

import re

from email.iterators import body_line_iterator
from flufl.bounce.interfaces import (
    IBounceDetector, NoFailures, NoTemporaryFailures)
from public import public
from zope.interface import implementer


acre = re.compile(r',\s*(?P<addr>\S+@[^,]+),', re.IGNORECASE)


@public
@implementer(IBounceDetector)
class LLNL:
    """LLNL's custom Sendmail bounce message."""

    def process(self, msg):
        """See `IBounceDetector`."""

        for line in body_line_iterator(msg):
            mo = acre.search(line)
            if mo:
                address = mo.group('addr').encode('us-ascii')
                return NoTemporaryFailures, set([address])
        return NoFailures
