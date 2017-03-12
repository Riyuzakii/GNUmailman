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
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django_mailman3.models import MailDomain

from postorius.tests.utils import ViewTestCase


class DomainCreationTest(ViewTestCase):
    """Tests for the new list page."""

    def setUp(self):
        super(DomainCreationTest, self).setUp()
        self.user = User.objects.create_user('user', 'user@example.com', 'pwd')
        self.superuser = User.objects.create_superuser('su', 'su@example.com',
                                                       'pwd')
        for user in (self.user, self.superuser):
            EmailAddress.objects.create(
                user=user, email=user.email, verified=True)

    def test_permission_denied(self):
        self.client.login(username='user', password='pwd')
        response = self.client.get(reverse('domain_new'))
        self.assertEqual(response.status_code, 403)

    def test_new_domain_created_with_owner(self):
        self.client.login(username='su', password='pwd')
        post_data = {'mail_host': 'example.com',
                     'description': 'A new Domain.',
                     'site': '1',
                     }
        response = self.client.post(reverse('domain_new'), post_data)

        self.assertHasSuccessMessage(response)
        self.assertRedirects(response, reverse('domain_index'))

        a_new_domain = self.mm_client.get_domain('example.com')
        self.assertEqual(a_new_domain.mail_host, u'example.com')
        self.assertEqual(a_new_domain.owners[0]['user_id'],
                         self.mm_client.get_user('su@example.com').user_id)
        self.assertTrue(
            MailDomain.objects.filter(mail_domain='example.com').exists())
        a_new_domain.delete()

    def test_validation_of_mail_host(self):
        self.client.login(username='su', password='pwd')
        post_data = {'mail_host': 'example com',
                     'description': 'A new Domain',
                     'site': '1',
                     }
        response = self.client.post(reverse('domain_new'), post_data)
        self.assertContains(response, 'Please enter a valid domain name')
        # self.assertHasErrorMessage(response)
        self.assertEquals(response.status_code, 200)
