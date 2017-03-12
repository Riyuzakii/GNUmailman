# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 by the Free Software Foundation, Inc.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301,
# USA.
#
# Author: Aurelien Bompard <abompard@fedoraproject.org>

"""
Refresh the recent threads cache for each mailing list.
"""

from __future__ import absolute_import, print_function, unicode_literals

from django_extensions.management.jobs import BaseJob
from django_mailman3.lib.cache import cache
from hyperkitty.models import MailingList


class Job(BaseJob):
    help = "Refresh the recent threads cache"
    when = "daily"

    def execute(self):
        for mlist in MailingList.objects.all():
            cache_key = "MailingList:%s:recent_threads" % mlist.name
            cache.delete(cache_key)
            mlist.recent_threads
