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

from __future__ import absolute_import, print_function, unicode_literals

import logging
import os
from StringIO import StringIO

import mailmanclient
from django.contrib.messages.storage.cookie import CookieStorage
from django.core.cache import cache
from django.utils.timezone import now
from django.test import RequestFactory, TestCase as DjangoTestCase
from mock import Mock, patch


def get_flash_messages(response, empty=True):
    if "messages" not in response.cookies:
        return []
    # A RequestFactory will not run the messages middleware, and thus will
    # not delete the messages after retrieval.
    dummy_request = RequestFactory().get("/")
    dummy_request.COOKIES["messages"] = response.cookies["messages"].value
    msgs = list(CookieStorage(dummy_request))
    if empty:
        del response.client.cookies["messages"]
    return msgs
get_flash_messages.__test__ = False  # noqa: E305


def get_test_file(*fileparts):
    return os.path.join(os.path.dirname(__file__), "testdata", *fileparts)
get_test_file.__test__ = False  # noqa: E305


class FakeMMList:
    def __init__(self, name):
        if '@' not in name:
            name = name.replace('.', '@', 1)
        self.fqdn_listname = name
        self.display_name = name.partition("@")[0]
        self.list_id = name.replace("@", ".")
        self.settings = {
            "description": "",
            "subject_prefix": "[%s] " % self.display_name,
            "created_at": now().isoformat(),
            "archive_policy": "public",
            }


class FakeMMMember:
    def __init__(self, list_id, address, role="member"):
        self.list_id = list_id
        self.address = address
        self.role = role


class FakeMMPage():

    def __init__(self, entries=None, count=20, page=1):
        self.entries = entries or []
        self._count = count
        self._page = page

    def __iter__(self):
        first = (self._page - 1) * self._count
        last = self._page * self._count
        for entry in self.entries[first:last]:
            yield entry

    @property
    def has_previous(self):
        return self._page > 1

    @property
    def has_next(self):
        return self._count * self._page < len(self.entries)


class FakeMMAddress:

    def __init__(self, email, verified=False):
        self.email = email
        self.verified = verified

    def __str__(self):
        return self.email

    def verify(self):
        self.verified = True


class FakeMMAddressList(list):

    def find_by_email(self, email):
        try:
            index = [a.email for a in self].index(email)
        except ValueError:
            return None
        return self[index]


def setup_logging(extra_apps=[]):
    formatter = logging.Formatter(fmt="%(message)s")
    levels = ["debug", "info", "warning", "error"]
    handlers = []
    log = StringIO()
    for level_name in levels:
        handler = logging.StreamHandler(log)
        handler.setLevel(getattr(logging, level_name.upper()))
        handler.setFormatter(formatter)
        handlers.append(handler)
    for logger_name in ["django", "django_mailman3"] + extra_apps:
        logger = logging.getLogger(logger_name)
        logger.propagate = False
        logger.setLevel(logging.DEBUG)
        del logger.handlers[:]
        for handler in handlers:
            logger.addHandler(handler)
    return log


class TestCase(DjangoTestCase):

    def _pre_setup(self):
        super(TestCase, self)._pre_setup()
        # Logging
        self.log = setup_logging()
        # Mock the Mailman client
        self.mailman_client = Mock()
        self.mailman_client.get_user.side_effect = \
            mailmanclient.MailmanConnectionError()
        self.mailman_client.get_list.side_effect = \
            mailmanclient.MailmanConnectionError()
        self._mm_client_patcher = patch(
            "django_mailman3.lib.mailman.MailmanClient",
            lambda *a: self.mailman_client)
        self._mm_client_patcher.start()

    def _post_teardown(self):
        self._mm_client_patcher.stop()
        cache.clear()
        super(TestCase, self)._post_teardown()
