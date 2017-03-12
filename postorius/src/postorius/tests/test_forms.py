# -*- coding: utf-8 -*-
# Copyright (C) 2012-2016 by the Free Software Foundation, Inc.
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

from __future__ import absolute_import, unicode_literals

from django.test import TestCase

from postorius.forms import (
    ChangeSubscriptionForm, DomainForm, ListIdentityForm, ListNew,
    ListSubscribe, UserPreferences)


class UserPreferencesTest(TestCase):

    def test_form_fields_valid(self):
        form = UserPreferences({
            'acknowledge_posts': 'True',
            'hide_address': 'True',
            'receive_list_copy': 'False',
            'receive_own_postings': 'False',
        })
        self.assertTrue(form.is_valid())


class DomainNewTest(TestCase):

    def test_form_fields_valid(self):
        form = DomainForm({
            'mail_host': 'mailman.most-desirable.org',
            'description': 'The Most Desirable organization',
            'contact_address': 'contact@mailman.most-desirable.org',
            'site': 1,
        })
        self.assertTrue(form.is_valid())


class ListSubscribeTest(TestCase):
    def test_subscribe_works(self):
        user_emails = ['someone@example.com']
        form = ListSubscribe(user_emails,
                             {'email': 'someone@example.com',
                              'display_name': 'Someone'})
        self.assertTrue(form.is_valid())

    def test_subscribe_fails(self):
        user_emails = ['someone@example.com']
        form = ListSubscribe(user_emails,
                             {'email': 'notaemail',
                              'display_name': 'Someone'})
        self.assertFalse(form.is_valid())

    def test_subscribe_validates_email(self):
        user_emails = ['something']
        form = ListSubscribe(user_emails,
                             {'email': 'something',
                              'display_name': 'Someone'})
        self.assertFalse(form.is_valid())


class ChangeSubscriptionTest(TestCase):
    def test_subscription_changes_only_to_user_addresses(self):
        user_emails = ['one@example.com', 'two@example.com']
        form = ChangeSubscriptionForm(user_emails, {'email': 'abcd@d.com'})
        self.assertFalse(form.is_valid())

    def test_subscription_works(self):
        user_emails = ['one@example.com', 'two@example.com']
        form = ChangeSubscriptionForm(user_emails,
                                      {'email': 'two@example.com'})
        self.assertTrue(form.is_valid())


class ListNewTest(TestCase):

    def test_form_fields_list(self):
        form = ListNew([
            ("mailman.most-desirable.org", "mailman.most-desirable.org")],
            {
            'listname': 'xyz',
            'mail_host': 'mailman.most-desirable.org',
            'list_owner': 'contact@mailman.most-desirable.org',
            'advertised': 'True',
            'description': 'The Most Desirable organization',
            })
        self.assertTrue(form.is_valid(), form.errors)

    def test_form_fields_list_invalid(self):
        form = ListNew([
            ("mailman.most-desirable.org", "mailman.most-desirable.org")],
            {
            'listname': 'xy#z',
            'mail_host': 'mailman.most-desirable.org',
            'list_owner': 'mailman.most-desirable.org',
            'advertised': 'abcd',
            'description': 'The Most Desirable organization',
            })
        self.assertFalse(form.is_valid())


class ListIdentityTest(TestCase):

    def test_info_not_required(self):
        form = ListIdentityForm({
            'advertised': 'True',
            'description': 'The Most Desirable organization',
            'display_name': 'Most Desirable',
            'subject_prefix': '[Most Desirable] ',
        }, mlist=None)
        self.assertTrue(form.is_valid(), form.errors)
