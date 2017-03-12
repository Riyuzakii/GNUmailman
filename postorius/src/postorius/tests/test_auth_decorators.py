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

from allauth.account.models import EmailAddress
from django.contrib.auth.models import AnonymousUser, User
from django.core.exceptions import PermissionDenied
from django.test.client import RequestFactory
from django.test import TestCase
from mock import patch

from postorius.auth.decorators import (list_owner_required,
                                       list_moderator_required,
                                       superuser_required)
from postorius.tests.utils import create_mock_list
from mailmanclient import Client


@list_owner_required
def dummy_function(request, list_id):
    return True


@list_moderator_required
def dummy_function_mod_req(request, list_id):
    return True


@superuser_required
def dummy_superuser_required(request):
    return True


def create_user():
    user = User.objects.create_user(
        'les c', 'les@primus.org', 'pwd')
    EmailAddress.objects.create(
        user=user, email=user.email, verified=True)
    return user


class ListOwnerRequiredTest(TestCase):
    """Tests the list_owner_required auth decorator."""

    def setUp(self):
        from postorius.tests.utils import create_mock_list
        self.request_factory = RequestFactory()
        # create a mock list with members
        list_name = 'foolist.example.org'
        list_id = 'foolist.example.org'
        self.mock_list = create_mock_list(dict(
            fqdn_listname=list_name,
            list_id=list_id))

    @patch.object(Client, 'get_list')
    def test_not_authenticated(self, mock_get_list):
        """Should raise PermissionDenied if user is not authenticated."""
        mock_get_list.return_value = self.mock_list
        request = self.request_factory.get(
            '/lists/foolist.example.org/settings/')
        request.user = AnonymousUser()
        self.assertRaises(PermissionDenied, dummy_function, request,
                          list_id='foolist.example.org')

    @patch.object(Client, 'get_list')
    def test_superuser(self, mock_get_list):
        """Should call the dummy method, if user is superuser."""
        mock_get_list.return_value = self.mock_list
        request = self.request_factory.get(
            '/lists/foolist.example.org/settings/')
        request.user = User.objects.create_superuser(
            'su1', 'su@sodo.org', 'pwd')
        EmailAddress.objects.create(
            user=request.user, email=request.user.email, verified=True)
        return_value = dummy_function(
            request, list_id='foolist.example.org')
        self.assertEqual(return_value, True)

    @patch.object(Client, 'get_list')
    def test_non_list_owner(self, mock_get_list):
        """Should raise PermissionDenied if user is not a list owner."""
        # prepare mock list object
        self.mock_list.owners = ['geddy@rush.it']
        mock_get_list.return_value = self.mock_list
        # prepare request
        request = self.request_factory.get(
            '/lists/foolist.example.org/settings/')
        request.user = create_user()
        self.assertRaises(PermissionDenied, dummy_function, request,
                          list_id='foolist.example.org')

    @patch.object(Client, 'get_list')
    def test_list_owner(self, mock_get_list):
        """Should return fn return value if user is the list owner."""
        # prepare mock list object
        self.mock_list.owners = ['les@primus.org']
        mock_get_list.return_value = self.mock_list
        # prepare request
        request = self.request_factory.get(
            '/lists/foolist.example.org/settings/')
        request.user = create_user()
        return_value = dummy_function(
            request, list_id='foolist.example.org')
        self.assertEqual(return_value, True)


