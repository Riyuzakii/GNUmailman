# -*- coding: utf-8 -*-
#
# Copyright (C) 2013-2016 by the Free Software Foundation, Inc.
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

from hyperkitty.models import Sender
from hyperkitty.tests.utils import TestCase


class SenderTestCase(TestCase):

    def test_set_mailman_id_invalid_address(self):
        # set_mailman_id: invalid email address given should silently do
        # nothing
        sender = Sender.objects.create(address="invalid email address")
        self.mailman_client.get_user.side_effect = ValueError
        try:
            sender.set_mailman_id()  # The ValueError should not be propagated
        except ValueError:
            self.fail("ValueError was raised")
