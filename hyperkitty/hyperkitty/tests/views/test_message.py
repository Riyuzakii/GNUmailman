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

import json
import uuid
from email.message import Message

from allauth.account.models import EmailAddress
from mock import Mock, patch
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.core import mail
from django.utils import timezone
from django_gravatar.helpers import get_gravatar_url
from django_mailman3.tests.utils import get_flash_messages

from hyperkitty.lib.utils import get_message_id_hash
from hyperkitty.lib.incoming import add_to_list
from hyperkitty.models.email import Email
from hyperkitty.models.mailinglist import MailingList
from hyperkitty.models.thread import Thread
from hyperkitty.tests.utils import TestCase


class MessageViewsTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
                'testuser', 'test@example.com', 'testPass')
        self.client.login(username='testuser', password='testPass')
        # Create a dummy message to test on
        msg = Message()
        msg["From"] = "Dummy Sender <dummy@example.com>"
        msg["Subject"] = "Dummy Subject"
        msg["Date"] = "Mon, 02 Feb 2015 13:00:00 +0300"
        msg["Message-ID"] = "<msg>"
        msg.set_payload("Dummy message")
        add_to_list("list@example.com", msg)

    def test_vote_up(self):
        url = reverse('hk_message_vote', args=("list@example.com",
                      get_message_id_hash("msg")))
        resp = self.client.post(url, {"vote": "1"})
        self.assertEqual(resp.status_code, 200)
        result = json.loads(resp.content)
        self.assertEqual(result["like"], 1)
        self.assertEqual(result["dislike"], 0)

    def test_vote_down(self):
        url = reverse('hk_message_vote', args=("list@example.com",
                      get_message_id_hash("msg")))
        resp = self.client.post(url, {"vote": "-1"})
        self.assertEqual(resp.status_code, 200)
        result = json.loads(resp.content)
        self.assertEqual(result["like"], 0)
        self.assertEqual(result["dislike"], 1)

    def test_vote_cancel(self):
        msg = Message()
        msg["From"] = "dummy@example.com"
        msg["Message-ID"] = "<msg1>"
        msg.set_payload("Dummy message")
        add_to_list("list@example.com", msg)
        msg.replace_header("Message-ID", "<msg2>")
        add_to_list("list@example.com", msg)
        msg1 = Email.objects.get(mailinglist__name="list@example.com",
                                 message_id="msg1")
        msg1.vote(1, self.user)
        msg2 = Email.objects.get(mailinglist__name="list@example.com",
                                 message_id="msg2")
        msg2.vote(-1, self.user)
        self.assertEqual(msg1.get_votes()["likes"], 1)
        self.assertEqual(msg2.get_votes()["dislikes"], 1)
        for msg in (msg1, msg2):
            url = reverse('hk_message_vote', args=("list@example.com",
                          msg.message_id_hash))
            resp = self.client.post(url, {"vote": "0"})
            self.assertEqual(resp.status_code, 200)
            votes = msg.get_votes()
            self.assertEqual(votes["likes"], 0)
            self.assertEqual(votes["dislikes"], 0)
            result = json.loads(resp.content)
            self.assertEqual(result["like"], 0)
            self.assertEqual(result["dislike"], 0)

    def test_unauth_vote(self):
        self.client.logout()
        url = reverse('hk_message_vote', args=("list@example.com",
                      get_message_id_hash("msg")))
        resp = self.client.post(url, {"vote": "1"})
        self.assertEqual(resp.status_code, 403)

    def test_message_page(self):
        url = reverse('hk_message_index', args=("list@example.com",
                      get_message_id_hash("msg")))
        with self.settings(USE_L10N=False, DATETIME_FORMAT='Y-m-d H:i:s',
                           TIME_FORMAT="H:i:s"):
            with timezone.override(timezone.utc):
                response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dummy message")
        self.assertContains(response, "Dummy Sender", count=1)
        self.assertContains(response, "Dummy Subject", count=3)
        self.assertNotContains(response, "dummy@example.com")
        self.assertContains(
            response,
            get_gravatar_url("dummy@example.com", 120).replace("&", "&amp;"))
        self.assertContains(response, "list@example.com")
        self.assertContains(response, url)
        sender_time = ('<span title="Sender\'s time: 2015-02-02 '
                       '13:00:00">10:00:00</span>')
        self.assertIn(sender_time, response.content.decode("utf-8"))

    def test_reply(self):
        self.user.first_name = "Django"
        self.user.last_name = "User"
        self.user.save()
        mlist = MailingList.objects.get(name="list@example.com")
        url = reverse('hk_message_reply', args=("list@example.com",
                      get_message_id_hash("msg")))
        with patch("hyperkitty.views.message.post_to_list") as posting_fn:
            response = self.client.post(
                url, {"message": "dummy reply content"})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(posting_fn.call_count, 1)
            self.assertEqual(
                posting_fn.call_args[0][1:],
                (mlist, 'Re: Dummy Subject', 'dummy reply content',
                 {'References': '<msg>', 'In-Reply-To': '<msg>'}))
        result = json.loads(response.content)
        self.assertIn("Django User", result["message_html"])
        self.assertIn("dummy reply content", result["message_html"])
        self.assertIn(
            get_gravatar_url("test@example.com", 120).replace("&", "&amp;"),
            result["message_html"])

    def test_reply_newthread(self):
        mlist = MailingList.objects.get(name="list@example.com")
        url = reverse('hk_message_reply', args=("list@example.com",
                      get_message_id_hash("msg")))
        with patch("hyperkitty.views.message.post_to_list") as posting_fn:
            response = self.client.post(
                url,
                {"message": "dummy reply content",
                 "newthread": 1, "subject": "new subject"})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(posting_fn.call_count, 1)
            self.assertEqual(
                posting_fn.call_args[0][1:],
                (mlist, 'new subject', 'dummy reply content', {}))
        result = json.loads(response.content)
        self.assertEqual(result["message_html"], None)

    def test_reply_different_sender(self):
        self.user.first_name = "Django"
        self.user.last_name = "User"
        self.user.save()
        EmailAddress.objects.create(
            user=self.user, verified=True, email="testuser@example.com")
        EmailAddress.objects.create(
            user=self.user, verified=True, email="otheremail@example.com")
        mm_user = Mock()
        self.mailman_client.get_user.side_effect = lambda name: mm_user
        mm_user.user_id = uuid.uuid1().int
        mm_user.subscriptions = []
        mlist = MailingList.objects.get(name="list@example.com")
        url = reverse('hk_message_reply', args=("list@example.com",
                      get_message_id_hash("msg")))
        with patch("hyperkitty.views.message.post_to_list") as posting_fn:
            response = self.client.post(url, {
                "message": "dummy reply content",
                "sender": "otheremail@example.com",
                })
            self.assertEqual(response.status_code, 200)
            self.assertEqual(posting_fn.call_count, 1)
            self.assertEqual(
                posting_fn.call_args[0][1:],
                (mlist, 'Re: Dummy Subject', 'dummy reply content',
                 {'From': 'otheremail@example.com',
                  'In-Reply-To': '<msg>', 'References': '<msg>'}))
        result = json.loads(response.content)
        self.assertIn("Django User", result["message_html"])
        self.assertIn("dummy reply content", result["message_html"])
        self.assertIn(
            get_gravatar_url("otheremail@example.com", 120).replace(
                "&", "&amp;"),
            result["message_html"])

    def test_new_message_page(self):
        url = reverse('hk_message_new', args=["list@example.com"])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)

    def test_new_message_post(self):
        self.user.first_name = "Django"
        self.user.last_name = "User"
        self.user.save()
        url = reverse('hk_message_new', args=["list@example.com"])
        with patch("hyperkitty.lib.posting.mailman.subscribe") as sub_fn:
            response = self.client.post(url, {
                "subject": "Test subject",
                "message": "Test message content"})
        self.assertTrue(sub_fn.called)
        redirect_url = reverse(
                'hk_archives_with_month', kwargs={
                    "mlist_fqdn": "list@example.com",
                    'year': timezone.now().year,
                    'month': timezone.now().month})
        self.assertRedirects(response, redirect_url)
        # flash message
        messages = get_flash_messages(response)
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].tags, "success")
        # sent email
        self.assertEqual(len(mail.outbox), 1)
        # print(mail.outbox[0].message())
        self.assertEqual(mail.outbox[0].recipients(), ["list@example.com"])
        self.assertEqual(mail.outbox[0].from_email,
                         '"Django User" <test@example.com>')
        self.assertEqual(mail.outbox[0].subject, 'Test subject')
        self.assertEqual(mail.outbox[0].body, "Test message content")
        self.assertIsNone(mail.outbox[0].message().get("references"))
        self.assertIsNone(mail.outbox[0].message().get("in-reply-to"))

    def test_new_message_different_sender(self):
        self.user.first_name = "Django"
        self.user.last_name = "User"
        self.user.save()
        EmailAddress.objects.create(
            user=self.user, verified=True, email="testuser@example.com")
        EmailAddress.objects.create(
            user=self.user, verified=True, email="otheremail@example.com")
        mm_user = Mock()
        self.mailman_client.get_user.side_effect = lambda name: mm_user
        mm_user.user_id = uuid.uuid1().int
        mm_user.subscriptions = []
        mlist = MailingList.objects.get(name="list@example.com")
        url = reverse('hk_message_new', args=["list@example.com"])
        with patch("hyperkitty.views.message.post_to_list") as posting_fn:
            response = self.client.post(url, {
                "subject": "Test subject",
                "sender": "otheremail@example.com",
                "message": "Test message content",
                })
            self.assertEqual(posting_fn.call_count, 1)
            self.assertEqual(
                posting_fn.call_args[0][1:],
                (mlist, 'Test subject', 'Test message content',
                 {'From': 'otheremail@example.com'}))
        redirect_url = reverse(
                'hk_archives_with_month', kwargs={
                    "mlist_fqdn": "list@example.com",
                    'year': timezone.now().year,
                    'month': timezone.now().month})
        self.assertRedirects(response, redirect_url)
        # flash message
        messages = get_flash_messages(response)
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].tags, "success")

    def test_display_fixed(self):
        msg = Message()
        msg["From"] = "Dummy Sender <dummy@example.com>"
        msg["Subject"] = "Dummy Subject"
        msg["Date"] = "Mon, 02 Feb 2015 13:00:00 +0300"
        msg["Message-ID"] = "<msg2>"
        msg.set_payload("Dummy message with @@ signs (looks like a patch)")
        add_to_list("list@example.com", msg)
        url1 = reverse(
            'hk_message_index', args=("list@example.com",
                                      get_message_id_hash("msg")))
        response1 = self.client.get(url1)
        self.assertNotContains(response1, "email-body fixed", status_code=200)
        url2 = reverse(
            'hk_message_index', args=("list@example.com",
                                      get_message_id_hash("msg2")))
        response2 = self.client.get(url2)
        self.assertContains(response2, "email-body fixed", status_code=200)

    def test_email_escaped_body(self):
        msg = Message()
        msg["From"] = "Dummy Sender <dummy@example.com>"
        msg["Subject"] = "Dummy Subject"
        msg["Date"] = "Mon, 02 Feb 2015 13:00:00 +0300"
        msg["Message-ID"] = "<msg2>"
        msg.set_payload("Email address: email@example.com")
        add_to_list("list@example.com", msg)
        url = reverse('hk_message_index', args=("list@example.com",
                      get_message_id_hash("msg2")))
        response = self.client.get(url)
        self.assertNotContains(response, "email@example.com", status_code=200)

    def test_email_in_link_in_body(self):
        msg = Message()
        msg["From"] = "Dummy Sender <dummy@example.com>"
        msg["Subject"] = "Dummy Subject"
        msg["Date"] = "Mon, 02 Feb 2015 13:00:00 +0300"
        msg["Message-ID"] = "<msg2>"
        link = "http://example.com/list/email@example.com/message"
        msg.set_payload("Email address in link: %s" % link)
        add_to_list("list@example.com", msg)
        url = reverse('hk_message_index', args=("list@example.com",
                      get_message_id_hash("msg2")))
        response = self.client.get(url)
        self.assertContains(
            response, '<a href="{0}" rel="nofollow">{0}</a>'.format(link),
            status_code=200)

    def test_email_escaped_sender(self):
        msg = Message()
        msg["From"] = "someone-else@example.com"
        msg["Subject"] = "Dummy Subject"
        msg["Date"] = "Mon, 02 Feb 2015 13:00:00 +0300"
        msg["Message-ID"] = "<msg2>"
        msg.set_payload("Dummy content")
        add_to_list("list@example.com", msg)
        url = reverse('hk_message_index', args=("list@example.com",
                      get_message_id_hash("msg2")))
        response = self.client.get(url)
        self.assertNotContains(
            response, "someone-else@example.com", status_code=200)

    def test_delete_forbidden(self):
        url = reverse('hk_message_delete', args=("list@example.com",
                      get_message_id_hash("msg")))
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)

    def test_delete_single_message(self):
        self.user.is_staff = True
        self.user.save()
        msg = Email.objects.get(message_id="msg")
        thread_id = msg.thread.pk
        url = reverse('hk_message_delete',
                      args=("list@example.com", msg.message_id_hash))
        response = self.client.post(url, {"email": msg.pk})
        self.assertRedirects(
            response, reverse('hk_list_overview', kwargs={
                "mlist_fqdn": "list@example.com"}))
        # Flash message
        messages = get_flash_messages(response)
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].tags, "success")
        # The message and the thread must be deleted.
        self.assertFalse(Email.objects.filter(message_id="msg").exists())
        self.assertFalse(Thread.objects.filter(pk=thread_id).exists())

    def test_delete_single_in_thread(self):
        # Delete an email in a thread that contains other emails
        self.user.is_staff = True
        self.user.save()
        msg = Email.objects.get(message_id="msg")
        msg2 = Message()
        msg2["From"] = "dummy@example.com"
        msg2["Message-ID"] = "<msg2>"
        msg2["In-Reply-To"] = "<msg>"
        msg2.set_payload("Dummy message")
        add_to_list("list@example.com", msg2)
        msg2 = Email.objects.get(message_id="msg2")
        thread_id = msg.thread.thread_id
        url = reverse('hk_message_delete',
                      args=("list@example.com", msg.message_id_hash))
        response = self.client.post(url, {"email": msg.pk})
        self.assertRedirects(
            response, reverse('hk_thread', kwargs={
                "mlist_fqdn": "list@example.com",
                "threadid": thread_id}))
        # Flash message
        messages = get_flash_messages(response)
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].tags, "success")
        # The message must be deleted, but not the other message or the thread.
        self.assertFalse(Email.objects.filter(message_id="msg").exists())
        self.assertTrue(Email.objects.filter(message_id="msg2").exists())
        thread = Thread.objects.get(thread_id=thread_id)
        self.assertIsNotNone(thread)
        # msg2 must now be the thread starter.
        msg2.refresh_from_db()
        self.assertIsNone(msg2.parent_id)
        self.assertEqual(thread.starting_email.message_id, "msg2")

    def test_delete_all_messages_in_thread(self):
        self.user.is_staff = True
        self.user.save()
        msg = Email.objects.get(message_id="msg")
        msg2 = Message()
        msg2["From"] = "dummy@example.com"
        msg2["Message-ID"] = "<msg2>"
        msg2["In-Reply-To"] = "<msg>"
        msg2.set_payload("Dummy message")
        add_to_list("list@example.com", msg2)
        msg2 = Email.objects.get(message_id="msg2")
        thread_id = msg.thread.pk
        url = reverse('hk_thread_delete',
                      args=("list@example.com", msg.thread.thread_id))
        response = self.client.post(url, {"email": [msg.pk, msg2.pk]})
        self.assertRedirects(
            response, reverse('hk_list_overview', kwargs={
                "mlist_fqdn": "list@example.com"}))
        # Flash message
        messages = get_flash_messages(response)
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].tags, "success")
        # Alls messages and the thread must be deleted.
        self.assertFalse(Email.objects.filter(message_id="msg").exists())
        self.assertFalse(Email.objects.filter(message_id="msg2").exists())
        self.assertFalse(Thread.objects.filter(pk=thread_id).exists())
