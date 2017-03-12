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

from __future__ import absolute_import, print_function, unicode_literals

import uuid
from email.message import Message

from mock import Mock, patch
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django_mailman3.tests.utils import FakeMMList, FakeMMMember

from hyperkitty.lib.incoming import add_to_list
from hyperkitty.models import MailingList, ArchivePolicy
from hyperkitty.tests.utils import SearchEnabledTestCase


class SearchViewsTestCase(SearchEnabledTestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            'testuser', 'test@example.com', 'testPass')
        self.mailman_client.get_list.side_effect = \
            lambda name: FakeMMList(name)
        self.mm_user = Mock()
        self.mailman_client.get_user.side_effect = lambda name: self.mm_user
        self.mm_user.user_id = uuid.uuid1().int
        self.mm_user.addresses = ["testuser@example.com"]

    def _send_message(self, mlist):
        msg = Message()
        msg["From"] = "Dummy Sender <dummy@example.com>"
        msg["Message-ID"] = "<msg>"
        msg["Subject"] = "Dummy message"
        msg.set_payload("Dummy content with keyword")
        return add_to_list(mlist.name, msg)

    def test_search(self):
        response = self.client.get(reverse("hk_search"), {"q": "dummy"})
        self.assertEqual(response.status_code, 200)

    def test_search_basic(self):
        mlist = MailingList.objects.create(
            name="public@example.com",
            archive_policy=ArchivePolicy.private.value
        )
        mm_mlist = FakeMMList("public@example.com")
        self.mailman_client.get_list.side_effect = lambda name: mm_mlist
        self._send_message(mlist)
        response = self.client.get(
            reverse("hk_search"),
            {"q": "dummy", "mlist": "public@example.com"})
        self.assertContains(response, "Dummy message")

    def test_search_private_list(self):
        mlist = MailingList.objects.create(
            name="private@example.com",
            archive_policy=ArchivePolicy.private.value
        )
        mm_mlist = FakeMMList("private@example.com")
        mm_mlist.settings["archive_policy"] = "private"
        self.mailman_client.get_list.side_effect = lambda name: mm_mlist
        self.mm_user.subscriptions = [
            FakeMMMember("private.example.com", self.user.email),
        ]
        self._send_message(mlist)
        response = self.client.get(
            reverse("hk_search"),
            {"q": "dummy", "mlist": "private@example.com"})
        self.assertEqual(response.status_code, 403)
        self.client.login(username='testuser', password='testPass')
        response = self.client.get(
            reverse("hk_search"),
            {"q": "dummy", "mlist": "private@example.com"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dummy message")

    def test_search_private_lists(self):
        # Create 1 public and 2 private lists
        mlist_public = MailingList.objects.create(name="public@example.com")
        mlist_private = MailingList.objects.create(
            name="private@example.com",
            archive_policy=ArchivePolicy.private.value
        )
        mlist_private_sub = MailingList.objects.create(
            name="private-sub@example.com",
            archive_policy=ArchivePolicy.private.value
        )
        # (make sure the mailman client will not reset the archive_policy)
        mailman_lists = {
            "public@example.com": FakeMMList("public@example.com"),
            "private@example.com": FakeMMList("private@example.com"),
            "private-sub@example.com": FakeMMList("private-sub@example.com"),
        }
        mailman_lists["private@example.com"].settings["archive_policy"] = \
            "private"
        mailman_lists["private-sub@example.com"].settings["archive_policy"] = \
            "private"
        self.mailman_client.get_list.side_effect = \
            lambda name: mailman_lists[name]
        # Subscribe the user to one of the private lists
        self.mm_user.subscriptions = [
            FakeMMMember("private-sub.example.com", self.user.email),
        ]
        # Populate the lists with messages
        self._send_message(mlist_public)
        self._send_message(mlist_private)
        self._send_message(mlist_private_sub)
        # There must be a result from the public and the subscribed list only
        self.client.login(username='testuser', password='testPass')
        response = self.client.get(reverse("hk_search"), {"q": "keyword"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["emails"].paginator.count, 2)
        self.assertContains(response, "Dummy message", count=2)

    def test_email_escaped_body(self):
        MailingList.objects.create(
            name="public@example.com",
            archive_policy=ArchivePolicy.private.value
        )
        mm_mlist = FakeMMList("public@example.com")
        self.mailman_client.get_list.side_effect = lambda name: mm_mlist
        msg = Message()
        msg["From"] = "Dummy Sender <dummy@example.com>"
        msg["Subject"] = "Dummy Subject"
        msg["Date"] = "Mon, 02 Feb 2015 13:00:00 +0300"
        msg["Message-ID"] = "<msg2>"
        msg.set_payload("Email address: email@example.com")
        add_to_list("public@example.com", msg)
        for query in [{"q": "dummy"},
                      {"q": "dummy", "mlist": "public@example.com"}]:
            response = self.client.get(reverse("hk_search"), query)
            self.assertNotContains(
                response, "email@example.com",
                msg_prefix="With query %r" % query, status_code=200)

    def test_email_in_link_in_body(self):
        MailingList.objects.create(
            name="public@example.com",
            archive_policy=ArchivePolicy.private.value
        )
        mm_mlist = FakeMMList("public@example.com")
        self.mailman_client.get_list.side_effect = lambda name: mm_mlist
        msg = Message()
        msg["From"] = "Dummy Sender <dummy@example.com>"
        msg["Subject"] = "Dummy Subject"
        msg["Date"] = "Mon, 02 Feb 2015 13:00:00 +0300"
        msg["Message-ID"] = "<msg2>"
        link = "http://example.com/list/email@example.com/message"
        msg.set_payload("Email address in link: %s" % link)
        add_to_list("public@example.com", msg)
        for query in [{"q": "dummy"},
                      {"q": "dummy", "mlist": "public@example.com"}]:
            response = self.client.get(reverse("hk_search"), query)
            self.assertContains(
                response, '<a href="{0}" rel="nofollow">{0}</a>'.format(link),
                msg_prefix="With query %r" % query, status_code=200)

    def test_email_escaped_sender(self):
        MailingList.objects.create(
            name="public@example.com",
            archive_policy=ArchivePolicy.private.value
        )
        mm_mlist = FakeMMList("public@example.com")
        self.mailman_client.get_list.side_effect = lambda name: mm_mlist
        msg = Message()
        msg["From"] = "someone-else@example.com"
        msg["Subject"] = "Dummy Subject"
        msg["Date"] = "Mon, 02 Feb 2015 13:00:00 +0300"
        msg["Message-ID"] = "<msg2>"
        msg.set_payload("Dummy content")
        add_to_list("public@example.com", msg)
        for query in [{"q": "dummy"},
                      {"q": "dummy", "mlist": "public@example.com"}]:
            response = self.client.get(reverse("hk_search"), query)
            self.assertNotContains(
                response, "someone-else@example.com",
                msg_prefix="With query %r" % query, status_code=200)

    def test_parse_error(self):
        from whoosh.qparser.common import QueryParserError

        class CrashingIterator(list):
            def __len__(self):
                raise QueryParserError("dummy parsing failure")
            query = Mock()

        with patch("hyperkitty.views.search.SearchForm.search") as form_search:
            form_search.return_value = CrashingIterator()
            response = self.client.get(reverse("hk_search"), {"q": "FAIL"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "alert-danger")
        self.assertContains(response, "dummy parsing failure")