class ListModeratorRequiredTest(TestCase):
    """Tests the list_owner_required auth decorator."""

    def setUp(self):
        from postorius.tests.utils import create_mock_list
        self.request_factory = RequestFactory()
        # create a mock list with members
        list_name = 'foolist.example.org'
        list_id = 'foolist.example.org'
        self.mock_list = create_mock_list(dict(
            fqdn_listname=list_name,
            list_id=list_id))

    @patch.object(Client, 'get_list')
    def test_not_authenticated(self, mock_get_list):
        """Should raise PermissionDenied if user is not authenticated."""
        mock_get_list.return_value = self.mock_list
        request = self.request_factory.get(
            '/lists/foolist.example.org/settings/')
        request.user = AnonymousUser()
        self.assertRaises(PermissionDenied, dummy_function_mod_req, request,
                          list_id='foolist.example.org')

    @patch.object(Client, 'get_list')
    def test_superuser(self, mock_get_list):
        """Should call the dummy method, if user is superuser."""
        mock_get_list.return_value = self.mock_list
        request = self.request_factory.get(
            '/lists/foolist.example.org/settings/')
        request.user = User.objects.create_superuser(
            'su2', 'su@sodo.org', 'pwd')
        EmailAddress.objects.create(
            user=request.user, email=request.user.email, verified=True)
        return_value = dummy_function_mod_req(
            request, list_id='foolist.example.org')
        self.assertEqual(return_value, True)

    @patch.object(Client, 'get_list')
    def test_non_list_moderator(self, mock_get_list):
        """Should raise PermissionDenied if user is not a list owner."""
        # prepare mock list object
        self.mock_list.moderators = ['geddy@rush.it']
        mock_get_list.return_value = self.mock_list
        # prepare request
        request = self.request_factory.get(
            '/lists/foolist.example.org/settings/')
        request.user = create_user()
        self.assertRaises(PermissionDenied, dummy_function_mod_req, request,
                          list_id='foolist.example.org')

    @patch.object(Client, 'get_list')
    def test_list_owner(self, mock_get_list):
        """Should return fn return value if user is the list owner."""
        # prepare mock list object
        self.mock_list.owners = ['les@primus.org']
        mock_get_list.return_value = self.mock_list
        # prepare request
        request = self.request_factory.get(
            '/lists/foolist.example.org/settings/')
        request.user = create_user()
        return_value = dummy_function_mod_req(
            request, list_id='foolist.example.org')
        self.assertEqual(return_value, True)

    @patch.object(Client, 'get_list')
    def test_list_moderator(self, mock_get_list):
        """Should return fn return value if user is the list moderator."""
        # prepare mock list object
        self.mock_list.moderators = ['les@primus.org']
        mock_get_list.return_value = self.mock_list
        # prepare request
        request = self.request_factory.get(
            '/lists/foolist.example.org/settings/')
        request.user = create_user()
        return_value = dummy_function_mod_req(
            request, list_id='foolist.example.org')
        self.assertEqual(return_value, True)


class TestSuperUserOr403(TestCase):
    """Tests superuser_required auth decorator"""

    def setUp(self):
        self.request_factory = RequestFactory()
        # create a mock list with members
        list_name = 'foolist.example.org'
        list_id = 'foolist.example.org'
        self.mock_list = create_mock_list(dict(
            fqdn_listname=list_name,
            list_id=list_id))

    @patch.object(Client, 'get_list')
    def test_anonymous_user(self, mock_get_list):
        """Should raise PermissionDenied if user is an anonymous user."""
        mock_get_list.return_value = self.mock_list

        request = self.request_factory.get(
            '/lists/foolist.example.org/settings/')
        request.user = AnonymousUser()
        self.assertRaises(PermissionDenied, dummy_superuser_required, request)

    @patch.object(Client, 'get_list')
    def test_normal_user(self, mock_get_list):
        """Should raise PermissionDenied if user is a normal user."""
        mock_get_list.return_value = self.mock_list

        request = self.request_factory.get(
            '/lists/foolist.example.org/settings/')
        request.user = create_user()
        self.assertRaises(PermissionDenied, dummy_superuser_required, request)

    @patch.object(Client, 'get_list')
    def test_super_user(self, mock_get_list):
        """Should not raise PermissionDenied if user is superuser."""
        mock_get_list.return_value = self.mock_list

        request = self.request_factory.get(
            '/lists/foolist.example.org/settings/')
        request.user = create_user()
        request.user.is_superuser = True
        request.user.save()
        self.assertTrue(dummy_superuser_required(request))
