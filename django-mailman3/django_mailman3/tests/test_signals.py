# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 by the Free Software Foundation, Inc.
#
# This file is part of Django-Mailman.
#
# Django-Mailman is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# Django-Mailman is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# Django-Mailman.  If not, see <http://www.gnu.org/licenses/>.
#
# Author: Aurelien Bompard <abompard@fedoraproject.org>
#

from __future__ import absolute_import, print_function, unicode_literals

from allauth.account.models import EmailAddress
from allauth.account.signals import (
    email_confirmed, user_signed_up, user_logged_in, email_removed)
from allauth.socialaccount.models import SocialLogin
from allauth.socialaccount.signals import social_account_added
from django.contrib.auth.models import User
from mock import Mock, call, patch

from django_mailman3.models import Profile
from django_mailman3.tests.utils import TestCase


class SignalsTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            'testuser', 'test@example.com', 'testPass')

    def test_user_logged_in(self):
        Profile.objects.get(user=self.user).delete()
        with patch('django_mailman3.signals.sync_email_addresses') as sea:
            user_logged_in.send(sender=User, user=self.user)
        self.assertEqual(sea.call_args_list, [call(self.user)])
        self.assertTrue(Profile.objects.filter(user=self.user).exists())

    def test_user_signed_up(self):
        Profile.objects.get(user=self.user).delete()
        EmailAddress.objects.create(
            user=self.user, email=self.user.email, verified=True)
        EmailAddress.objects.create(
            user=self.user, email='another@example.com', verified=False)
        with patch('django_mailman3.signals.add_address_to_mailman_user') \
                as aatmu:
            user_signed_up.send(sender=User, user=self.user)
        self.assertEqual(
            aatmu.call_args_list, [call(self.user, self.user.email)])
        self.assertTrue(Profile.objects.filter(user=self.user).exists())

    def test_email_removed(self):
        address = EmailAddress.objects.create(
            user=self.user, email=self.user.email, verified=True)
        mm_user = Mock()
        with patch('django_mailman3.signals.get_mailman_user') as gmu:
            gmu.return_value = mm_user
            email_removed.send(
                sender=User, user=self.user, email_address=address)
        self.assertEqual(mm_user.addresses.remove.call_args_list,
                         [call(self.user.email)])

    def test_email_removed_no_mailman_user(self):
        address = EmailAddress.objects.create(
            user=self.user, email=self.user.email, verified=True)
        with patch('django_mailman3.signals.get_mailman_user') as gmu:
            gmu.return_value = None
            email_removed.send(
                sender=User, user=self.user, email_address=address)

    def test_email_confirmed(self):
        address = EmailAddress.objects.create(
            user=self.user, email=self.user.email, verified=True)
        with patch('django_mailman3.signals.add_address_to_mailman_user') \
                as aatmu:
            email_confirmed.send(sender=EmailAddress, email_address=address)
        self.assertEqual(
            aatmu.call_args_list, [call(self.user, self.user.email)])

    def test_social_account_added(self):
        verified = EmailAddress(
            email='verified@example.com', verified=True)
        unverified = EmailAddress(
            email='unverified@example.com', verified=False)
        sociallogin = SocialLogin(
            user=self.user, email_addresses=[verified, unverified])
        with patch('django_mailman3.signals.add_address_to_mailman_user') \
                as aatmu:
            social_account_added.send(sender=User, sociallogin=sociallogin)
        self.assertEqual(
            aatmu.call_args_list, [call(self.user, 'verified@example.com')])
        self.assertEqual(
            [e.user for e in EmailAddress.objects.all()],
            [self.user, self.user])
