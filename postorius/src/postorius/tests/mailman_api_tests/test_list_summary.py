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

from postorius.tests.utils import ViewTestCase
from postorius.forms import ListAnonymousSubscribe


class ListSummaryPageTest(ViewTestCase):
    """Tests for the list summary page.

    Tests accessiblity and existince of the submit form depending on
    login status.
    """

    def setUp(self):
        super(ListSummaryPageTest, self).setUp()
        self.domain = self.mm_client.create_domain('example.com')
        self.foo_list = self.domain.create_list('foo')
        self.user = User.objects.create_user(
            'testuser', 'test@example.com', 'testpass')
        EmailAddress.objects.create(
            user=self.user, email=self.user.email, verified=True)

    def test_list_summary_logged_out(self):
        # Response must contain list obj and anonymous subscribe form.
        response = self.client.get(reverse('list_summary',
                                   args=('foo@example.com', )))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['list'].fqdn_listname,
                         'foo@example.com')
        self.assertIsInstance(response.context['anonymous_subscription_form'],
                              ListAnonymousSubscribe)
        self.assertContains(response, '<form ')

    def test_list_summary_logged_in(self):
        # Response must contain list obj and the form.
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('list_summary',
                                   args=('foo@example.com', )))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<form ')
        self.assertContains(response, 'Subscribe')

    def test_pending_subscription_request(self):
        mlist = self.mm_client.get_list('foo@example.com')
        mlist.settings['subscription_policy'] = 'moderate'
        mlist.settings.save()
        mlist.subscribe('test@example.com',
                        pre_verified=True,
                        pre_confirmed=True)
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('list_summary',
                                           args=('foo@example.com', )))
        self.assertEqual(response.status_code, 200)
        self.assertTrue('You have a subscription request pending. '
                        'If you don\'t hear back soon, '
                        'please contact the list owners.' in response.content)
        self.assertNotContains(response, 'Unsubscribe')
        self.assertNotContains(response, 'Subscribe')

    def test_unsubscribe_button_is_available(self):
        mlist = self.mm_client.get_list('foo@example.com')
        mlist.subscribe('test@example.com',
                        pre_verified=True,
                        pre_confirmed=True)
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('list_summary',
                                           args=('foo@example.com', )))
        self.assertEqual(response.status_code, 200)
        self.assertTrue('Unsubscribe' in response.content)

    def test_list_summary_owner(self):
        # Response must contain the administration menu
        self.mm_client.create_user('test@example.com', None)
        mlist = self.mm_client.get_list('foo@example.com')
        mlist.add_owner('test@example.com')
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('list_summary',
                                   args=('foo@example.com', )))
        self.assertContains(response, 'Delete list</a>')

    def test_list_summary_moderator(self):
        # Response must contain the administration menu
        self.mm_client.create_user('test@example.com', None)
        mlist = self.mm_client.get_list('foo@example.com')
        mlist.add_moderator('test@example.com')
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('list_summary',
                                   args=('foo@example.com', )))
        self.assertContains(response, 'Held messages</a>')
        self.assertNotContains(response, 'Delete list</a>')

    def test_list_summary_is_admin_secondary_owner(self):
        # Response must contain the administration menu
        EmailAddress.objects.create(
            user=self.user, email='anotheremail@example.com', verified=True)
        user = self.mm_client.create_user('test@example.com', None)
        address = user.add_address('anotheremail@example.com')
        address.verify()
        mlist = self.mm_client.get_list('foo@example.com')
        mlist.add_owner('anotheremail@example.com')
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('list_summary',
                                   args=('foo@example.com', )))
        self.assertContains(response, 'Delete list</a>')

    def test_list_summary_is_admin_secondary_moderator(self):
        # Response must contain the administration menu
        EmailAddress.objects.create(
            user=self.user, email='anotheremail@example.com', verified=True)
        user = self.mm_client.create_user('test@example.com', None)
        address = user.add_address('anotheremail@example.com')
        address.verify()
        mlist = self.mm_client.get_list('foo@example.com')
        mlist.add_moderator('anotheremail@example.com')
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('list_summary',
                                   args=('foo@example.com', )))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Held messages</a>')
        self.assertNotContains(response, 'Delete list</a>')

    def test_metrics_not_displayed_to_anonymous(self):
        response = self.client.get(reverse('list_summary',
                                           args=('foo@example.com',)))
        self.assertNotContains(response, 'List metrics')

    def test_list_metrics_not_displayed_to_moderator(self):
        mlist = self.mm_client.get_list('foo@example.com')
        mlist.add_moderator('test@example.com')
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('list_summary',
                                           args=('foo@example.com',)))
        self.assertNotContains(response, 'List metrics')

    def test_list_metrics_displayed_to_owner(self):
        mlist = self.mm_client.get_list('foo@example.com')
        mlist.add_owner('test@example.com')
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('list_summary',
                                           args=('foo@example.com',)))
        self.assertContains(response, 'List metrics')

    def test_list_metrics_displayed_to_superuser(self):
        user = User.objects.create_superuser(
            'testadminuser', 'testadmin@example.com', 'testpass')
        EmailAddress.objects.create(
            user=user, email=user.email, verified=True)
        self.assertTrue(self.client.login(username='testadminuser',
                                          password='testpass'))
        response = self.client.get(reverse('list_summary',
                                           args=('foo@example.com',)))
        self.assertContains(response, 'List metrics')
