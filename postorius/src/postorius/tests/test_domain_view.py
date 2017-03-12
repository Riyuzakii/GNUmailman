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

from __future__ import absolute_import, print_function, unicode_literals

from allauth.account.models import EmailAddress
from django.test import TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from postorius.forms import DomainForm


class DomainViewTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_superuser('su', 'su@example.com',
                                                  'pass')
        EmailAddress.objects.create(
            user=self.user, email=self.user.email, verified=True)

    def tearDown(self):
        self.user.delete()

    def test_form_is_rendered(self):
        self.client.login(username='su', password='pass')
        response = self.client.get(reverse('domain_new'), follow=True)
        self.assertEquals(response.status_code, 200)
        self.assertIsInstance(response.context['form'], DomainForm)
