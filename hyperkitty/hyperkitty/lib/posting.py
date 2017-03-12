# -*- coding: utf-8 -*-
#
# Copyright (C) 1998-2012 by the Free Software Foundation, Inc.
#
# This file is part of HyperKitty.
#
# HyperKitty is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# HyperKitty is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# HyperKitty.  If not, see <http://www.gnu.org/licenses/>.
#
# Author: Aurelien Bompard <abompard@fedoraproject.org>
#

import re

from django.conf import settings
from django.core.exceptions import SuspiciousOperation
from django.core.mail import EmailMessage
from django_mailman3.lib.mailman import get_subscriptions
from mailmanclient import MailmanConnectionError

from hyperkitty.lib import mailman


class PostingFailed(Exception):
    pass


def get_sender(request, mlist):
    """Returns the appropriate sender email address"""
    if not request.user.is_authenticated():
        return None
    # Fallback to the logged-in user
    address = request.user.email
    # Try to get the email used to susbscribe to the list
    subscriptions = get_subscriptions(request.user)
    if mlist.list_id in subscriptions:
        address = subscriptions[mlist.list_id]
    return str(address)


def get_from(request, address):
    """Returns the appropriate 'From' header"""
    assert address is not None
    display_name = "%s %s" % (request.user.first_name, request.user.last_name)
    # Get the display_name from the Address in Mailman? And if not found,
    # from the User in Mailman?
    if display_name.strip():
        return '"%s" <%s>' % (display_name, address)
    else:
        return address


def post_to_list(request, mlist, subject, message, headers=None,
                 attachments=None):
    if not mlist:
        # Make sure the list exists to avoid posting to any email addess
        raise SuspiciousOperation("I don't know this mailing-list")
    if headers is None:
        headers = {}

    sender = headers.pop("From", get_sender(request, mlist))
    display_name = "%s %s" % (request.user.first_name, request.user.last_name)
    if display_name.strip():
        from_email = '"%s" <%s>' % (display_name, sender)
    else:
        from_email = sender
    # Unwrap and collapse spaces
    subject = re.sub(r'\n+', ' ', subject)
    subject = re.sub(r'\s+', ' ', subject)

    # Check that the user is subscribed
    try:
        subscribed_now = mailman.subscribe(
            mlist.name, request.user, sender, display_name)
    except MailmanConnectionError:
        raise PostingFailed("Can't connect to Mailman's REST server, "
                            "your message has not been sent.")
    # send the message
    headers["User-Agent"] = (
        "HyperKitty on %s" % request.build_absolute_uri("/"))
    msg = EmailMessage(
               subject=subject,
               body=message,
               from_email=from_email,
               to=[mlist.name],
               headers=headers,
               )
    # Attachments
    if attachments:
        if not isinstance(attachments, list):
            attachments = [attachments]
        for attach in attachments:
            msg.attach(attach.name, attach.read())
    # XXX: Inject into the incoming queue instead?
    if not settings.DEBUG:
        msg.send()  # Don't send mail in debug mode, just in case...
    return subscribed_now


def reply_subject(subject):
    if not subject.lower().startswith("re:"):
        return u"Re: %s" % subject
    else:
        return subject
