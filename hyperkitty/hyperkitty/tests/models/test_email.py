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
from email.mime.text import MIMEText
from mimetypes import guess_all_extensions

from hyperkitty.lib.incoming import add_to_list
from hyperkitty.models import Email, Thread
from hyperkitty.tests.utils import TestCase


class EmailTestCase(TestCase):

    def test_as_message(self):
        msg_in = Message()
        msg_in["From"] = "dummy@example.com"
        msg_in["Message-ID"] = "<msg>"
        msg_in["Date"] = "Fri, 02 Nov 2012 16:07:54 +0000"
        msg_in.set_payload("Dummy message with email@address.com")
        add_to_list("list@example.com", msg_in)
        email = Email.objects.get(message_id="msg")
        msg = email.as_message()
        self.assertEqual(msg["From"], "dummy at example.com")
        self.assertEqual(msg["Message-ID"], "<msg>")
        self.assertEqual(msg["Date"], msg_in["Date"])
        self.assertTrue(msg.is_multipart())
        payload = msg.get_payload()
        self.assertEqual(len(payload), 1)
        self.assertEqual(
            payload[0].get_payload(decode=True),
            "Dummy message with email(a)address.com")

    def test_as_message_unicode(self):
        msg_in = Message()
        msg_in["From"] = "dummy@example.com"
        msg_in["Message-ID"] = "<msg>"
        msg_in.set_payload("Dummy message ünîcödé", "utf-8")
        add_to_list("list@example.com", msg_in)
        email = Email.objects.get(message_id="msg")
        msg = email.as_message()
        self.assertEqual(msg["From"], "dummy at example.com")
        self.assertEqual(msg["Message-ID"], "<msg>")
        self.assertTrue(msg.is_multipart())
        payload = msg.get_payload()
        self.assertEqual(len(payload), 1)
        payload = payload[0]
        self.assertEqual(
            payload["Content-Transfer-Encoding"], "quoted-printable")
        self.assertEqual(payload.get_charset(), "utf-8")
        self.assertEqual(
            payload.get_payload(decode=True).decode("utf-8"),
            "Dummy message ünîcödé")

    def test_as_message_attachments(self):
        msg_in = Message()
        msg_in["From"] = "dummy@example.com"
        msg_in["Message-ID"] = "<msg>"
        msg_in.attach(MIMEText("Dummy message"))
        msg_in.attach(MIMEText("<html><body>Dummy message</body></html>",
                               _subtype="html"))
        add_to_list("list@example.com", msg_in)
        email = Email.objects.get(message_id="msg")
        msg = email.as_message()
        self.assertEqual(msg["From"], "dummy at example.com")
        self.assertEqual(msg["Message-ID"], "<msg>")
        self.assertTrue(msg.is_multipart())
        payload = msg.get_payload()
        self.assertEqual(len(payload), 2)
        self.assertEqual(
            payload[0].get_payload(decode=True).strip(), "Dummy message")
        # The filename extension detection from content type is a bit random
        # (depends on the PYTHON_HASHSEED), make sure we get the right one
        # here for testing.
        expected_ext = guess_all_extensions("text/html", strict=False)[0]
        self.assertEqual(payload[1].get_content_type(), "text/html")
        self.assertEqual(
            payload[1]["Content-Disposition"],
            'attachment; filename="attachment%s"' % expected_ext)
        self.assertEqual(
            payload[1].get_payload(decode=True),
            "<html><body>Dummy message</body></html>")

    def test_as_message_timezone(self):
        msg_in = Message()
        msg_in["From"] = "dummy@example.com"
        msg_in["Message-ID"] = "<msg>"
        msg_in["Date"] = "Fri, 02 Nov 2012 16:07:54 +0400"
        msg_in.set_payload("Dummy message")
        add_to_list("list@example.com", msg_in)
        email = Email.objects.get(message_id="msg")
        msg = email.as_message()
        self.assertEqual(msg["Date"], msg_in["Date"])


class EmailSetParentTestCase(TestCase):

    def _create_tree(self, tree):
        emails = []
        for msgid in tree:
            msg = Message()
            msg["From"] = "sender@example.com"
            msg["Message-ID"] = "<%s>" % msgid
            parent_id = msgid.rpartition(".")[0]
            if Email.objects.filter(message_id=parent_id).exists():
                msg["In-Reply-To"] = "<%s>" % parent_id
            msg.set_payload("dummy message")
            add_to_list("example-list", msg)
            emails.append(Email.objects.get(message_id=msgid))
        return emails

    def test_simple(self):
        email1, email2 = self._create_tree(["msg1", "msg2"])
        email2.set_parent(email1)
        self.assertEqual(email2.parent_id, email1.id)
        self.assertEqual(email2.thread_id, email1.thread_id)
        self.assertEqual(Thread.objects.count(), 1)
        thread = Thread.objects.first()
        self.assertEqual(thread.id, email1.thread_id)
        self.assertEqual(thread.emails.count(), 2)
        self.assertEqual(
            list(thread.emails.order_by(
                "thread_order").values_list("message_id", flat=True)),
            ["msg1", "msg2"])
        self.assertEqual(thread.date_active, email2.date)

    def test_subthread(self):
        tree = ["msg1", "msg2", "msg2.1", "msg2.1.1", "msg2.1.1.1", "msg2.2"]
        emails = self._create_tree(tree)
        email1 = emails[0]
        email2 = emails[1]
        self.assertEqual(email2.thread.emails.count(), len(tree) - 1)
        email2.set_parent(email1)
        self.assertEqual(email2.parent_id, email1.id)
        self.assertEqual(email2.thread_id, email1.thread_id)
        self.assertEqual(Thread.objects.count(), 1)
        thread = Thread.objects.first()
        self.assertEqual(thread.id, email1.thread_id)
        self.assertEqual(thread.emails.count(), len(tree))
        for msgid in tree:
            email = Email.objects.get(message_id=msgid)
            self.assertEqual(email.thread_id, email1.thread_id)
        self.assertEqual(
            tree, list(thread.emails.order_by(
                "thread_order").values_list("message_id", flat=True)))

    def test_switch(self):
        email1, email2 = self._create_tree(["msg1", "msg1.1"])
        email1.set_parent(email2)
        self.assertEqual(email1.parent, email2)
        self.assertEqual(email2.parent, None)

    def test_attach_to_child(self):
        emails = self._create_tree(["msg1", "msg1.1", "msg1.1.1", "msg1.1.2"])
        emails[1].set_parent(emails[2])
        self.assertEqual(emails[2].parent_id, emails[0].id)
        self.assertEqual(list(emails[0].thread.emails.order_by(
            "thread_order").values_list("message_id", flat=True)),
            ["msg1", "msg1.1.1", "msg1.1", "msg1.1.2"])

    def test_attach_to_grandchild(self):
        emails = self._create_tree(
            ["msg1", "msg1.1", "msg1.1.1", "msg1.1.2", "msg1.1.1.1"])
        emails[1].set_parent(emails[-1])
        self.assertEqual(emails[-1].parent_id, emails[0].id)
        self.assertEqual(list(emails[0].thread.emails.order_by(
            "thread_order").values_list("message_id", flat=True)),
            ["msg1", "msg1.1.1.1", "msg1.1", "msg1.1.1", "msg1.1.2"])

    def test_attach_to_itself(self):
        email1 = self._create_tree(["msg1"])[0]
        self.assertRaises(ValueError, email1.set_parent, email1)
