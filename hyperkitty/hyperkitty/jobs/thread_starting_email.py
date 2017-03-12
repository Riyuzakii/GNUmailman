# -*- coding: utf-8 -*-
#
# Copyright (C) 2014-2015 by the Free Software Foundation, Inc.
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
Find the starting email for threads which don't have one set already.
"""

from __future__ import absolute_import, print_function, unicode_literals

from django_extensions.management.jobs import BaseJob
from hyperkitty.models.email import Email
from hyperkitty.models.thread import Thread


class Job(BaseJob):
    help = "Find the starting email when it is missing"
    when = "hourly"

    def execute(self):
        for thread in Thread.objects.filter(
                starting_email__isnull=True).all():
            try:
                thread.starting_email = thread.emails.get(
                    parent_id__isnull=True)
            except Email.DoesNotExist:
                thread.starting_email = thread.emails.order_by("date").first()
                if thread.starting_email is None:
                    # No email, delete the thread
                    assert thread.emails.count() == 0
                    thread.delete()
                    continue
            thread.save()
