# Copyright (C) 2016 by the Free Software Foundation, Inc.
#
# This file is part of Django-Mailman.
#
# Django-Mailman is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by the
# Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# Django-Mailman is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License
# for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Django-Mailman.  If not, see <http://www.gnu.org/licenses/>.

from django import template
from django.utils.html import conditional_escape
from django.utils.translation import ugettext_lazy as _


register = template.Library()


@register.simple_tag(takes_context=True)
def add_to_query_string(context, *args, **kwargs):
    """Adds or replaces parameters in the query string"""
    qs = context["request"].GET.copy()
    # create a dict from every args couple
    new_qs_elements = dict(zip(args[::2], args[1::2]))
    new_qs_elements.update(kwargs)
    # don't use the .update() method, it appends instead of overwriting.
    for key, value in new_qs_elements.items():
        qs[key] = value
    return conditional_escape(qs.urlencode())


@register.inclusion_tag('django_mailman3/paginator/pagination.html',
                        takes_context=True)
def paginator(context, page, qsprefix='', bydate=False):
    if bydate:
        label_previous = _("Newer")
        label_next = _("Older")
    else:
        label_previous = _("Previous")
        label_next = _("Next")
    context.update(dict(
        page=page,
        label_previous=label_previous,
        label_next=label_next,
        page_key="{}page".format(qsprefix),
        count_key="{}count".format(qsprefix),
        per_page_options=[10, 50, 100, 200],  # move to settings?
        ))
    return context
