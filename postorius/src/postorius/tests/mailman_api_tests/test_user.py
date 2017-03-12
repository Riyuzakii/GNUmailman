# -*- coding: utf-8 -*-
# Copyright (C) 2016 by the Free Software Foundation, Inc.
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
from django.test.utils import override_settings
from mock import patch

from postorius.models import MailmanUser, Mailman404Error
from postorius.tests.utils import ViewTestCase
from postorius.forms import UserPreferences, ChangeSubscriptionForm


class MailmanUserTest(ViewTestCase):
    """
    Tests for the mailman user preferences settings page.
    """

    def setUp(self):
        super(MailmanUserTest, self).setUp()
        self.domain = self.mm_client.create_domain('example.com')
        self.foo_list = self.domain.create_list('foo')
        self.user = User.objects.create_user(
            'user', 'user@example.com', 'testpass')
        EmailAddress.objects.create(
            user=self.user, email=self.user.email, verified=True)
        self.mm_user = MailmanUser.objects.create_from_django(self.user)

    def test_address_preferences_not_logged_in(self):
        self.assertRedirectsToLogin(reverse('user_address_preferences'))

    def test_subscriptions_not_logged_in(self):
        self.assertRedirectsToLogin(reverse('ps_user_profile'))

    def test_subscriptions_logged_in(self):
        self.client.login(username='user', password='testpass')
        response = self.client.get(reverse('ps_user_profile'))
        self.assertEquals(response.status_code, 200)

    def test_address_based_preferences(self):
        self.client.login(username='user', password='testpass')
        self.mm_user.add_address('user2@example.com')
        self.mm_user.add_address('user3@example.com')
        response = self.client.get(reverse('user_address_preferences'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["formset"]), 3)

    def test_preferences_none(self):
        # Mailman does not accept None values for boolean preferences. When
        # those preferences are unset, they must be excluded from the POST
        # data.
        self.client.login(username='user', password='testpass')
        self.foo_list.subscribe(self.user.email, pre_verified=True,
                                pre_confirmed=True, pre_approved=True)
        prefs_with_none = (
            'receive_own_postings', 'acknowledge_posts',
            'hide_address', 'receive_list_copy',
            )
        # Prepare a Preferences subclass that will check the POST data
        import mailmanclient._client

        class TestingPrefs(mailmanclient._client.Preferences):
            testcase = self

            def save(self):
                for pref in prefs_with_none:
                    self.testcase.assertNotIn(pref, self._changed_rest_data)
        # Now check the relevant URLs
        with patch('mailmanclient._client.Preferences') as pref_class:
            pref_class.side_effect = TestingPrefs
            # Simple forms
            for url in (
                    reverse('user_mailmansettings'),
                    reverse('user_list_options', args=[self.foo_list.list_id]),
                    ):
                response = self.client.post(
                    url, dict((pref, None) for pref in prefs_with_none))
                self.assertEqual(response.status_code, 302)
            # Formsets
            for url in ('user_address_preferences',
                        'user_subscription_preferences'):
                url = reverse(url)
                post_data = dict(
                    ('form-0-%s' % pref, None)
                    for pref in prefs_with_none)
                post_data.update({
                    'form-TOTAL_FORMS': '1',
                    'form-INITIAL_FORMS': '0',
                    'form-MAX_NUM_FORMS': ''
                })
                response = self.client.post(url, post_data)
                self.assertEqual(response.status_code, 302)

    @override_settings(AUTOCREATE_MAILMAN_USER=False)
    def test_subscriptions_no_mailman_user(self):
        # Existing Django users without a corresponding Mailman user must not
        # cause views to crash.
        user = User.objects.create_user(
            'old-user', 'old-user@example.com', 'testpass')
        EmailAddress.objects.create(
            user=user, email=user.email, verified=True)
        self.client.login(username='old-user', password='testpass')
        self.assertRaises(Mailman404Error, MailmanUser.objects.get,
                          address=user.email)
        response = self.client.get(reverse('ps_user_profile'))
        self.assertEqual(response.status_code, 200)
        # The Mailman user must have been created
        self.assertIsNotNone(MailmanUser.objects.get(address=user.email))

    def test_presence_of_form_in_user_global_settings(self):
        self.client.login(username='user', password='testpass')
        response = self.client.get(reverse('user_mailmansettings'))
        self.assertEquals(response.status_code, 200)
        self.assertIsInstance(response.context['form'], UserPreferences)

    def test_presence_of_form_in_user_subscription_preferences(self):
        self.client.login(username='user', password='testpass')
        self.foo_list.subscribe(self.user.email, pre_verified=True,
                                pre_confirmed=True, pre_approved=True)
        response = self.client.get(reverse('user_subscription_preferences'))
        self.assertEquals(response.status_code, 200)
        self.assertIsNotNone(response.context['formset'])
        self.assertEquals(len(response.context['formset']), 1)

    def test_presence_of_form_in_user_list_options(self):
        self.client.login(username='user', password='testpass')
        self.foo_list.subscribe(self.user.email, pre_verified=True,
                                pre_confirmed=True, pre_approved=True)
        response = self.client.get(reverse('user_list_options',
                                           args=[self.foo_list.list_id]))
        self.assertEquals(response.status_code, 200)
        self.assertIsInstance(response.context['form'],
                              UserPreferences)
        self.assertIsInstance(response.context['change_subscription_form'],
                              ChangeSubscriptionForm)

    def test_list_options_shows_all_addresses(self):
        self.client.login(username='user', password='testpass')
        self.foo_list.subscribe(self.user.email, pre_verified=True,
                                pre_confirmed=True, pre_approved=True)
        # Add another email
        EmailAddress.objects.create(
            user=self.user, email='anotheremail@example.com', verified=True)
        user = self.mm_client.get_user('user@example.com')
        address = user.add_address('anotheremail@example.com')
        address.verify()
        # Check response
        response = self.client.get(reverse('user_list_options',
                                           args=[self.foo_list.list_id]))
        self.assertEquals(response.status_code, 200)
        self.assertTrue('anotheremail@example.com' in response.content)
