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

"""Tests for list header matches"""

from __future__ import absolute_import, print_function, unicode_literals

from allauth.account.models import EmailAddress
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from postorius.tests.utils import ViewTestCase


class ListHeaderMatchesTest(ViewTestCase):
    """
    Tests for the list settings page.
    """

    def setUp(self):
        super(ListHeaderMatchesTest, self).setUp()
        self.domain = self.mm_client.create_domain('example.com')
        self.mlist = self.domain.create_list('list')
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
        self.mlist.add_owner('owner@example.com')
        self.mlist.add_moderator('moderator@example.com')

    def test_page_not_accessible_if_not_logged_in(self):
        url = reverse('list_header_matches', args=['list.example.com'])
        self.assertRedirectsToLogin(url)

    def test_page_not_accessible_for_unprivileged_users(self):
        self.client.login(username='testuser', password='testpass')
        url = reverse('list_header_matches', args=['list.example.com'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_not_accessible_for_moderator(self):
        self.client.login(username='testmoderator', password='testpass')
        url = reverse('list_header_matches', args=['list.example.com'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_page_accessible_for_owner(self):
        self.client.login(username='testowner', password='testpass')
        url = reverse('list_header_matches', args=['list.example.com'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_page_accessible_for_superuser(self):
        self.client.login(username='testsu', password='testpass')
        url = reverse('list_header_matches', args=['list.example.com'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_show_existing(self):
        self.mlist.header_matches.add(
            header='testheader', pattern='testpattern', action='discard')
        self.client.login(username='testowner', password='testpass')
        url = reverse('list_header_matches', args=['list.example.com'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["formset"]), 2)
        self.assertEqual(
            response.context["formset"].initial,
            [{'header': u'testheader', 'pattern': u'testpattern',
              'action': u'discard'}])
        self.assertContains(response, 'testheader')
        self.assertContains(response, 'testpattern')
        self.assertContains(response, 'value="discard" selected="selected"')
        # the new header match subform should not have ORDER or DELETE fields
        self.assertNotContains(response, 'form-1-ORDER')
        self.assertNotContains(response, 'form-1-DELETE')

    def test_add(self):
        self.client.login(username='testowner', password='testpass')
        url = reverse('list_header_matches', args=['list.example.com'])
        data = {
            # Management form
            'form-TOTAL_FORMS': '1',
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',
            # New form
            'form-0-header': 'testheader',
            'form-0-pattern': 'testpattern',
            'form-0-action': 'discard',
        }
        response = self.client.post(url, data)
        self.assertRedirects(response, url)
        self.assertHasSuccessMessage(response)
        self.assertEqual(len(self.mlist.header_matches), 1)
        hm = self.mlist.header_matches[0]
        self.assertEqual(hm.header, 'testheader')
        self.assertEqual(hm.pattern, 'testpattern')
        self.assertEqual(hm.action, 'discard')

    def test_add_empty(self):
        self.client.login(username='testowner', password='testpass')
        url = reverse('list_header_matches', args=['list.example.com'])
        data = {
            # Management form
            'form-TOTAL_FORMS': '1',
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',
            # New form
            'form-0-header': '',
            'form-0-pattern': '',
            'form-0-action': '',
        }
        response = self.client.post(url, data)
        self.assertRedirects(response, url)
        self.assertHasNoMessage(response)
        self.assertEqual(len(self.mlist.header_matches), 0)

    def test_add_empty_header(self):
        self.client.login(username='testowner', password='testpass')
        url = reverse('list_header_matches', args=['list.example.com'])
        data = {
            # Management form
            'form-TOTAL_FORMS': '1',
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',
            # New form
            'form-0-header': '',
            'form-0-pattern': 'testpattern',
            'form-0-action': '',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertHasNoMessage(response)
        self.assertEqual(
            response.context["formset"].errors,
            [{'header': [u'Please enter a header.']}])
        self.assertEqual(len(self.mlist.header_matches), 0)

    def test_add_empty_pattern(self):
        self.client.login(username='testowner', password='testpass')
        url = reverse('list_header_matches', args=['list.example.com'])
        data = {
            # Management form
            'form-TOTAL_FORMS': '1',
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',
            # New form
            'form-0-header': 'testheader',
            'form-0-pattern': '',
            'form-0-action': '',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertHasNoMessage(response)
        self.assertEqual(
            response.context["formset"].errors,
            [{'pattern': [u'Please enter a pattern.']}])
        self.assertEqual(len(self.mlist.header_matches), 0)

    def test_edit(self):
        self.mlist.header_matches.add(
            header='testheader', pattern='testpattern', action='discard')
        self.client.login(username='testowner', password='testpass')
        url = reverse('list_header_matches', args=['list.example.com'])
        data = {
            # Management form
            'form-TOTAL_FORMS': '2',
            'form-INITIAL_FORMS': '1',
            'form-MIN_NUM_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',
            # Existing pattern
            'form-0-header': 'testheader-changed',
            'form-0-pattern': 'testpattern-changed',
            'form-0-action': 'hold',
            'form-0-ORDER': '1',
            'form-0-DELETE': '',
            # New form
            'form-1-header': '',
            'form-1-pattern': '',
            'form-1-action': '',
        }
        response = self.client.post(url, data)
        self.assertRedirects(response, url)
        self.assertHasSuccessMessage(response)
        self.assertEqual(len(self.mlist.header_matches), 1)
        hm = self.mlist.header_matches[0]
        self.assertEqual(hm.header, 'testheader-changed')
        self.assertEqual(hm.pattern, 'testpattern-changed')
        self.assertEqual(hm.action, 'hold')

    def test_edit_empty(self):
        self.mlist.header_matches.add(
            header='testheader', pattern='testpattern', action='discard')
        self.client.login(username='testowner', password='testpass')
        url = reverse('list_header_matches', args=['list.example.com'])
        data = {
            # Management form
            'form-TOTAL_FORMS': '2',
            'form-INITIAL_FORMS': '1',
            'form-MIN_NUM_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',
            # Existing pattern
            'form-0-header': '',
            'form-0-pattern': '',
            'form-0-action': '',
            'form-0-ORDER': '1',
            'form-0-DELETE': '',
            # New form
            'form-1-header': '',
            'form-1-pattern': '',
            'form-1-action': '',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertHasNoMessage(response)
        self.assertEqual(
            response.context["formset"].errors,
            [{'header': [u'Please enter a header.'],
              'pattern': [u'Please enter a pattern.'],
              }, {}])
        self.assertEqual(len(self.mlist.header_matches), 1)
        hm = self.mlist.header_matches[0]
        self.assertEqual(hm.header, 'testheader')
        self.assertEqual(hm.pattern, 'testpattern')
        self.assertEqual(hm.action, 'discard')

    def test_delete(self):
        self.mlist.header_matches.add(
            header='testheader-1', pattern='testpattern-1', action='discard')
        self.mlist.header_matches.add(
            header='testheader-2', pattern='testpattern-2', action='discard')
        self.client.login(username='testowner', password='testpass')
        url = reverse('list_header_matches', args=['list.example.com'])
        data = {
            # Management form
            'form-TOTAL_FORMS': '3',
            'form-INITIAL_FORMS': '2',
            'form-MIN_NUM_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',
            # Existing pattern
            'form-0-header': 'testheader-1',
            'form-0-pattern': 'testpattern-1',
            'form-0-action': 'hold',
            'form-0-ORDER': '1',
            'form-0-DELETE': '1',
            'form-1-header': 'testheader-2',
            'form-1-pattern': 'testpattern-2',
            'form-1-action': 'discard',
            'form-1-ORDER': '2',
            'form-1-DELETE': '',
            # New form
            'form-2-header': '',
            'form-2-pattern': '',
            'form-2-action': '',
        }
        response = self.client.post(url, data)
        self.assertRedirects(response, url)
        self.assertHasSuccessMessage(response)
        self.assertEqual(len(self.mlist.header_matches), 1)
        hm = self.mlist.header_matches[0]
        self.assertEqual(hm.header, 'testheader-2')
        self.assertEqual(hm.pattern, 'testpattern-2')
        self.assertEqual(hm.action, 'discard')

    def test_move_up(self):
        self.mlist.header_matches.add(
            header='testheader-1', pattern='testpattern-1', action='discard')
        self.mlist.header_matches.add(
            header='testheader-2', pattern='testpattern-2', action='discard')
        self.mlist.header_matches.add(
            header='testheader-3', pattern='testpattern-3', action='discard')
        self.client.login(username='testowner', password='testpass')
        url = reverse('list_header_matches', args=['list.example.com'])
        data = {
            # Management form
            'form-TOTAL_FORMS': '4',
            'form-INITIAL_FORMS': '3',
            'form-MIN_NUM_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',
            # Existing patterns
            'form-0-header': 'testheader-1',
            'form-0-pattern': 'testpattern-1',
            'form-0-action': 'discard',
            'form-0-ORDER': '1',
            'form-0-DELETE': '',
            'form-1-header': 'testheader-2',
            'form-1-pattern': 'testpattern-2',
            'form-1-action': 'discard',
            'form-1-ORDER': '3',
            'form-1-DELETE': '',
            'form-2-header': 'testheader-3',
            'form-2-pattern': 'testpattern-3',
            'form-2-action': 'discard',
            'form-2-ORDER': '2',
            'form-2-DELETE': '',
            # New form
            'form-3-header': '',
            'form-3-pattern': '',
            'form-3-action': '',
        }
        response = self.client.post(url, data)
        self.assertRedirects(response, url)
        self.assertHasSuccessMessage(response)
        self.assertEqual(len(self.mlist.header_matches), 3)
        self.assertEqual(
            [(hm.header, hm.pattern, hm.action)
             for hm in self.mlist.header_matches],
            [('testheader-1', 'testpattern-1', 'discard'),
             ('testheader-3', 'testpattern-3', 'discard'),
             ('testheader-2', 'testpattern-2', 'discard')]
            )

    def test_move_down(self):
        self.mlist.header_matches.add(
            header='testheader-1', pattern='testpattern-1', action='discard')
        self.mlist.header_matches.add(
            header='testheader-2', pattern='testpattern-2', action='discard')
        self.mlist.header_matches.add(
            header='testheader-3', pattern='testpattern-3', action='discard')
        self.client.login(username='testowner', password='testpass')
        url = reverse('list_header_matches', args=['list.example.com'])
        data = {
            # Management form
            'form-TOTAL_FORMS': '4',
            'form-INITIAL_FORMS': '3',
            'form-MIN_NUM_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',
            # Existing patterns
            'form-0-header': 'testheader-1',
            'form-0-pattern': 'testpattern-1',
            'form-0-action': 'discard',
            'form-0-ORDER': '2',
            'form-0-DELETE': '',
            'form-1-header': 'testheader-2',
            'form-1-pattern': 'testpattern-2',
            'form-1-action': 'discard',
            'form-1-ORDER': '1',
            'form-1-DELETE': '',
            'form-2-header': 'testheader-3',
            'form-2-pattern': 'testpattern-3',
            'form-2-action': 'discard',
            'form-2-ORDER': '3',
            'form-2-DELETE': '',
            # New form
            'form-3-header': '',
            'form-3-pattern': '',
            'form-3-action': '',
        }
        response = self.client.post(url, data)
        self.assertRedirects(response, url)
        self.assertHasSuccessMessage(response)
        self.assertEqual(len(self.mlist.header_matches), 3)
        self.assertEqual(
            [(hm.header, hm.pattern, hm.action)
             for hm in self.mlist.header_matches],
            [('testheader-2', 'testpattern-2', 'discard'),
             ('testheader-1', 'testpattern-1', 'discard'),
             ('testheader-3', 'testpattern-3', 'discard')]
            )

    def test_same_order(self):
        self.mlist.header_matches.add(
            header='testheader-1', pattern='testpattern-1', action='discard')
        self.mlist.header_matches.add(
            header='testheader-2', pattern='testpattern-2', action='discard')
        self.client.login(username='testowner', password='testpass')
        url = reverse('list_header_matches', args=['list.example.com'])
        data = {
            # Management form
            'form-TOTAL_FORMS': '3',
            'form-INITIAL_FORMS': '2',
            'form-MIN_NUM_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',
            # Existing patterns
            'form-0-header': 'testheader-1',
            'form-0-pattern': 'testpattern-1',
            'form-0-action': 'discard',
            'form-0-ORDER': '1',
            'form-0-DELETE': '',
            'form-1-header': 'testheader-2',
            'form-1-pattern': 'testpattern-2',
            'form-1-action': 'discard',
            'form-1-ORDER': '1',
            'form-1-DELETE': '',
            # New form
            'form-2-header': '',
            'form-2-pattern': '',
            'form-2-action': '',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertHasNoMessage(response)
        for form_errors in response.context["formset"].errors:
            self.assertEqual(len(form_errors), 0)
        self.assertEqual(
            response.context["formset"].non_form_errors(),
            ['Header matches must have distinct orders.'])
        self.assertEqual(len(self.mlist.header_matches), 2)
        self.assertEqual(
            [(hm.header, hm.pattern, hm.action)
             for hm in self.mlist.header_matches],
            [('testheader-1', 'testpattern-1', 'discard'),
             ('testheader-2', 'testpattern-2', 'discard')]
            )

    def test_add_existing(self):
        self.mlist.header_matches.add(
            header='testheader', pattern='testpattern', action='discard')
        self.client.login(username='testowner', password='testpass')
        url = reverse('list_header_matches', args=['list.example.com'])
        data = {
            # Management form
            'form-TOTAL_FORMS': '2',
            'form-INITIAL_FORMS': '1',
            'form-MIN_NUM_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',
            # Existing patterns
            'form-0-header': 'testheader',
            'form-0-pattern': 'testpattern',
            'form-0-action': 'discard',
            'form-0-ORDER': '1',
            'form-0-DELETE': '',
            # New form
            'form-1-header': 'testheader',
            'form-1-pattern': 'testpattern',
            'form-1-action': 'hold',
        }
        response = self.client.post(url, data)
        self.assertRedirects(response, url)
        self.assertHasErrorMessage(response)
        self.assertEqual(len(self.mlist.header_matches), 1)
        self.assertEqual(
            [(hm.header, hm.pattern, hm.action)
             for hm in self.mlist.header_matches],
            [('testheader', 'testpattern', 'discard')])
