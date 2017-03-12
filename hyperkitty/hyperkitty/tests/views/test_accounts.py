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
# Author: Aamir Khan <syst3m.w0rm@gmail.com>
# Author: Aurelien Bompard <abompard@fedoraproject.org>
#

from __future__ import absolute_import, print_function, unicode_literals

import datetime
import uuid
from email.message import Message
from traceback import format_exc

from allauth.account.models import EmailAddress
from mock import Mock
from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django_mailman3.tests.utils import FakeMMList, FakeMMMember

from hyperkitty.lib.utils import get_message_id_hash
from hyperkitty.lib.incoming import add_to_list
from hyperkitty.models import (
    LastView, MailingList, Thread, Email, Favorite)
from hyperkitty.tests.utils import TestCase


class AccountViewsTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            'testuser', 'test@example.com', 'testPass')
        EmailAddress.objects.create(
            user=self.user, verified=True, email='test@example.com')

    def _send_message(self):
        msg = Message()
        msg["From"] = "Dummy Sender <dummy@example.com>"
        msg["Message-ID"] = "<msg>"
        msg["Subject"] = "Dummy message"
        msg.set_payload("Dummy content")
        return add_to_list("list@example.com", msg)

    def test_login_page(self):
        # Try to access the login page
        response = self.client.get(reverse(settings.LOGIN_URL))
        self.assertEqual(response.status_code, 200)

    def test_redirect_to_login(self):
        # Try to access user profile (private data) without logging in
        response = self.client.get(reverse("hk_user_profile"))
        self.assertRedirects(
            response,
            "%s?next=%s" % (reverse(settings.LOGIN_URL),
                            reverse("hk_user_profile")))

    def test_profile(self):
        self.client.login(username='testuser', password='testPass')
        response = self.client.get(reverse("hk_user_profile"))
        self.assertEqual(response.status_code, 200)

    def test_public_profile(self):
        user_id = uuid.uuid1()
        self.client.login(username='testuser', password='testPass')
        response = self.client.get(reverse("hk_public_user_profile",
                                   args=[user_id.int]))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Email addresses:")

    def test_public_profile_anonymous(self):
        user_id = uuid.uuid1()
        response = self.client.get(reverse("hk_public_user_profile",
                                   args=[user_id.int]))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Email addresses:")

    def test_public_profile_as_oneself(self):
        user_id = uuid.uuid1()
        self.mailman_client.get_list.side_effect = \
            lambda name: FakeMMList(name)
        mm_user = Mock()
        self.mailman_client.get_user.side_effect = lambda name: mm_user
        mm_user.user_id = user_id.int
        mm_user.created_on = None
        mm_user.addresses = ["test@example.com"]
        self.client.login(username='testuser', password='testPass')
        response = self.client.get(reverse("hk_public_user_profile",
                                   args=[user_id.int]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["is_user"])
        self.assertContains(response, "This is you.", count=1)
        self.assertContains(response, "Edit your private profile", count=1)

    def test_public_profile_as_superuser(self):
        user_id = uuid.uuid1()
        self.user.is_superuser = True
        self.user.save()
        self.client.login(username='testuser', password='testPass')
        self.mailman_client.get_list.side_effect = \
            lambda name: FakeMMList(name)
        mm_user = Mock()
        self.mailman_client.get_user.side_effect = lambda name: mm_user
        mm_user.user_id = user_id.int
        mm_user.created_on = None
        mm_user.addresses = [
            "some-user-1@example.com", "some-user-2@example.com",
            ]
        response = self.client.get(reverse("hk_public_user_profile",
                                   args=[user_id.int]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Email addresses:", count=1)
        self.assertContains(response, "some-user-1@example.com", count=1)
        self.assertContains(response, "some-user-2@example.com", count=1)

    def test_registration_redirect(self):
        self.client.login(username='testuser', password='testPass')
        # If the user if already logged in, redirect to index page...
        # Don't let him register again
        response = self.client.get(reverse('account_signup'))
        self.assertRedirects(response, reverse('hk_root'))

        # Access the user registration page after logging out and try to
        # register now
        self.client.logout()
        response = self.client.get(reverse('account_signup'))
        self.assertEqual(response.status_code, 200)

    def test_votes(self):
        self.client.login(username='testuser', password='testPass')
        msg_hash = self._send_message()
        email = Email.objects.get(message_id="msg")
        email.vote(user=self.user, value=1)

        try:
            response = self.client.get(reverse("hk_user_votes"))
        except AttributeError:
            self.fail("Getting the votes should not fail if "
                      "the user has never voted yet\n%s" % format_exc())
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            '<a href="{}">Dummy message</a>'.format(
                reverse(
                    "hk_message_index", args=("list@example.com", msg_hash))
                ), count=2, html=True)
        self.assertContains(
            response, 'action="{}">'.format(
                reverse(
                    "hk_message_vote", args=("list@example.com", msg_hash))
                ), count=2, html=False)
        self.assertContains(response, "Dummy Sender", count=2, html=False)

    def test_favorites(self):
        self.client.login(username='testuser', password='testPass')
        threadid = self._send_message()
        thread = Thread.objects.get(thread_id=threadid)
        self.client.post(
            reverse("hk_favorite", args=("list@example.com", threadid)),
            {"action": "add"})
        self.assertEqual(Favorite.objects.filter(
            thread=thread, user=self.user).count(), 1)

        response = self.client.get(reverse("hk_user_favorites"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "No favorites yet")
        self.assertContains(
            response,
            '<a href="{}">Dummy message</a>'.format(
                reverse(
                    "hk_thread", args=("list@example.com", threadid))
                ), count=2, html=True)
        self.assertContains(response, "Dummy Sender", count=2, html=False)

    def test_posts(self):
        self.client.login(username='testuser', password='testPass')
        msg_hash = self._send_message()
        email = Email.objects.get(message_id="msg")
        email.sender.mailman_id = "dummy_user_id"
        email.sender.save()
        response = self.client.get(
            reverse("hk_user_posts", args=("dummy_user_id",)) +
            "?list=list@example.com")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dummy content", count=1, html=False)
        self.assertContains(response, "Dummy Sender", count=5, html=False)
        self.assertContains(
            response,
            '<a name="{}" href="{}">Dummy message</a>'.format(
                msg_hash,
                reverse(
                    "hk_message_index", args=("list@example.com", msg_hash))
                ), count=1, html=True)


class LastViewsTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            'testuser', 'test@example.com', 'testPass')
        self.client.login(username='testuser', password='testPass')
        # Create test data
        MailingList.objects.create(
            name="list@example.com", subject_prefix="[example] ")
        # Create 3 threads
        messages = []
        for msgnum in range(3):
            msg = Message()
            msg["From"] = "dummy@example.com"
            msg["Message-ID"] = "<id%d>" % (msgnum+1)
            msg["Subject"] = "Dummy message %d" % (msgnum+1)
            msg.set_payload("Dummy message")
            add_to_list("list@example.com", msg)
            messages.append(msg)
        # 1st is unread, 2nd is read, 3rd is updated
        thread_2 = Thread.objects.get(thread_id=get_message_id_hash("<id2>"))
        thread_3 = Thread.objects.get(thread_id=get_message_id_hash("<id3>"))
        LastView.objects.create(user=self.user, thread=thread_2)
        LastView.objects.create(user=self.user, thread=thread_3)
        msg4 = Message()
        msg4["From"] = "dummy@example.com"
        msg4["Message-ID"] = "<id4>"
        msg4["Subject"] = "Dummy message 4"
        msg4["In-Reply-To"] = "<id3>"
        msg4.set_payload("Dummy message")
        add_to_list("list@example.com", msg4)

    def test_profile(self):
        response = self.client.get(reverse('hk_user_last_views'))
        self.assertContains(response, "<td>dummy@example.com</td>",
                            count=2, status_code=200, html=True)
        self.assertContains(
            response,
            '<a href="{}">Dummy message 2</a>'.format(
                reverse("hk_thread", args=("list@example.com",
                                           get_message_id_hash("id2")))),
            count=2, status_code=200, html=True)
        self.assertContains(
            response,
            '<a href="{}">Dummy message 3</a>'.format(
                reverse("hk_thread", args=("list@example.com",
                                           get_message_id_hash("id3")))),
            count=2, status_code=200, html=True)

    def test_thread(self):
        responses = []
        for msgnum in range(3):
            threadid = get_message_id_hash("<id%d>" % (msgnum+1))
            response = self.client.get(reverse('hk_thread', args=(
                        "list@example.com", threadid)))
            responses.append(response)
        # There's always one icon in the right column, so all counts are +1
        self.assertContains(
            responses[0], "fa-envelope", count=2, status_code=200)
        self.assertContains(
            responses[1], "fa-envelope", count=1, status_code=200)
        self.assertContains(
            responses[2], "fa-envelope", count=2, status_code=200)

    def test_thread_list(self):
        now = datetime.datetime.now()
        response = self.client.get(reverse('hk_archives_with_month', args=(
                    "list@example.com", now.year, now.month)))
        self.assertContains(response, "fa-envelope",
                            count=2, status_code=200)

    def test_overview(self):
        response = self.client.get(
            reverse('hk_list_overview', args=["list@example.com"]))
        # 2 in recently active, 2 in most active
        self.assertContains(response, "fa-envelope",
                            count=4, status_code=200)


class SubscriptionsTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            'testuser', 'testuser@example.com', 'testPass')
        self.mailman_client.get_list.side_effect = \
            lambda name: FakeMMList(name)
        self.mm_user = Mock()
        self.mailman_client.get_user.side_effect = lambda name: self.mm_user
        self.mm_user.user_id = uuid.uuid1().int
        self.mm_user.addresses = ["testuser@example.com"]

    def test_get_subscriptions(self):
        mlist = MailingList.objects.create(name="test@example.com")
        self.mm_user.subscriptions = [
            FakeMMMember("test.example.com", self.user.email),
        ]
        self.client.login(username='testuser', password='testPass')
        response = self.client.get(reverse("hk_user_subscriptions"))
        self.assertEqual(
            response.context["subscriptions"], [{
                'first_post': None, 'posts_count': 0,
                'likes': 0, 'dislikes': 0, 'likestatus': 'neutral',
                'mlist': mlist,
                'list_name': "test@example.com",
                'all_posts_url':
                    "%s?list=test@example.com"
                    % reverse("hk_user_posts", args=[self.mm_user.user_id]),
            }])
        self.assertContains(response, "test@example.com", status_code=200)

    def test_list_not_archived(self):
        self.mm_user.subscriptions = [
            FakeMMMember("test.example.com", self.user.email),
        ]
        self.client.login(username='testuser', password='testPass')
        response = self.client.get(reverse("hk_user_subscriptions"))
        self.assertContains(response, "test@example.com", status_code=200)
        self.assertEqual(
            response.context["subscriptions"], [{
                'first_post': None, 'posts_count': 0,
                'likes': 0, 'dislikes': 0, 'likestatus': 'neutral',
                'mlist': None,
                'all_posts_url': None,
                'list_name': "test@example.com",
            }])
