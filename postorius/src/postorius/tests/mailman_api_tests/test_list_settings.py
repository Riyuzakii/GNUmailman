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

"""Tests for list settings"""

from __future__ import absolute_import, print_function, unicode_literals

from allauth.account.models import EmailAddress
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from postorius.views.list import SETTINGS_FORMS
from postorius.models import List
from postorius.tests.utils import ViewTestCase


class ListSettingsTest(ViewTestCase):
    """
    Tests for the list settings page.
    """

    def setUp(self):
        super(ListSettingsTest, self).setUp()
        self.domain = self.mm_client.create_domain('example.com')
        self.foo_list = self.domain.create_list('foo')
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

    def test_page_not_accessible_if_not_logged_in(self):
        for section_name in SETTINGS_FORMS:
            url = reverse('list_settings', args=('foo.example.com',
                                                 section_name))
            self.assertRedirectsToLogin(url)

    def test_page_not_accessible_for_unprivileged_users(self):
        self.client.login(username='testuser', password='testpass')
        for section_name in SETTINGS_FORMS:
            url = reverse('list_settings', args=('foo.example.com',
                                                 section_name))
            response = self.client.get(url)
            self.assertEqual(response.status_code, 403)

    def test_not_accessible_for_moderator(self):
        self.client.login(username='testmoderator', password='testpass')
        for section_name in SETTINGS_FORMS:
            url = reverse('list_settings', args=('foo.example.com',
                                                 section_name))
            response = self.client.get(url)
            self.assertEqual(response.status_code, 403)

    def test_page_accessible_for_owner(self):
        self.client.login(username='testowner', password='testpass')
        for section_name in SETTINGS_FORMS:
            url = reverse('list_settings', args=('foo.example.com',
                                                 section_name))
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)

    def test_page_accessible_for_superuser(self):
        self.client.login(username='testsu', password='testpass')
        for section_name in SETTINGS_FORMS:
            url = reverse('list_settings', args=('foo@example.com',
                                                 section_name))
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)

    def test_archiving_policy(self):
        self.assertEqual(self.foo_list.settings['archive_policy'], 'public')
        self.client.login(username='testsu', password='testpass')
        url = reverse('list_settings', args=('foo.example.com', 'archiving'))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["form"].initial['archive_policy'], 'public')
        response = self.client.post(url, {'archive_policy': 'private'})
        self.assertRedirects(response, url)
        self.assertHasSuccessMessage(response)
        # Get a new list object to avoid caching
        m_list = List.objects.get(fqdn_listname='foo.example.com')
        self.assertEqual(m_list.settings['archive_policy'], 'private')

    def test_archivers(self):
        self.assertEqual(dict(self.foo_list.archivers),
                         {'mhonarc': True, 'prototype': True,
                          'mail-archive': True})
        self.client.login(username='testsu', password='testpass')
        url = reverse('list_settings', args=('foo.example.com', 'archiving'))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["form"].initial['archivers'],
                         ['mail-archive', 'mhonarc', 'prototype'])
        response = self.client.post(
            url, {'archive_policy': 'public', 'archivers': ['prototype']})
        self.assertRedirects(response, url)
        self.assertHasSuccessMessage(response)
        # Get a new list object to avoid caching
        m_list = List.objects.get(fqdn_listname='foo.example.com')
        self.assertEqual(dict(m_list.archivers),
                         {'mhonarc': False, 'prototype': True,
                          'mail-archive': False})

    def test_bug_117(self):
        self.assertEqual(self.foo_list.settings['first_strip_reply_to'], False)
        self.client.login(username='testsu', password='testpass')
        url = reverse(
            'list_settings', args=('foo.example.com', 'alter_messages'))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        form = response.context["form"]
        self.assertEqual(
            form.initial['first_strip_reply_to'], 'False')
        post_data = dict(
            (key, unicode(self.foo_list.settings[key]))
            for key in form.fields)
        post_data['first_strip_reply_to'] = 'True'
        response = self.client.post(url, post_data)
        self.assertRedirects(response, url)
        self.assertHasSuccessMessage(response)
        # Get a new list object to avoid caching
        m_list = List.objects.get(fqdn_listname='foo.example.com')
        self.assertEqual(m_list.settings['first_strip_reply_to'], True)

    def test_list_identity_allow_empty_prefix_and_desc(self):
        self.assertEqual(self.foo_list.settings['subject_prefix'], '[Foo] ')
        self.assertEqual(self.foo_list.settings['description'], '')
        self.client.login(username='testsu', password='testpass')
        url = reverse('list_settings',
                      args=('foo.example.com', 'list_identity'))
        response = self.client.post(url, {
            'subject_prefix': '',
            'description': '',
            'advertised': 'True',
            })
        self.assertRedirects(response, url)
        self.assertHasSuccessMessage(response)
        # Get a new list object to avoid caching
        m_list = List.objects.get(fqdn_listname='foo.example.com')
        self.assertEqual(m_list.settings['subject_prefix'], '')
        self.assertEqual(m_list.settings['description'], '')
