# -*- coding: utf-8 -*-
#
# Copyright (C) 2014-2015 by the Free Software Foundation, Inc.
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

from __future__ import absolute_import, unicode_literals, print_function


from six.moves.urllib.error import HTTPError

from django.db import models
from django_mailman3.lib.mailman import get_mailman_client
from mailmanclient import MailmanConnectionError


import logging
logger = logging.getLogger(__name__)


class Sender(models.Model):
    address = models.EmailField(max_length=255, primary_key=True)
    mailman_id = models.CharField(max_length=255, null=True, db_index=True)

    @property
    def name(self):
        try:
            return self.emails.order_by("-date").values_list(
                "sender_name", flat=True)[0]
        except IndexError:
            return "(no name)"

    @property
    def names(self):
        return self.emails.order_by("-date").values_list(
            "sender_name", flat=True)

    def set_mailman_id(self):
        try:
            client = get_mailman_client()
            mm_user = client.get_user(self.address)
        except HTTPError as e:
            if e.code == 404:
                return  # User not found in Mailman
            # normalize all possible error types
            raise MailmanConnectionError(e)
        except ValueError as e:
            # This smells like a badly formatted email address (saw it in the
            # wild)
            logger.warning(
                "Invalid response when getting user %s from Mailman",
                self.address)
            return  # Ignore it
        self.mailman_id = mm_user.user_id
        self.save()
        # # Go further and associate the user's other addresses?
        # Sender.objects.filter(address__in=mm_user.addresses
        #     ).update(mailman_id=mm_user.user_id)
