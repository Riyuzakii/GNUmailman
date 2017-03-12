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
# Author: Aurelien Bompard <abompard@fedoraproject.org>
#

from __future__ import absolute_import, unicode_literals, division

from django.http import Http404
from django.core.paginator import (
    Paginator, EmptyPage, InvalidPage)
from django.utils.functional import cached_property


class MailmanPaginator(Paginator):
    """
    Subclass of Django's Paginator that works with MailmanClient's 'get_*_page'
    functions. Use the function reference as the first argument::

        MailmanPaginator(get_member_page, 25)

    """

    def __init__(self, function, per_page, **kwargs):
        self.function = function
        super(MailmanPaginator, self).__init__(None, per_page, **kwargs)

    def page(self, number):
        """
        Returns a Page object for the given 1-based page number.
        """
        number = self.validate_number(number)
        result = self.function(count=self.per_page, page=number)
        return self._get_page(result, number, self)

    @cached_property
    def count(self):
        """
        Returns the total number of objects, across all pages.
        """
        # See the rest/docs/collections.rst in the Mailman source tree.
        return self.function(count=0, page=1).total_size


def paginate(objects=None, page_num=None, results_per_page=None,
             max_page_range=10, paginator_class=Paginator):
    try:
        page_num = int(page_num)
    except (ValueError, TypeError):
        page_num = 1
    try:
        results_per_page = int(results_per_page)
    except (ValueError, TypeError):
        results_per_page = 10
    paginator = paginator_class(objects, results_per_page)
    try:
        objects = paginator.page(page_num)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        objects = paginator.page(paginator.num_pages)
    except InvalidPage:
        # This never happens with Django's Paginator, but just in case.
        raise Http404("No such page of results!")
    # Calculate the displayed page range
    if paginator.num_pages > max_page_range:
        paginator.page_range_ellipsis = [1]
        subrange_lower = page_num - int(max_page_range / 2 - 2)
        if subrange_lower > 3:
            paginator.page_range_ellipsis.append("...")
        else:
            subrange_lower = 2
        paginator.page_range_ellipsis.extend(range(subrange_lower, page_num))
        if page_num != 1 and page_num != paginator.num_pages:
            paginator.page_range_ellipsis.append(page_num)
        subrange_upper = page_num + int(max_page_range / 2 - 2)
        if subrange_upper >= paginator.num_pages - 2:
            subrange_upper = paginator.num_pages - 1
        paginator.page_range_ellipsis.extend(
            range(page_num+1, subrange_upper+1))
        if subrange_upper < paginator.num_pages - 2:
            paginator.page_range_ellipsis.append("...")
        paginator.page_range_ellipsis.append(paginator.num_pages)
    else:
        paginator.page_range_ellipsis = paginator.page_range
    return objects
