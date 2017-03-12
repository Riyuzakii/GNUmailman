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

from __future__ import absolute_import, print_function, unicode_literals

from email.message import Message

from django.contrib.auth.models import User
from hyperkitty.lib.incoming import add_to_list
from hyperkitty.models import Email
from hyperkitty.tests.utils import TestCase


def _create_email(num, reply_to=None):
    msg = Message()
    msg["From"] = "sender%d@example.com" % num
    msg["Message-ID"] = "<msg%d>" % num
    msg.set_payload("message %d" % num)
    if reply_to is not None:
        msg["In-Reply-To"] = "<msg%d>" % reply_to
    return add_to_list("example-list", msg)


class ProfileTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create(username="dummy")

    def test_votes_in_list(self):
        # Count the number of votes in a list
        _create_email(1)
        _create_email(2, reply_to=1)
        _create_email(3, reply_to=2)
        msg1 = Email.objects.get(message_id="msg1")
        msg1.vote(1, self.user)
        msg2 = Email.objects.get(message_id="msg2")
        msg2.vote(-1, self.user)
        self.assertEqual(
            (1, 1),
            self.user.hyperkitty_profile.get_votes_in_list("example-list"))
