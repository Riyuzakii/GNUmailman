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
Import new lists from Mailman over REST.
Those lists have no archived email yet.
"""

from __future__ import absolute_import, print_function, unicode_literals

from django_extensions.management.jobs import BaseJob
from hyperkitty.lib.mailman import get_new_lists_from_mailman


class Job(BaseJob):
    help = "Import new lists from Mailman"
    when = "hourly"

    def execute(self):
        get_new_lists_from_mailman()
