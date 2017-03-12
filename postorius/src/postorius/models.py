# -*- coding: utf-8 -*-
# Copyright (C) 1998-2015 by the Free Software Foundation, Inc.
#
# This file is part of Postorius.
#
# Postorius is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# Postorius is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# Postorius.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import (
    absolute_import, division, print_function, unicode_literals)


import logging

from django.conf import settings
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.http import Http404
from django_mailman3.lib.mailman import get_mailman_client
from mailmanclient import MailmanConnectionError
from django.utils.six.moves.urllib.error import HTTPError

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def create_mailman_user(sender, **kwargs):
    if kwargs.get('created'):
        autocreate = False
        try:
            autocreate = settings.AUTOCREATE_MAILMAN_USER
        except AttributeError:
            pass
        if autocreate:
            user = kwargs.get('instance')
            try:
                MailmanUser.objects.create_from_django(user)
            except (MailmanApiError, HTTPError):
                pass


class MailmanApiError(Exception):
    """Raised if the API is not available.
    """
    pass


class Mailman404Error(Exception):
    """Proxy exception. Raised if the API returns 404."""
    pass


class MailmanRestManager(object):
    """Manager class to give a model class CRUD access to the API.
    Returns objects (or lists of objects) retrived from the API.
    """

    def __init__(self, resource_name, resource_name_plural, cls_name=None):
        self.resource_name = resource_name
        self.resource_name_plural = resource_name_plural

    def all(self):
        try:
            return getattr(get_mailman_client(), self.resource_name_plural)
        except AttributeError:
            raise MailmanApiError
        except MailmanConnectionError as e:
            raise MailmanApiError(e)

    def get(self, *args, **kwargs):
        try:
            method = getattr(get_mailman_client(), 'get_' + self.resource_name)
            return method(*args, **kwargs)
        except AttributeError as e:
            raise MailmanApiError(e)
        except HTTPError as e:
            if e.code == 404:
                raise Mailman404Error('Mailman resource could not be found.')
            else:
                raise
        except MailmanConnectionError as e:
            raise MailmanApiError(e)

    def get_or_404(self, *args, **kwargs):
        """Similar to `self.get` but raises standard Django 404 error.
        """
        try:
            return self.get(*args, **kwargs)
        except Mailman404Error:
            raise Http404
        except MailmanConnectionError as e:
            raise MailmanApiError(e)

    def create(self, *args, **kwargs):
        try:
            method = getattr(
                get_mailman_client(), 'create_' + self.resource_name)
            return method(*args, **kwargs)
        except AttributeError as e:
            raise MailmanApiError(e)
        except HTTPError as e:
            if e.code == 409:
                raise MailmanApiError
            else:
                raise
        except MailmanConnectionError:
            raise MailmanApiError

    def delete(self):
        """Not implemented since the objects returned from the API
        have a `delete` method of their own.
        """
        pass


class MailmanListManager(MailmanRestManager):

    def __init__(self):
        super(MailmanListManager, self).__init__('list', 'lists')

    def all(self, advertised=False):
        try:
            method = getattr(
                get_mailman_client(), 'get_' + self.resource_name_plural)
            return method(advertised=advertised)
        except AttributeError:
            raise MailmanApiError
        except MailmanConnectionError as e:
            raise MailmanApiError(e)

    def by_mail_host(self, mail_host, advertised=False):
        objects = self.all(advertised)
        host_objects = []
        for obj in objects:
            if obj.mail_host == mail_host:
                host_objects.append(obj)
        return host_objects


class MailmanUserManager(MailmanRestManager):

    def __init__(self):
        super(MailmanUserManager, self).__init__('user', 'users')

    def create_from_django(self, user):
        return self.create(user.email, user.get_full_name())

    def get_or_create_from_django(self, user):
        try:
            return self.get(address=user.email)
        except Mailman404Error:
            return self.create_from_django(user)


class MailmanRestModel(object):
    """Simple REST Model class to make REST API calls Django style.
    """
    MailmanApiError = MailmanApiError
    DoesNotExist = Mailman404Error

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def save(self):
        """Proxy function for `objects.create`.
        (REST API uses `create`, while Django uses `save`.)
        """
        self.objects.create(*self.args, **self.kwargs)


class Domain(MailmanRestModel):
    """Domain model class.
    """
    objects = MailmanRestManager('domain', 'domains')


class List(MailmanRestModel):
    """List model class.
    """
    objects = MailmanListManager()


class MailmanUser(MailmanRestModel):
    """MailmanUser model class.
    """
    objects = MailmanUserManager()


class Member(MailmanRestModel):
    """Member model class.
    """
    objects = MailmanRestManager('member', 'members')
