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
import re
import urlparse
from email.message import Message

from bs4 import BeautifulSoup

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django_mailman3.tests.utils import get_flash_messages

from hyperkitty.lib.incoming import add_to_list
from hyperkitty.models import MailingList, Thread, Tag, Tagging, Email
from hyperkitty.tests.utils import TestCase, SearchEnabledTestCase


class ReattachTestCase(SearchEnabledTestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            'testuser', 'test@example.com', 'testPass')
        self.user.is_staff = True
        self.user.save()
        self.client.login(username='testuser', password='testPass')
        MailingList.objects.create(
            name="list@example.com", subject_prefix="[example] ")
        # Create 2 threads
        self.messages = []
        for msgnum in range(2):
            msg = Message()
            msg["From"] = "dummy@example.com"
            msg["Message-ID"] = "<id%d>" % (msgnum+1)
            msg["Subject"] = "Dummy message"
            msg.set_payload("Dummy message")
            msg["Message-ID-Hash"] = add_to_list("list@example.com", msg)
            self.messages.append(msg)

    def test_suggestions(self):
        threadid = self.messages[0]["Message-ID-Hash"]
        Email.objects.get(message_id="id2")
        response = self.client.get(reverse('hk_thread_reattach_suggest',
                                   args=["list@example.com", threadid]))
        other_threadid = self.messages[1]["Message-ID-Hash"]
        expected = ('<input type="radio" name="parent" value="%s" />'
                    % other_threadid)
        self.assertEqual(len(response.context["suggested_threads"]), 1)
        self.assertEqual(response.context["suggested_threads"][0].thread_id,
                         other_threadid)
        self.assertContains(response, expected, count=1, status_code=200)

    def test_reattach(self):
        threadid1 = self.messages[0]["Message-ID-Hash"]
        threadid2 = self.messages[1]["Message-ID-Hash"]
        response = self.client.post(
            reverse('hk_thread_reattach',
                    args=["list@example.com", threadid2]),
            data={"parent": threadid1})
        threads = Thread.objects.order_by("id")
        self.assertEqual(len(threads), 1)
        self.assertEqual(threads[0].thread_id, threadid1)
        expected_url = reverse(
            'hk_thread', args=["list@example.com", threadid1])
        self.assertRedirects(response, expected_url)
        messages = get_flash_messages(response)
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].tags, "success")

    def test_reattach_manual(self):
        threadid1 = self.messages[0]["Message-ID-Hash"]
        threadid2 = self.messages[1]["Message-ID-Hash"]
        response = self.client.post(reverse('hk_thread_reattach',
                                    args=["list@example.com", threadid2]),
                                    data={"parent": "",
                                          "parent-manual": threadid1})
        threads = Thread.objects.order_by("id")
        self.assertEqual(threads[0].thread_id, threadid1)
        expected_url = reverse(
            'hk_thread', args=["list@example.com", threadid1])
        self.assertRedirects(response, expected_url)
        messages = get_flash_messages(response)
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].tags, "success")

    def test_reattach_invalid(self):
        threadid = self.messages[0]["Message-ID-Hash"]
        response = self.client.post(reverse('hk_thread_reattach',
                                    args=["list@example.com", threadid]),
                                    data={"parent": "invalid-data"})
        self.assertEqual(Thread.objects.count(), 2)
        for thread in Thread.objects.all():
            self.assertEqual(thread.emails.count(), 1)
        messages = list(response.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].tags, "warning")
        self.assertIn("Invalid thread id, it should look", str(messages[0]))

    def test_reattach_on_itself(self):
        threadid = self.messages[0]["Message-ID-Hash"]
        response = self.client.post(reverse('hk_thread_reattach',
                                    args=["list@example.com", threadid]),
                                    data={"parent": threadid})
        self.assertEqual(Thread.objects.count(), 2)
        for thread in Thread.objects.all():
            self.assertEqual(thread.emails.count(), 1)
        messages = list(response.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].tags, "warning")
        self.assertIn(
            "Can't re-attach a thread to itself",
            str(messages[0]))

    def test_reattach_on_unknown(self):
        threadid = self.messages[0]["Message-ID-Hash"]
        threadid_unknown = "L36TVP2EFFDSXGVNQJCY44W5AB2YMJ65"
        response = self.client.post(reverse('hk_thread_reattach',
                                    args=["list@example.com", threadid]),
                                    data={"parent": threadid_unknown})
        self.assertEqual(Thread.objects.count(), 2)
        for thread in Thread.objects.all():
            self.assertEqual(thread.emails.count(), 1)
        messages = list(response.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].tags, "warning")
        self.assertIn("Unknown thread", str(messages[0]))


class ThreadTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            'testuser', 'test@example.com', 'testPass')
        self.user.is_staff = True
        self.user.save()
        self.client.login(username='testuser', password='testPass')
        MailingList.objects.create(
            name="list@example.com", subject_prefix="[example] ")
        msg = self._make_msg("msgid")
        self.threadid = msg["Message-ID-Hash"]

    def _make_msg(self, msgid, headers=None):
        if headers is None:
            headers = {}
        msg = Message()
        msg["From"] = "dummy@example.com"
        msg["Message-ID"] = "<%s>" % msgid
        msg["Subject"] = "Dummy message"
        msg.set_payload("Dummy message")
        for header, value in headers.items():
            if header in msg:
                msg.replace_header(header, value)
            else:
                msg[header] = value
        msg["Message-ID-Hash"] = add_to_list("list@example.com", msg)
        return msg

    def do_tag_post(self, data):
        url = reverse('hk_tags', args=["list@example.com", self.threadid])
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        return json.loads(response.content)

    def test_add_tag(self):
        result = self.do_tag_post({"tag": "testtag", "action": "add"})
        self.assertEqual(result["tags"], ["testtag"])

    def test_add_tag_stripped(self):
        result = self.do_tag_post({"tag": " testtag ", "action": "add"})
        self.assertEqual(result["tags"], ["testtag"])
        self.assertEqual(Tag.objects.count(), 1)
        self.assertEqual(Tag.objects.all()[0].name, "testtag")

    def test_add_tag_twice(self):
        # A second adding of the same tag should just be ignored
        thread = Thread.objects.get(thread_id=self.threadid)
        tag = Tag.objects.create(name="testtag")
        Tagging.objects.create(tag=tag, thread=thread, user=self.user)
        result = self.do_tag_post({"tag": "testtag", "action": "add"})
        self.assertEqual(result["tags"], [u"testtag"])
        self.assertEqual(Tag.objects.count(), 1)
        self.assertEqual(Tagging.objects.count(), 1)

    def test_add_multiple_tags(self):
        result = self.do_tag_post({
            "tag": "testtag 1, testtag 2 ; testtag 3",
            "action": "add"})
        expected = ["testtag 1", "testtag 2", "testtag 3"]
        self.assertEqual(result["tags"], expected)
        self.assertEqual(Tag.objects.count(), 3)
        self.assertEqual(list(Tag.objects.values_list("name", flat=True)),
                         expected)

    def test_same_tag_by_different_users(self):
        # If the same tag is added by different users, it must only show up
        # once in the page AND if the current user is one of the taggers, the
        # tag must be removable.
        User.objects.create_user(
            'testuser_2', 'test2@example.com', 'testPass')
        self.do_tag_post({"tag": "testtag", "action": "add"})
        self.client.logout()
        self.client.login(username='testuser_2', password='testPass')
        result = self.do_tag_post({"tag": "testtag", "action": "add"})
        self.assertEqual(result["tags"], ["testtag"])

    def test_tag_removal_form(self):
        user_2 = User.objects.create_user(
            'testuser_2', 'test2@example.com', 'testPass')
        user_3 = User.objects.create_user(
            'testuser_3', 'test3@example.com', 'testPass')
        User.objects.create_user(
            'testuser_4', 'test4@example.com', 'testPass')
        url = reverse('hk_thread', args=["list@example.com", self.threadid])
        thread = Thread.objects.get(thread_id=self.threadid)
        # Create tags
        t1 = Tag.objects.create(name="t1")
        t2 = Tag.objects.create(name="t2")
        Tagging.objects.create(tag=t1, thread=thread, user=self.user)
        Tagging.objects.create(tag=t1, thread=thread, user=user_2)
        Tagging.objects.create(tag=t2, thread=thread, user=user_3)

        def check_page(username, expected_num_form):
            self.client.logout()
            self.client.login(username=username, password='testPass')
            response = self.client.get(url)
            soup = BeautifulSoup(response.content, "html.parser")
            tags = soup.find("div", id="tags")
            self.assertIsNotNone(tags)
            self.assertEqual(len(tags.find_all("li")), 2)
            self.assertEqual(len(tags.find_all("form")), expected_num_form)
        # self.user, user_2 and user_3 should see one removal form
        check_page("testuser", 1)
        check_page("testuser_2", 1)
        check_page("testuser_3", 1)
        # user_4 should see no removal form
        check_page("testuser_4", 0)

    def test_num_comments(self):
        self._make_msg("msgid2", {"In-Reply-To": "<msgid>"})
        self._make_msg("msgid3", {"In-Reply-To": "<msgid2>"})
        self._make_msg("msgid4", {"In-Reply-To": "<msgid3>"})
        url = reverse('hk_thread', args=["list@example.com", self.threadid])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue("num_comments" in response.context)
        self.assertEqual(response.context["num_comments"], 3)

    def test_reply_button(self):
        def check_mailto(link):
            self.assertTrue(link is not None)
            link_mo = re.match(r'mailto:list@example.com\?(.+)', link["href"])
            self.assertTrue(link_mo is not None)
            params = urlparse.parse_qs(link_mo.group(1))
            self.assertEqual(params, {u'In-Reply-To': [u'<msgid>'],
                                      u'Subject':     [u'Re: Dummy message']})
        url = reverse('hk_thread', args=["list@example.com", self.threadid])
        # Authenticated request
        response = self.client.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        self.assertEqual(len(soup.find_all("a", class_="reply-mailto")), 1)
        self.assertTrue(soup.find("a", class_="reply") is not None)
        link = soup.find(class_="reply-tools").find("a", class_="reply-mailto")
        check_mailto(link)
        # Anonymous request
        self.client.logout()
        response = self.client.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        self.assertEqual(len(soup.find_all("a", class_="reply-mailto")), 1)
        link = soup.find("a", class_="reply")
        self.assertTrue(link is not None)
        self.assertTrue("reply-mailto" in link["class"])
        check_mailto(link)

    def test_subject_changed(self):
        # Test the detection of subject change
        self._make_msg("msgid2", {"In-Reply-To": "<msgid>",
                       "Subject": "Re: Dummy message"})
        self._make_msg("msgid3", {"In-Reply-To": "<msgid2>",
                       "Subject": "Re: Re: Dummy message"})
        self._make_msg("msgid4", {"In-Reply-To": "<msgid3>",
                       "Subject": "Re: Re: Re: Dummy message"})
        self._make_msg("msgid5", {"In-Reply-To": "<msgid4>",
                       "Subject": "[example] Re: Dummy message"})
        self._make_msg("msgid6", {"In-Reply-To": "<msgid5>",
                       "Subject": "Re: [example] Dummy message"})
        self._make_msg("msgid7", {"In-Reply-To": "<msgid6>",
                       "Subject": "Re: [example] Re: Dummy message"})
        url = reverse('hk_thread', args=["list@example.com", self.threadid])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["replies"]), 6)
        for email in response.context["replies"]:
            self.assertFalse(
                email.changed_subject,
                "Message %s changed subject" % email.message_id)

    def test_display_fixed(self):
        msg = Message()
        msg["From"] = "dummy@example.com"
        msg["Message-ID"] = "<msgid2>"
        msg["Subject"] = "Dummy message"
        msg["In-Reply-To"] = "<msgid>"
        msg.set_payload("Dummy message with @@ signs (looks like a patch)")
        msg["Message-ID-Hash"] = add_to_list("list@example.com", msg)
        url = reverse('hk_thread', args=["list@example.com", self.threadid])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '"email-body fixed"', count=1)
        self.assertContains(response, '"email-body "', count=1)

    def test_email_escaped_body(self):
        msg = Message()
        msg["From"] = "Dummy Sender <dummy@example.com>"
        msg["Subject"] = "Dummy Subject"
        msg["Date"] = "Mon, 02 Feb 2015 13:00:00 +0300"
        msg["Message-ID"] = "<msgid2>"
        msg["In-Reply-To"] = "<msgid>"
        msg.set_payload("Email address: email@example.com")
        add_to_list("list@example.com", msg)
        url = reverse('hk_thread', args=["list@example.com", self.threadid])
        response = self.client.get(url)
        self.assertNotContains(response, "email@example.com", status_code=200)

    def test_email_in_link_in_body(self):
        msg = Message()
        msg["From"] = "Dummy Sender <dummy@example.com>"
        msg["Subject"] = "Dummy Subject"
        msg["Date"] = "Mon, 02 Feb 2015 13:00:00 +0300"
        msg["Message-ID"] = "<msgid2>"
        msg["In-Reply-To"] = "<msgid>"
        link = "http://example.com/list/email@example.com/message"
        msg.set_payload("Email address in link: %s" % link)
        add_to_list("list@example.com", msg)
        url = reverse('hk_thread', args=["list@example.com", self.threadid])
        response = self.client.get(url)
        self.assertContains(
            response, '<a href="{0}" rel="nofollow">{0}</a>'.format(link),
            status_code=200)

    def test_email_escaped_sender(self):
        url = reverse('hk_thread', args=["list@example.com", self.threadid])
        response = self.client.get(url)
        self.assertNotContains(response, "dummy@example.com", status_code=200)
