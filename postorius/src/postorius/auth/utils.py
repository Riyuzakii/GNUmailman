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

"""
Authentication and authorization-related utilities.
"""

from __future__ import absolute_import, unicode_literals

from allauth.account.models import EmailAddress
from django.utils import six
from postorius.models import List


def user_is_in_list_roster(user, mailing_list, roster):
    if not user.is_authenticated():
        return False
    addresses = set(EmailAddress.objects.filter(
        user=user, verified=True).values_list("email", flat=True))
    if addresses & set(getattr(mailing_list, roster)):
        return True  # At least one address is in the roster
    return False


def set_user_access_props(user, mlist):
    if isinstance(mlist, six.string_types):
        mlist = List.objects.get_or_404(mlist)
    if not hasattr(user, 'is_list_owner'):
        user.is_list_owner = user_is_in_list_roster(
            user, mlist, "owners")
    if not hasattr(user, 'is_list_moderator'):
        user.is_list_moderator = user_is_in_list_roster(
            user, mlist, "moderators")
