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

from __future__ import absolute_import, unicode_literals

from django.test import TestCase

from django.core.urlresolvers import reverse, NoReverseMatch


class URLTest(TestCase):

    def test_email_allows_slash(self):
        try:
            reverse('list_member_options', kwargs={
                    'list_id': 'test.example.com',
                    'email': 'slashed/are/allowed@example.com',
                    })
            reverse('remove_role', kwargs={
                    'list_id': 'test.example.com',
                    'role': 'subscriber',
                    'address': 'slashed/are/allowed@example.com',
                    })
        except NoReverseMatch as e:
            self.fail(e)

    def test_held_message_url_ends_with_slash(self):
        url = reverse('rest_held_message', args=('foo', 0))
        self.assertEquals(url[-2:], '0/')
