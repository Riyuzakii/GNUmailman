# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 by the Free Software Foundation, Inc.
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

from django.core.urlresolvers import reverse
from django.contrib.sites.models import Site
from django_mailman3.models import MailDomain
from hyperkitty.tests.utils import TestCase
from hyperkitty.views.mailman import _get_url


class PrivateListTestCase(TestCase):

    def test_get_url_no_msgid(self):
        self.assertEqual(
            _get_url("test@example.com"),
            "https://example.com" +
            reverse('hk_list_overview', args=["test@example.com"]))

    def test_get_url_default_domain(self):
        self.assertEqual(
            _get_url("test@example.com", "<message-id>"),
            "https://example.com" + reverse('hk_message_index', kwargs={
                "mlist_fqdn": "test@example.com",
                "message_id_hash": "3F32NJAOW2XVHJWKZ73T2EPICEIAB3LI"
            }))

    def test_get_url_with_domain(self):
        site = Site.objects.create(name="Example", domain="lists.example.org")
        MailDomain.objects.create(site=site, mail_domain="example.com")
        self.assertEqual(
            _get_url("test@example.com", "<message-id>"),
            "https://lists.example.org" + reverse('hk_message_index', kwargs={
                "mlist_fqdn": "test@example.com",
                "message_id_hash": "3F32NJAOW2XVHJWKZ73T2EPICEIAB3LI"
            }))
