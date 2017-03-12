# -*- coding: utf-8 -*-
# Copyright (C) 1998-2015 by the Free Software Foundation, Inc.
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

from django.core.management.base import BaseCommand
from django_mailman3.lib.mailman import get_mailman_client


class Command(BaseCommand):
    help = """Opens a Python shell with a mailmanclient object named `client`.

Usage example:
    client.lists
    [<List "foo@example.org">]
    foo = client.get_list('foo@example.org')
    foo.members
    [<Member "les@primus.org">]

A complete list of commands can be found in the mailmanclient documentation."""

    def handle(self, *args, **options):
        # choose an interpreter
        try:
            import IPython
            console_fn = IPython.embed
        except ImportError:
            import code
            shell = code.InteractiveConsole(globals())
            console_fn = shell.interact
        # connect to mailmanclient
        client = get_mailman_client()
        # Putting client back in the global scope
        globals()['client'] = client
        # run the interpreter
        console_fn()
