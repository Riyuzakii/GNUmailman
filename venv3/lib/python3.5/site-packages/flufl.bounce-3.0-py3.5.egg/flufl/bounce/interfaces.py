"""Interfaces."""

from public import public
from zope.interface import Interface


# Constants for improved readability in detector classes.  Use these like so:
#
# - to signal that no temporary or permanent failures were found:
#   `return NoFailures`
# - to signal that no temporary failures, but some permanent failures were
#   found:
#   `return NoTemporaryFailures, my_permanent_failures`
# - to signal that some temporary failures, but no permanent failures were
#   found:
#   `return my_temporary_failures, NoPermanentFailures`

NoTemporaryFailures = NoPermanentFailures = ()
NoFailures = (NoTemporaryFailures, NoPermanentFailures)

public(NoTemporaryFailures=NoTemporaryFailures)
public(NoPermanentFailures=NoPermanentFailures)
public(NoFailures=NoFailures)


@public
class IBounceDetector(Interface):
    """Detect a bounce in an email message."""

    def process(self, msg):
        """Scan an email message looking for bounce addresses.

        :param msg: An email message.
        :type msg: `Message`
        :return: A 2-tuple of the detected temporary and permanent bouncing
            addresses.  Both elements of the tuple are sets of string
            email addresses.  Not all detectors can tell the difference
            between temporary and permanent failures, in which case, the
            addresses will be considered to be permanently bouncing.
        :rtype: (set of strings, set of string)
        """
