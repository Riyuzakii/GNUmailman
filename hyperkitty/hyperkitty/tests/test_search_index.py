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

from email.message import Message

from django.apps import apps
from haystack.query import SearchQuerySet

from hyperkitty.models import Email
from hyperkitty.lib.incoming import add_to_list
from hyperkitty.search_indexes import update_index
from hyperkitty.tests.utils import SearchEnabledTestCase


class SearchIndexTestCase(SearchEnabledTestCase):

    def setUp(self):
        # Disable automatic update
        apps.get_app_config('haystack').signal_processor.teardown()

    def tearDown(self):
        # Restore automatic update
        apps.get_app_config('haystack').signal_processor.setup()

    def _add_message(self, msgid="msg"):
        msg = Message()
        msg["From"] = "Dummy Sender <dummy@example.com>"
        msg["Message-ID"] = "<%s>" % msgid
        msg["Subject"] = "Dummy message"
        msg.set_payload("Dummy content with keyword")
        return add_to_list("list@example.com", msg)

    def test_update_index(self):
        self._add_message()
        self.assertEqual(SearchQuerySet().count(), 0)
        # Update the index
        update_index()
        self.assertEqual(SearchQuerySet().count(), 1)

    def test_update_index_with_remove(self):
        self._add_message()
        self._add_message("msgid2")
        self.assertEqual(SearchQuerySet().count(), 0)
        # Update the index
        update_index()
        self.assertEqual(SearchQuerySet().count(), 2)
        # Delete the second email
        Email.objects.get(message_id="msgid2").delete()
        # Update the index with the remove option
        update_index(remove=True)
        self.assertEqual(SearchQuerySet().count(), 1)
