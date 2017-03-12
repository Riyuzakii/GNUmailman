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
from mock import patch

from postorius.tests.utils import ViewTestCase


class TestSubscription(ViewTestCase):
    """Tests subscription to lists"""

    def setUp(self):
        super(TestSubscription, self).setUp()
        self.domain = self.mm_client.create_domain('example.com')
        self.open_list = self.domain.create_list('open_list')
        # Set subscription policy to open
        settings = self.open_list.settings
        settings['subscription_policy'] = 'open'
        settings.save()
        self.mod_list = self.domain.create_list('moderate_subs')
        # Set subscription policy to moderate
        settings = self.mod_list.settings
        settings['subscription_policy'] = 'moderate'
        settings.save()
        # Create django user.
        self.user = User.objects.create_user(
            'testuser', 'test@example.com', 'pwd')
        EmailAddress.objects.create(
            user=self.user, email=self.user.email, verified=True)
        EmailAddress.objects.create(
            user=self.user, email='fritz@example.org', verified=True)
        # Create Mailman user
        self.mm_user = self.mm_client.create_user('test@example.com', '')
        self.mm_user.add_address('fritz@example.org')
        for address in self.mm_user.addresses:
            address.verify()

    @patch('mailmanclient._client.MailingList.subscribe')
    def test_anonymous_subscribe(self, mock_subscribe):
        response = self.client.post(
            reverse('list_anonymous_subscribe',
                    args=('open_list.example.com', )),
            {'email': 'test@example.com'})
        mock_subscribe.assert_called_once()
        mock_subscribe.assert_called_with(
            'test@example.com', pre_verified=False, pre_confirmed=False)
        self.assertRedirects(
            response, reverse('list_summary',
                              args=('open_list.example.com', )))
        self.assertHasSuccessMessage(response)

    def test_subscribe_open(self):
        # The subscription goes straight through.
        self.client.login(username='testuser', password='pwd')
        response = self.client.post(
            reverse('list_subscribe', args=('open_list.example.com', )),
            {'email': 'test@example.com'})
        self.assertEqual(len(self.open_list.members), 1)
        self.assertEqual(len(self.open_list.requests), 0)
        self.assertRedirects(
            response, reverse('list_summary',
                              args=('open_list.example.com', )))
        self.assertHasSuccessMessage(response)

    def test_secondary_open(self):
        # Subscribe with a secondary email address
        self.client.login(username='testuser', password='pwd')
        response = self.client.post(
            reverse('list_subscribe', args=('open_list.example.com', )),
            {'email': 'fritz@example.org'})
        self.assertEqual(len(self.open_list.members), 1)
        self.assertEqual(len(self.open_list.requests), 0)
        self.assertRedirects(
            response, reverse('list_summary',
                              args=('open_list.example.com', )))
        self.assertHasSuccessMessage(response)

    def test_unknown_address(self):
        # Impossible to register with an unknown address
        self.client.login(username='testuser', password='pwd')
        response = self.client.post(
            reverse('list_subscribe', args=('open_list.example.com', )),
            {'email': 'unknown@example.org'})
        self.assertEqual(len(self.open_list.members), 0)
        self.assertEqual(len(self.open_list.requests), 0)
        self.assertRedirects(
            response, reverse('list_summary',
                              args=('open_list.example.com', )))
        self.assertHasErrorMessage(response)

    def test_banned_address(self):
        # Impossible to register with a banned address
        self.client.login(username='testuser', password='pwd')
        self.open_list.bans.add('test@example.com')
        response = self.client.post(
            reverse('list_subscribe', args=('open_list.example.com', )),
            {'email': 'test@example.com'})
        self.assertEqual(len(self.open_list.members), 0)
        self.assertEqual(len(self.open_list.requests), 0)
        self.assertRedirects(
            response, reverse('list_summary',
                              args=('open_list.example.com', )))
        self.assertHasErrorMessage(response)

    def test_subscribe_mod(self):
        # The subscription is held for approval.
        self.client.login(username='testuser', password='pwd')
        response = self.client.post(
            reverse('list_subscribe', args=('moderate_subs.example.com', )),
            {'email': 'test@example.com'})
        self.assertEqual(len(self.mod_list.members), 0)
        self.assertEqual(len(self.mod_list.requests), 1)
        self.assertRedirects(
            response, reverse('list_summary',
                              args=('moderate_subs.example.com', )))
        self.assertHasSuccessMessage(response)

    def test_secondary_mod(self):
        # Subscribe with a secondary email address
        self.client.login(username='testuser', password='pwd')
        response = self.client.post(
            reverse('list_subscribe', args=('moderate_subs.example.com', )),
            {'email': 'fritz@example.org'})
        self.assertEqual(len(self.mod_list.members), 0)
        self.assertEqual(len(self.mod_list.requests), 1)
        self.assertRedirects(
            response, reverse('list_summary',
                              args=('moderate_subs.example.com', )))
        self.assertHasSuccessMessage(response)

    def test_subscribe_already_pending(self):
        # The user tries to subscribe twice on a moderated list.
        self.client.login(username='testuser', password='pwd')
        response = self.client.post(
            reverse('list_subscribe', args=('moderate_subs.example.com', )),
            {'email': 'test@example.com'})
        self.assertEqual(len(self.mod_list.members), 0)
        self.assertEqual(len(self.mod_list.requests), 1)
        self.assertHasSuccessMessage(response)
        # Try to subscribe a second time.
        response = self.client.post(
            reverse('list_subscribe', args=('moderate_subs.example.com', )),
            {'email': 'test@example.com'})
        self.assertEqual(len(self.mod_list.members), 0)
        self.assertEqual(len(self.mod_list.requests), 1)
        message = self.assertHasErrorMessage(response)
        self.assertIn('Subscription request already pending', message)

    def test_subscribe_with_name(self):
        owner = User.objects.create_user(
            'testowner', 'owner@example.com', 'pwd')
        EmailAddress.objects.create(
            user=owner, email=owner.email, verified=True)
        self.open_list.add_owner('owner@example.com')
        self.client.login(username='testowner', password='pwd')
        email_list = """First Person <test-1@example.org>\n
                        "Second Person" <test-2@example.org>\n
                        test-3@example.org (Third Person)\n
                        test-4@example.org\n
                        <test-5@example.org>\n"""
        self.client.post(
            reverse('mass_subscribe', args=('open_list.example.com',)),
            {'emails': email_list})
        self.assertEqual(len(self.open_list.members), 5)
        first = self.open_list.get_member('test-1@example.org')
        second = self.open_list.get_member('test-2@example.org')
        third = self.open_list.get_member('test-3@example.org')
        fourth = self.open_list.get_member('test-4@example.org')
        fifth = self.open_list.get_member('test-5@example.org')
        self.assertEqual(first.address.display_name, 'First Person')
        self.assertEqual(second.address.display_name, 'Second Person')
        self.assertEqual(third.address.display_name, 'Third Person')
        self.assertIsNone(fourth.address.display_name)
        self.assertIsNone(fifth.address.display_name)

    def test_change_subscription_open(self):
        # The subscription is changed from an address to another
        self.open_list.subscribe('test@example.com')
        self.assertEqual(len(self.open_list.members), 1)
        self.assertEqual(len(self.open_list.requests), 0)
        self.client.login(username='testuser', password='pwd')
        response = self.client.post(
            reverse('change_subscription', args=['open_list.example.com']),
            {'email': 'fritz@example.org'})
        self.assertHasSuccessMessage(response)
        self.assertEqual(len(self.open_list.members), 1)
        self.assertEqual(len(self.open_list.requests), 0)
        try:
            member = self.open_list.get_member('fritz@example.org')
        except ValueError:
            self.fail('The subscription was not changed')
        self.assertEqual(member.email, 'fritz@example.org')
        self.assertRedirects(
            response, reverse('list_summary',
                              args=('open_list.example.com', )))

    def test_change_subscription_confirm(self):
        # The subscription is changed from an address to another
        confirm_list = self.domain.create_list('confirm_list')
        settings = confirm_list.settings
        settings['subscription_policy'] = 'confirm'
        settings.save()
        confirm_list.subscribe('test@example.com', pre_confirmed=True)
        self.assertEqual(len(confirm_list.members), 1)
        self.assertEqual(len(confirm_list.requests), 0)
        self.client.login(username='testuser', password='pwd')
        response = self.client.post(
            reverse('change_subscription', args=['confirm_list.example.com']),
            {'email': 'fritz@example.org'})
        self.assertHasSuccessMessage(response)
        self.assertEqual(len(confirm_list.members), 1)
        self.assertEqual(len(confirm_list.requests), 0)
        try:
            member = confirm_list.get_member('fritz@example.org')
        except ValueError:
            self.fail('The subscription was not changed')
        self.assertEqual(member.email, 'fritz@example.org')
        self.assertRedirects(
            response, reverse('list_summary',
                              args=('confirm_list.example.com', )))
