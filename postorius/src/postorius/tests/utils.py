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

import os
import logging

from django.conf import settings
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.test import TestCase
from mock import MagicMock
from six.moves.urllib_parse import quote
from django_mailman3.lib.mailman import get_mailman_client
from django_mailman3.tests.utils import get_flash_messages

from mailmanclient.testing.vcr_helpers import get_vcr

vcr_log = logging.getLogger('vcr')
vcr_log.setLevel(logging.WARNING)


def create_mock_domain(properties=None):
    """Create and return a mocked Domain.

    :param properties: A dictionary of the domain's properties.
    :type properties: dict
    :return: A MagicMock object with the properties set.
    :rtype: MagicMock
    """
    mock_object = MagicMock(name='Domain')
    mock_object.contact_address = ''
    mock_object.description = ''
    mock_object.mail_host = ''
    mock_object.lists = []
    if properties is not None:
        for key in properties:
            setattr(mock_object, key, properties[key])
    return mock_object


def create_mock_list(properties=None):
    """Create and return a mocked List.

    :param properties: A dictionary of the list's properties.
    :type properties: dict
    :return: A MagicMock object with the properties set.
    :rtype: MagicMock
    """
    mock_object = MagicMock(name='List')
    mock_object.members = []
    mock_object.moderators = []
    mock_object.owners = []
    # like in mock_domain, some defaults need to be added...
    if properties is not None:
        for key in properties:
            setattr(mock_object, key, properties[key])
    return mock_object


def create_mock_member(properties=None):
    """Create and return a mocked Member.

    :param properties: A dictionary of the member's properties.
    :type properties: dict
    :return: A MagicMock object with the properties set.
    :rtype: MagicMock
    """
    mock_object = MagicMock(name='Member')
    # like in mock_domain, some defaults need to be added...
    if properties is not None:
        for key in properties:
            setattr(mock_object, key, properties[key])
    return mock_object


class ViewTestCase(TestCase):

    use_vcr = True
    _fixtures_dir = os.path.join(os.path.abspath(
        os.path.dirname(__file__)), 'fixtures', 'vcr_cassettes')

    _mm_vcr = get_vcr(cassette_library_dir=_fixtures_dir)

    def setUp(self):
        self.mm_client = get_mailman_client()
        if self.use_vcr:
            cm = self._mm_vcr.use_cassette('.'.join([
                self.__class__.__name__, self._testMethodName, 'yaml']))
            self.cassette = cm.__enter__()
            self.addCleanup(cm.__exit__, None, None, None)

    def tearDown(self):
        for d in self.mm_client.domains:
            d.delete()
        for u in self.mm_client.users:
            u.delete()

    def assertHasSuccessMessage(self, response):
        msgs = get_flash_messages(response)
        self.assertEqual(len(msgs), 1)
        self.assertEqual(
            msgs[0].level, messages.SUCCESS,
            "%s: %s" % (messages.DEFAULT_TAGS[msgs[0].level], msgs[0].message))
        return msgs[0].message

    def assertHasErrorMessage(self, response):
        msgs = get_flash_messages(response)
        self.assertEqual(len(msgs), 1)
        self.assertEqual(
            msgs[0].level, messages.ERROR,
            "%s: %s" % (messages.DEFAULT_TAGS[msgs[0].level], msgs[0].message))
        return msgs[0].message

    def assertHasNoMessage(self, response):
        msgs = get_flash_messages(response)
        self.assertEqual(len(msgs), 0)

    def assertRedirectsToLogin(self, url):
        response = self.client.get(url)
        self.assertRedirects(response, '{}?next={}'.format(
            reverse(settings.LOGIN_URL), quote(url)))
