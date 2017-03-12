# -*- coding: utf-8 -*-
#
# Copyright (C) 2014-2015 by the Free Software Foundation, Inc.
#
# This file is part of HyperKitty.
#
# HyperKitty is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# HyperKitty is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# HyperKitty.  If not, see <http://www.gnu.org/licenses/>.
#
# Author: Aurelien Bompard <abompard@fedoraproject.org>
#

from __future__ import absolute_import, print_function, unicode_literals

import datetime

from django.utils.timezone import utc

from hyperkitty.lib.view_helpers import get_display_dates
from hyperkitty.tests.utils import TestCase


class GetDisplayDatesTestCase(TestCase):

    def test_month(self):
        begin_date, end_date = get_display_dates('2012', '6', None)
        self.assertEqual(begin_date, datetime.datetime(2012, 6, 1, tzinfo=utc))
        self.assertEqual(end_date, datetime.datetime(2012, 7, 1, tzinfo=utc))

    def test_month_december(self):
        try:
            begin_date, end_date = get_display_dates('2012', '12', None)
        except ValueError as e:
            self.fail(e)
        self.assertEqual(
            begin_date, datetime.datetime(2012, 12, 1, tzinfo=utc))
        self.assertEqual(end_date, datetime.datetime(2013, 1, 1, tzinfo=utc))

    def test_day(self):
        begin_date, end_date = get_display_dates('2012', '4', '2')
        self.assertEqual(begin_date, datetime.datetime(2012, 4, 2, tzinfo=utc))
        self.assertEqual(end_date, datetime.datetime(2012, 4, 3, tzinfo=utc))
