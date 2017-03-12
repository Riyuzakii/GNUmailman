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
from hyperkitty.models.thread import Thread, LastView
from hyperkitty.tests.utils import TestCase


class LastViewTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create(username="dummy")
        msg = Message()
        msg["From"] = "sender1@example.com"
        msg["Message-ID"] = "<msg>"
        msg.set_payload("message")
        add_to_list("example-list", msg)
        self.thread = Thread.objects.all()[0]

    def test_duplicate(self):
        # There's some sort of race condition that can lead to duplicate
        # LastView objects being created. Make sure we can handle it.
        LastView.objects.create(thread=self.thread, user=self.user)
        LastView.objects.create(thread=self.thread, user=self.user)
        self.assertFalse(self.thread.is_unread_by(self.user))
        self.assertEqual(LastView.objects.count(), 1)
