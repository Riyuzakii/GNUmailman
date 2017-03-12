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


register = template.Library()


@register.inclusion_tag('postorius/menu/list_nav.html', takes_context=True)
def list_nav(context, current, title='', subtitle=''):
    return dict(list=context['list'],
                current=current,
                user=context['request'].user,
                title=title, subtitle=subtitle)


@register.inclusion_tag('postorius/menu/user_nav.html', takes_context=True)
def user_nav(context, current, title='', subtitle=''):
    return dict(current=current,
                user=context['request'].user,
                title=title, subtitle=subtitle)


@register.simple_tag(takes_context=True)
def nav_active_class(context, current, view_name):
    if current == view_name:
        return 'active'
    return ''
