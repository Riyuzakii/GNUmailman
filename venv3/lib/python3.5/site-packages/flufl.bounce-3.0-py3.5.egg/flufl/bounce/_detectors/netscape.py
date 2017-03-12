"""Netscape Messaging Server bounce formats.

I've seen at least one NMS server version 3.6 (envy.gmp.usyd.edu.au) bounce
messages of this format.  Bounces come in DSN MIME format, but don't include
any -Recipient: headers.  Gotta just parse the text :(

NMS 4.1 (dfw-smtpin1.email.verio.net) seems even worse, but we'll try to
decipher the format here too.

"""

import re

from flufl.bounce.interfaces import (
    IBounceDetector, NoFailures, NoTemporaryFailures)
from io import BytesIO
from public import public
from zope.interface import implementer


pcre = re.compile(
    b'This Message was undeliverable due to the following reason:',
    re.IGNORECASE)

acre = re.compile(
    b'(?P<reply>please reply to)?.*<(?P<addr>[^>]*)>',
    re.IGNORECASE)


def flatten(msg, leaves):
    # Give us all the leaf (non-multipart) subparts.
    if msg.is_multipart():
        for part in msg.get_payload():
            flatten(part, leaves)
    else:
        leaves.append(msg)


@public
@implementer(IBounceDetector)
class Netscape:
    """Netscape Messaging Server bounce formats."""

    def process(self, msg):
        """See `IBounceDetector`."""

        # Sigh.  Some NMS 3.6's show
        #     multipart/report; report-type=delivery-status
        # and some show
        #     multipart/mixed;
        if not msg.is_multipart():
            return NoFailures
        # We're looking for a text/plain subpart occuring before a
        # message/delivery-status subpart.
        plainmsg = None
        leaves = []
        flatten(msg, leaves)
        for i, subpart in zip(range(len(leaves)-1), leaves):
            if subpart.get_content_type() == 'text/plain':
                plainmsg = subpart
                break
        if not plainmsg:
            return NoFailures
        # Total guesswork, based on captured examples...
        body = BytesIO(plainmsg.get_payload(decode=True))
        addresses = set()
        for line in body:
            mo = pcre.search(line)
            if mo:
                # We found a bounce section, but I have no idea what the
                # official format inside here is.  :( We'll just search for
                # <addr> strings.
                for line in body:
                    mo = acre.search(line)
                    if mo and not mo.group('reply'):
                        addresses.add(mo.group('addr'))
        return NoTemporaryFailures, addresses
