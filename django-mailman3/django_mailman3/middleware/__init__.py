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


# https://docs.djangoproject.com/en/dev/topics/i18n/timezones/

from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist


class TimezoneMiddleware(object):

    def process_request(self, request):
        if not request.user.is_authenticated():
            return
        try:
            profile = request.user.mailman_profile
        except ObjectDoesNotExist:
            return
        if profile.timezone:
            timezone.activate(profile.timezone)


class PaginationMiddleware(object):
    """
    Inserts a variable representing the current page onto the request object if
    it exists in either **GET** or **POST** portions of the request.
    """
    def process_request(self, request):
        try:
            request.page = int(request.REQUEST['page'])
        except (KeyError, ValueError, TypeError):
            request.page = 1
