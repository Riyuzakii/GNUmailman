# -*- coding: utf-8 -*-
#
# Copyright (C) 2013-2016 by the Free Software Foundation, Inc.
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
from hyperkitty.models import Email, Thread
from hyperkitty.tests.utils import TestCase


def _create_email(num, reply_to=None):
    msg = Message()
    msg["From"] = "sender%d@example.com" % num
    msg["Message-ID"] = "<msg%d>" % num
    msg.set_payload("message %d" % num)
    if reply_to is not None:
        msg["In-Reply-To"] = "<msg%d>" % reply_to
    return add_to_list("example-list", msg)


class VoteTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create(username="dummy")

    def test_msg_1(self):
        # First message in thread is voted for
        _create_email(1)
        _create_email(2, reply_to=1)
        _create_email(3, reply_to=2)
        msg1 = Email.objects.get(message_id="msg1")
        msg1.vote(1, self.user)
        self.assertEqual(Thread.objects.count(), 1)
        thread = Thread.objects.all()[0]
        votes = thread.get_votes()
        self.assertEqual(votes["likes"], 1)
        self.assertEqual(votes["dislikes"], 0)
        self.assertEqual(votes["status"], "like")

    def test_msg2(self):
        # Second message in thread is voted against
        _create_email(1)
        _create_email(2, reply_to=1)
        _create_email(3, reply_to=2)
        msg2 = Email.objects.get(message_id="msg2")
        msg2.vote(-1, self.user)
        self.assertEqual(Thread.objects.count(), 1)
        thread = Thread.objects.all()[0]
        votes = thread.get_votes()
        self.assertEqual(votes["likes"], 0)
        self.assertEqual(votes["dislikes"], 1)
        self.assertEqual(votes["status"], "neutral")

    def test_likealot(self):
        # All messages in thread are voted for
        for num in range(1, 11):
            if num == 1:
                reply_to = None
            else:
                reply_to = num - 1
            _create_email(num, reply_to=reply_to)
            msg = Email.objects.get(message_id="msg%d" % num)
            msg.vote(1, self.user)
        self.assertEqual(Thread.objects.count(), 1)
        thread = Thread.objects.all()[0]
        votes = thread.get_votes()
        self.assertEqual(votes["likes"], 10)
        self.assertEqual(votes["dislikes"], 0)
        self.assertEqual(votes["status"], "likealot")

    def test_same_msgid_different_lists(self):
        # Vote on messages with the same msgid but on different lists
        msg = Message()
        msg["From"] = "sender@example.com"
        msg["Message-ID"] = "<msg>"
        msg.set_payload("message")
        add_to_list("example-list-1", msg)
        add_to_list("example-list-2", msg)
        self.assertEqual(Email.objects.count(), 2)
        for msg in Email.objects.all():
            msg.vote(1, self.user)
        self.assertEqual(Thread.objects.count(), 2)
        for thread in Thread.objects.all():
            votes = thread.get_votes()
            self.assertEqual(votes["likes"], 1)
            self.assertEqual(votes["dislikes"], 0)

    def test_revote(self):
        # Overwrite the existing vote
        _create_email(1)
        msg = Email.objects.get(message_id="msg1")
        msg.vote(1, self.user)
        msg.vote(-1, self.user)
        votes = msg.get_votes()
        self.assertEqual(votes["likes"], 0)
        self.assertEqual(votes["dislikes"], 1)

    def test_revote_identical(self):
        # Voting in the same manner twice should not fail
        _create_email(1)
        msg = Email.objects.get(message_id="msg1")
        msg.vote(1, self.user)
        msg.vote(1, self.user)

    def test_vote_invalid(self):
        # Fail on invalid votes
        _create_email(1)
        msg = Email.objects.get(message_id="msg1")
        self.assertRaises(ValueError, msg.vote, 2, self.user)
