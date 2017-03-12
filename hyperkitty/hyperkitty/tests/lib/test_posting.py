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

from __future__ import absolute_import, print_function, unicode_literals

import uuid
from django.contrib.auth.models import User
from django.core import mail
from django.test.client import RequestFactory
from django.utils import six
from django_mailman3.tests.utils import FakeMMList, FakeMMMember
from mock import Mock, patch

from hyperkitty.lib import posting
from hyperkitty.models import MailingList
from hyperkitty.tests.utils import TestCase


class PostingTestCase(TestCase):

    def setUp(self):
        self.mlist = MailingList.objects.create(name="list@example.com")
        self.ml = FakeMMList("list@example.com")
        self.mailman_client.get_list.side_effect = lambda n: self.ml
        self.ml.get_member = Mock()
        self.user = User.objects.create_user(
            'testuser', 'testuser@example.com', 'testPass')
        self.mm_user = Mock()
        self.mailman_client.get_user.side_effect = lambda name: self.mm_user
        self.mm_user.user_id = uuid.uuid1().int
        self.mm_user.addresses = ["testuser@example.com"]
        self.mm_user.subscriptions = []
        self.request = RequestFactory().get("/")
        self.request.user = self.user

    def test_basic_reply(self):
        self.user.first_name = "Django"
        self.user.last_name = "User"
        self.user.save()
        with patch("hyperkitty.lib.posting.mailman.subscribe") as sub_fn:
            posting.post_to_list(
                self.request, self.mlist, "Dummy subject", "dummy content",
                {"In-Reply-To": "<msg>", "References": "<msg>"})
            sub_fn.assert_called_with(
                'list@example.com', self.user, 'testuser@example.com',
                'Django User')
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].recipients(), ["list@example.com"])
        self.assertEqual(mail.outbox[0].from_email,
                         '"Django User" <testuser@example.com>')
        self.assertEqual(mail.outbox[0].subject, 'Dummy subject')
        self.assertEqual(mail.outbox[0].body, "dummy content")
        self.assertEqual(mail.outbox[0].message().get("references"), "<msg>")
        self.assertEqual(mail.outbox[0].message().get("in-reply-to"), "<msg>")

    def test_reply_different_sender(self):
        self.user.first_name = "Django"
        self.user.last_name = "User"
        self.user.save()
        with patch("hyperkitty.lib.posting.mailman.subscribe") as sub_fn:
            posting.post_to_list(
                self.request, self.mlist, "Subject", "Content",
                {"From": "otheremail@example.com"})
            sub_fn.assert_called_with(
                'list@example.com', self.user, 'otheremail@example.com',
                'Django User')
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].recipients(), ["list@example.com"])
        self.assertEqual(mail.outbox[0].from_email,
                         '"Django User" <otheremail@example.com>')

    def test_sender_not_subscribed(self):
        self.assertEqual(posting.get_sender(self.request, self.mlist),
                         "testuser@example.com")

    def test_sender_with_display_name(self):
        self.user.first_name = "Test"
        self.user.last_name = "User"
        posting.post_to_list(self.request, self.mlist, "Test message", "dummy")
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].from_email,
                         '"Test User" <testuser@example.com>')

    def test_sender_subscribed(self):
        self.mm_user.subscriptions = [
            FakeMMMember(self.mlist.list_id, "secondemail@example.com"),
        ]
        self.assertEqual(posting.get_sender(self.request, self.mlist),
                         "secondemail@example.com")

    def test_unwrap_subject(self):
        subject = "This subject contains\n    a newline"
        try:
            posting.post_to_list(self.request, self.mlist, subject,
                                 "dummy content")
        except ValueError as e:
            self.fail(e)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, subject.replace("\n   ", ""))

    def test_unwrap_subject_2(self):
        subject = 'This subject is wrapped with\n a newline'
        try:
            posting.post_to_list(self.request, self.mlist, subject,
                                 "dummy content")
        except ValueError as e:
            self.fail(e)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, subject.replace("\n ", " "))

    def test_get_sender_is_string(self):
        # The get_sender function must always return a string
        from mailmanclient._client import Address
        self.mm_user.addresses = [
            Address(None, None, dict(email="testuser@example.com")),
            ]
        self.mm_user.subscriptions = [
            FakeMMMember(self.mlist.list_id, self.mm_user.addresses[0]),
        ]
        addr = posting.get_sender(self.request, self.mlist)
        self.assertTrue(isinstance(addr, six.string_types))
