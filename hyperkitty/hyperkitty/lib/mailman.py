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

from __future__ import absolute_import, unicode_literals

from six.moves.urllib.error import HTTPError

from django_mailman3.lib.cache import cache
from django_mailman3.lib.mailman import get_mailman_client
from mailmanclient import MailmanConnectionError


import logging
logger = logging.getLogger(__name__)


class ModeratedListException(Exception):
    pass


def subscribe(list_address, user, email=None, display_name=None):
    if email is None:
        email = user.email
    if display_name is None:
        display_name = "%s %s" % (user.first_name, user.last_name)
    client = get_mailman_client()
    rest_list = client.get_list(list_address)
    subscription_policy = rest_list.settings.get(
        "subscription_policy", "moderate")
    # Add a flag to return that would tell the user they have been subscribed
    # to the current list.
    subscribed_now = False
    try:
        member = rest_list.get_member(email)
    except ValueError:
        # We don't want to bypass moderation, don't subscribe. Instead
        # raise an error so that it can be caught to show the user
        if subscription_policy in ("moderate", "confirm_then_moderate"):
            raise ModeratedListException(
                "This list is moderated, please subscribe"
                " to it before posting.")

        # not subscribed yet, subscribe the user without email delivery
        member = rest_list.subscribe(
            email, display_name, pre_verified=True, pre_confirmed=True)
        # The result can be a Member object or a dict if the subscription can't
        # be done directly, or if it's pending, or something else.
        # Broken API :-(
        if isinstance(member, dict):
            logger.info("Subscription for %s to %s is pending",
                        email, list_address)
            return subscribed_now
        member.preferences["delivery_status"] = "by_user"
        member.preferences.save()
        subscribed_now = True
        cache.delete("User:%s:subscriptions" % user.id, version=2)
        logger.info("Subscribing %s to %s on first post",
                    email, list_address)

    return subscribed_now


def get_new_lists_from_mailman():
    from hyperkitty.models import MailingList
    mmclient = get_mailman_client()
    page_num = 0
    while page_num < 10000:  # Just for security
        page_num += 1
        try:
            mlist_page = mmclient.get_list_page(count=10, page=page_num)
        except MailmanConnectionError:
            break
        except HTTPError:
            break  # can't update at this time
        for mm_list in mlist_page:
            if MailingList.objects.filter(name=mm_list.fqdn_listname).exists():
                continue
            if mm_list.settings["archive_policy"] == "never":
                continue  # Should we display those lists anyway?
            logger.info("Imported the new list %s from Mailman",
                        mm_list.fqdn_listname)
            mlist = MailingList.objects.create(name=mm_list.fqdn_listname)
            mlist.update_from_mailman()
        if not mlist_page.has_next:
            break


def sync_with_mailman(overwrite=False):
    from hyperkitty.models import MailingList, Sender
    for mlist in MailingList.objects.all():
        mlist.update_from_mailman()
    # Now sync Sender.mailman_id with Mailman's User.user_id
    # There can be thousands of senders, break into smaller chuncks to avoid
    # hogging up the memory
    buffer_size = 1000
    query = Sender.objects.all()
    if not overwrite:
        query = query.filter(mailman_id__isnull=True)
    prev_count = query.count()
    lower_bound = 0
    upper_bound = buffer_size
    while True:
        try:
            for sender in query.all()[lower_bound:upper_bound]:
                sender.set_mailman_id()
        except MailmanConnectionError:
            break  # Can't refresh at this time
        count = query.count()
        if count == 0:
            break  # all done
        if count == prev_count:
            # no improvement...
            if count < upper_bound:
                break  # ...and all users checked
            else:
                # there may be some more left
                lower_bound = upper_bound
                upper_bound += buffer_size
        prev_count = count
        logger.info("%d emails left to refresh, checked %d",
                    count, lower_bound)
