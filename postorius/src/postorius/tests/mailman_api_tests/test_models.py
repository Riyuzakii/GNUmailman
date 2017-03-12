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
from django.utils.six.moves.urllib.error import HTTPError

from postorius.tests.utils import ViewTestCase


class ModelTest(ViewTestCase):
    """Tests for the list index page."""

    def setUp(self):
        super(ModelTest, self).setUp()
        self.domain = self.mm_client.create_domain('example.com')
        self.foo_list = self.domain.create_list('foo')

    def test_mailman_user_not_created_when_flag_is_off(self):
        with self.settings(AUTOCREATE_MAILMAN_USER=False):
            user = User.objects.create_user(
                'testuser', 'test@example.com', 'testpass')
            EmailAddress.objects.create(
                user=user, email=user.email, verified=True)
            with self.assertRaises(HTTPError):
                self.mm_client.get_user('test@example.com')

    def test_mailman_user_created_when_flag_is_on(self):
        with self.settings(AUTOCREATE_MAILMAN_USER=True):
            user = User.objects.create_user(
                'testuser', 'test@example.com', 'testpass')
            EmailAddress.objects.create(
                user=user, email=user.email, verified=True)
            mm_user = self.mm_client.get_user('test@example.com')
            self.assertEqual(str(mm_user.addresses[0]), 'test@example.com')
