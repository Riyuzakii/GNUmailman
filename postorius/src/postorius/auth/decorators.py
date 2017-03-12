# -*- coding: utf-8 -*-
# Copyright (C) 1998-2016 by the Free Software Foundation, Inc.
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

"""Postorius view decorators."""

from __future__ import absolute_import, unicode_literals

from django.core.exceptions import PermissionDenied

from postorius.auth.utils import set_user_access_props


def list_owner_required(fn):
    """Check if the logged in user is the list owner of the given list.
    Assumes that the request object is the first arg and that list_id
    is present in kwargs.
    """
    def wrapper(*args, **kwargs):
        user = args[0].user
        list_id = kwargs['list_id']
        if not user.is_authenticated():
            raise PermissionDenied
        if user.is_superuser:
            return fn(*args, **kwargs)
        set_user_access_props(user, list_id)
        if user.is_list_owner:
            return fn(*args, **kwargs)
        else:
            raise PermissionDenied
    return wrapper


def list_moderator_required(fn):
    """Check if the logged in user is a moderator of the given list.
    Assumes that the request object is the first arg and that list_id
    is present in kwargs.
    """
    def wrapper(*args, **kwargs):
        user = args[0].user
        list_id = kwargs['list_id']
        if not user.is_authenticated():
            raise PermissionDenied
        if user.is_superuser:
            return fn(*args, **kwargs)
        set_user_access_props(user, list_id)
        if user.is_list_owner or user.is_list_moderator:
            return fn(*args, **kwargs)
        else:
            raise PermissionDenied
    return wrapper


def superuser_required(fn):
    """Make sure that the logged in user is a superuser or otherwise raise
    PermissionDenied.
    Assumes the request object to be the first arg."""
    def wrapper(*args, **kwargs):
        user = args[0].user
        if not user.is_superuser:
            raise PermissionDenied
        return fn(*args, **kwargs)
    return wrapper
