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

from __future__ import absolute_import, unicode_literals

from django import template

from postorius.auth.utils import user_is_in_list_roster
from postorius.models import List

from mailmanclient._client import MailingList

register = template.Library()


def get_list(mlist):
    return mlist if isinstance(mlist, MailingList) else List.objects.get(mlist)


@register.assignment_tag
def user_is_list_owner(user, mlist):
    return user_is_in_list_roster(user, get_list(mlist), 'owners')


@register.assignment_tag
def user_is_list_moderator(user, mlist):
    return user_is_in_list_roster(user, get_list(mlist), 'moderators')
