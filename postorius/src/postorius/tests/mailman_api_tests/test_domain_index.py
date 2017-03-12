# -*- coding: utf-8 -*-
# Copyright (C) 2012-2015 by the Free Software Foundation, Inc.
#
# This file is part of Postorius.
#
# Postorius is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
# Postorius is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# Postorius.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import, print_function, unicode_literals

from allauth.account.models import EmailAddress
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django_mailman3.models import MailDomain
from django.utils.six.moves.urllib.error import HTTPError

from postorius.tests.utils import ViewTestCase


class DomainIndexPageTest(ViewTestCase):
    """Tests for the list index page."""

    def setUp(self):
        super(DomainIndexPageTest, self).setUp()
        self.domain = self.mm_client.create_domain('example.com')
        try:
            self.foo_list = self.domain.create_list('foo')
        except HTTPError:
            self.foo_list = self.mm_client.get_list('foo.example.com')

        self.user = User.objects.create_user(
            'testuser', 'test@example.com', 'testpass')
        self.superuser = User.objects.create_superuser(
            'testsu', 'su@example.com', 'testpass')
        self.owner = User.objects.create_user(
            'testowner', 'owner@example.com', 'testpass')
        self.moderator = User.objects.create_user(
            'testmoderator', 'moderator@example.com', 'testpass')
        for user in (self.user, self.superuser, self.owner, self.moderator):
            EmailAddress.objects.create(
                user=user, email=user.email, verified=True)
        self.foo_list.add_owner('owner@example.com')
        self.foo_list.add_moderator('moderator@example.com')

    def test_domain_index_not_accessible_to_public(self):
        response = self.client.get(reverse('domain_index'))
        self.assertEqual(response.status_code, 302)

    def test_domain_index_not_accessible_to_unpriveleged_user(self):
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('domain_index'))
        self.assertEqual(response.status_code, 403)

    def test_domain_index_not_accessible_to_moderators(self):
        self.client.login(username='testmoderator', password='testpass')
        response = self.client.get(reverse('domain_index'))
        self.assertEqual(response.status_code, 403)

    def test_domain_index_not_accessible_to_owners(self):
        self.client.login(username='testowner', password='testpass')
        response = self.client.get(reverse('domain_index'))
        self.assertEqual(response.status_code, 403)

    def test_contains_domains_and_site(self):
        # The list index page should contain the lists
        self.client.login(username='testsu', password='testpass')
        response = self.client.get(reverse('domain_index'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['domains']), 1)
        self.assertContains(response, 'example.com')
        self.assertTrue(
            MailDomain.objects.filter(mail_domain='example.com').exists())
