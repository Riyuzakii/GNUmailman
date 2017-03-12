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

from datetime import datetime
from email.message import Message

from django.utils.timezone import utc
from django_mailman3.tests.utils import FakeMMList

from hyperkitty.lib.incoming import add_to_list
from hyperkitty.models import MailingList, Thread, ArchivePolicy
from hyperkitty.tests.utils import TestCase


class MailingListTestCase(TestCase):

    def setUp(self):
        self.ml = MailingList.objects.create(name="list@example.com")
        self.mailman_ml = FakeMMList("list@example.com")
        self.mailman_client.get_list.side_effect = lambda n: self.mailman_ml

    def test_update_from_mailman(self):
        self.ml.display_name = "original-value"
        self.ml.description = "original-value"
        self.ml.subject_prefix = "original-value"
        self.ml.created_at = datetime(2000, 1, 1, 0, 0, 0, tzinfo=utc)
        self.ml.archive_policy = ArchivePolicy.public.value
        self.ml.list_id = "original.value"
        self.ml.save()

        self.mailman_ml.display_name = "new-value"
        self.mailman_ml.list_id = "new.value"
        self.mailman_ml.settings["description"] = "new-value"
        self.mailman_ml.settings["subject_prefix"] = "new-value"
        self.mailman_ml.settings["archive_policy"] = "private"
        new_date = datetime(2010, 12, 31, 0, 0, 0, tzinfo=utc)
        self.mailman_ml.settings["created_at"] = new_date.isoformat()

        self.ml.update_from_mailman()
        self.assertEqual(self.ml.display_name, "new-value")
        self.assertEqual(self.ml.description, "new-value")
        self.assertEqual(self.ml.subject_prefix, "new-value")
        self.assertEqual(self.ml.created_at, new_date)
        self.assertEqual(self.ml.archive_policy, ArchivePolicy.private.value)
        self.assertEqual(self.ml.list_id, "new.value")

    def test_update_from_mailman_naive(self):
        self.ml.created_at = datetime(2000, 1, 1, 0, 0, 0, tzinfo=utc)
        self.ml.save()
        new_date = datetime(2010, 12, 31, 0, 0, 0, tzinfo=None)
        self.mailman_ml.settings["created_at"] = new_date.isoformat()
        self.ml.update_from_mailman()
        self.assertTrue(self.ml.created_at.tzinfo is not None)
        self.assertEqual(self.ml.created_at, new_date.replace(tzinfo=utc))

    def test_get_threads_between(self):
        # the get_threads_between method should return all threads that have
        # been active between the two specified dates, including the threads
        # started in between those dates but updated later
        msg1 = Message()
        msg1["From"] = "sender1@example.com"
        msg1["Message-ID"] = "<msg1>"
        msg1["Date"] = "2015-02-15 00:00:00 UTC"
        msg1.set_payload("message 1")
        add_to_list(self.ml.name, msg1)
        # The thread started in Feb, it should show up in the Feb threads but
        # not in the January or March threads.
        self.assertEqual(Thread.objects.count(), 1)
        jan_threads = self.ml.get_threads_between(
            datetime(2015, 1, 1, 0, 0, 0, tzinfo=utc),
            datetime(2015, 1, 31, 0, 0, 0, tzinfo=utc),
            )
        self.assertEqual(jan_threads.count(), 0)
        feb_threads = self.ml.get_threads_between(
            datetime(2015, 2, 1, 0, 0, 0, tzinfo=utc),
            datetime(2015, 2, 28, 0, 0, 0, tzinfo=utc),
            )
        self.assertEqual(feb_threads.count(), 1)
        march_threads = self.ml.get_threads_between(
            datetime(2015, 3, 1, 0, 0, 0, tzinfo=utc),
            datetime(2015, 3, 31, 0, 0, 0, tzinfo=utc),
            )
        self.assertEqual(march_threads.count(), 0)

    def test_get_threads_between_across_months(self):
        # the get_threads_between method should return all threads that have
        # been active between the two specified dates, including the threads
        # started in between those dates but updated later
        msg1 = Message()
        msg1["From"] = "sender1@example.com"
        msg1["Message-ID"] = "<msg1>"
        msg1["Date"] = "2015-02-15 00:00:00 UTC"
        msg1.set_payload("message 1")
        add_to_list(self.ml.name, msg1)
        msg2 = Message()
        msg2["From"] = "sender2@example.com"
        msg2["Message-ID"] = "<msg2>"
        msg2["In-Reply-To"] = "<msg1>"
        msg2["Date"] = "2015-03-15 00:00:00 UTC"
        msg2.set_payload("message 2")
        add_to_list(self.ml.name, msg2)
        # The thread started in Feb, was updated in March. It should show up in
        # both the Feb threads and the March threads.
        self.assertEqual(Thread.objects.count(), 1)
        feb_threads = self.ml.get_threads_between(
            datetime(2015, 2, 1, 0, 0, 0, tzinfo=utc),
            datetime(2015, 2, 28, 0, 0, 0, tzinfo=utc),
            )
        self.assertEqual(feb_threads.count(), 1)
        march_threads = self.ml.get_threads_between(
            datetime(2015, 3, 1, 0, 0, 0, tzinfo=utc),
            datetime(2015, 3, 31, 0, 0, 0, tzinfo=utc),
            )
        self.assertEqual(march_threads.count(), 1)

    def test_get_threads_between_across_two_months(self):
        # the get_threads_between method should return all threads that have
        # been active between the two specified dates, including the threads
        # started in between those dates but updated later
        msg1 = Message()
        msg1["From"] = "sender1@example.com"
        msg1["Message-ID"] = "<msg1>"
        msg1["Date"] = "2015-01-15 00:00:00 UTC"
        msg1.set_payload("message 1")
        add_to_list(self.ml.name, msg1)
        msg2 = Message()
        msg2["From"] = "sender2@example.com"
        msg2["Message-ID"] = "<msg2>"
        msg2["In-Reply-To"] = "<msg1>"
        msg2["Date"] = "2015-03-15 00:00:00 UTC"
        msg2.set_payload("message 2")
        add_to_list(self.ml.name, msg2)
        # The thread started in Jan, was updated in March. It should show up in
        # the Jan, Feb and March threads.
        self.assertEqual(Thread.objects.count(), 1)
        jan_threads = self.ml.get_threads_between(
            datetime(2015, 1, 1, 0, 0, 0, tzinfo=utc),
            datetime(2015, 1, 31, 0, 0, 0, tzinfo=utc),
            )
        self.assertEqual(jan_threads.count(), 1)
        feb_threads = self.ml.get_threads_between(
            datetime(2015, 2, 1, 0, 0, 0, tzinfo=utc),
            datetime(2015, 2, 28, 0, 0, 0, tzinfo=utc),
            )
        self.assertEqual(feb_threads.count(), 1)
        march_threads = self.ml.get_threads_between(
            datetime(2015, 3, 1, 0, 0, 0, tzinfo=utc),
            datetime(2015, 3, 31, 0, 0, 0, tzinfo=utc),
            )
        self.assertEqual(march_threads.count(), 1)
