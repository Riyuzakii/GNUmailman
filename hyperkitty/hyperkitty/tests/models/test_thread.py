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

import string
import random
from email.message import Message

from hyperkitty.lib.incoming import add_to_list
from hyperkitty.models.email import Email
from hyperkitty.models.mailinglist import MailingList
from hyperkitty.models.thread import Thread
from hyperkitty.tests.utils import TestCase


class ThreadTestCase(TestCase):

    def test_starting_message_1(self):
        # A basic thread: msg2 replies to msg1
        msg1 = Message()
        msg1["From"] = "sender1@example.com"
        msg1["Message-ID"] = "<msg1>"
        msg1.set_payload("message 1")
        add_to_list("example-list", msg1)
        msg2 = Message()
        msg2["From"] = "sender2@example.com"
        msg2["Message-ID"] = "<msg2>"
        msg2.set_payload("message 2")
        msg2["In-Reply-To"] = msg1["Message-ID"]
        add_to_list("example-list", msg2)
        self.assertEqual(Thread.objects.count(), 1)
        thread = Thread.objects.all()[0]
        self.assertEqual(thread.starting_email.message_id, "msg1")

    def test_starting_message_2(self):
        # A partially-imported thread: msg1 replies to something we don't have
        msg1 = Message()
        msg1["From"] = "sender1@example.com"
        msg1["Message-ID"] = "<msg1>"
        msg1["In-Reply-To"] = "<msg0>"
        msg1.set_payload("message 1")
        add_to_list("example-list", msg1)
        msg2 = Message()
        msg2["From"] = "sender2@example.com"
        msg2["Message-ID"] = "<msg2>"
        msg2["In-Reply-To"] = msg1["Message-ID"]
        msg2.set_payload("message 2")
        add_to_list("example-list", msg2)
        self.assertEqual(Thread.objects.count(), 1)
        thread = Thread.objects.all()[0]
        self.assertEqual(thread.starting_email.message_id, "msg1")

    def test_starting_message_3(self):
        # A thread where the reply has an anterior date to the first email
        # (the In-Reply-To header must win over the date sort)
        msg1 = Message()
        msg1["From"] = "sender1@example.com"
        msg1["Message-ID"] = "<msg1>"
        msg1["Date"] = "Fri, 02 Nov 2012 16:07:54 +0000"
        msg1.set_payload("message 1")
        add_to_list("example-list", msg1)
        msg2 = Message()
        msg2["From"] = "sender2@example.com"
        msg2["Message-ID"] = "<msg2>"
        msg2["Date"] = "Fri, 01 Nov 2012 16:07:54 +0000"
        msg2.set_payload("message 2")
        msg2["In-Reply-To"] = msg1["Message-ID"]
        add_to_list("example-list", msg2)
        self.assertEqual(Thread.objects.count(), 1)
        thread = Thread.objects.all()[0]
        self.assertEqual(thread.starting_email.message_id, "msg1")

    def test_subject(self):
        msg = Message()
        msg["From"] = "sender@example.com"
        msg["Message-ID"] = "<dummymsg>"
        msg["Date"] = "Fri, 02 Nov 2012 16:07:54 +0000"
        msg["Subject"] = "Dummy subject"
        msg.set_payload("Dummy message")
        add_to_list("example-list", msg)
        self.assertEqual(Thread.objects.count(), 1)
        thread = Thread.objects.all()[0]
        self.assertEqual(thread.subject, "Dummy subject")

    def test_thread_no_email(self):
        mlist = MailingList.objects.create(name="example-list")
        Thread.objects.create(mailinglist=mlist, thread_id="<msg1>")

    def test_long_subject(self):
        # PostgreSQL will raise an OperationalError if the subject's index is
        # longer than 2712, but SQLite will accept anything, so we must test
        # with assertions here.
        # We use random chars to build the subject, if we use a single repeated
        # char, the index will never be big enough.
        subject = [random.choice(string.letters + string.digits + " ")
                   for i_ in range(3000)]
        subject = "".join(subject)
        msg = Message()
        msg["From"] = "sender@example.com"
        msg["Message-ID"] = "<dummymsg>"
        msg["Date"] = "Fri, 02 Nov 2012 16:07:54 +0000"
        msg["Subject"] = subject
        msg.set_payload("Dummy message")
        add_to_list("example-list", msg)
        self.assertEqual(Email.objects.count(), 1)
        msg_db = Email.objects.all()[0]
        self.assertTrue(
            len(msg_db.subject) < 2712,
            "Very long subjects are not trimmed")
