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
Sync properties from Mailman into HyperKitty
"""

from __future__ import absolute_import, print_function, unicode_literals

from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from hyperkitty.lib.mailman import sync_with_mailman
from hyperkitty.management.utils import setup_logging


class Command(BaseCommand):
    help = "Sync properties from Mailman into HyperKitty"
    option_list = BaseCommand.option_list + (
        make_option(
            '--overwrite', action='store_true', default=False,
            help="overwrite existing Mailman IDs in HyperKitty's database"),
        )

    def handle(self, *args, **options):
        options["verbosity"] = int(options.get("verbosity", "1"))
        setup_logging(self, options["verbosity"])
        if args:
            raise CommandError("no arguments allowed")
        sync_with_mailman(overwrite=options.get("overwrite", False))
