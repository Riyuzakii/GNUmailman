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

from django.core.urlresolvers import reverse

from postorius.tests.utils import ViewTestCase


class ListIndexPageTest(ViewTestCase):
    """Tests for the list index page."""

    def setUp(self):
        super(ListIndexPageTest, self).setUp()
        self.domain = self.mm_client.create_domain('example.com')
        self.foo_list = self.domain.create_list('foo')
        self.bar_list = self.domain.create_list('bar')

    def test_list_index_contains_the_lists(self):
        # The list index page should contain the lists
        response = self.client.get(reverse('list_index'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['lists']), 2)
        # The lists should be sorted by address
        self.assertEqual([l.fqdn_listname for l in response.context['lists']],
                         ['bar@example.com', 'foo@example.com'])

    def test_list_index_only_contains_advertised_lists(self):
        # The list index page should contain only contain the advertised lists
        baz_list = self.domain.create_list('baz')
        baz_list.settings['advertised'] = False
        baz_list.settings.save()
        response = self.client.get(reverse('list_index'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['lists']), 2)
        self.assertNotIn(
            'baz.example.com',
            [ml.list_id for ml in response.context['lists']])
