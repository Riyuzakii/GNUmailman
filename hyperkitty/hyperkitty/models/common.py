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

from __future__ import absolute_import, unicode_literals, print_function

from django_mailman3.lib.cache import cache


def get_votes(instance):
    from .thread import Thread
    from .email import Email
    from .vote import Vote

    def _getvalue():
        if isinstance(instance, Thread):
            filters = {"email__thread_id": instance.id}
        elif isinstance(instance, Email):
            filters = {"email_id": instance.id}
        else:
            ValueError("The 'get_votes' function only accepts 'Email' "
                       "and 'Thread' instance")
        votes = list(Vote.objects.filter(**filters).values_list(
            "value", flat=True))
        return (
                len([v for v in votes if v == 1]),
                len([v for v in votes if v == -1]),
            )

    cache_key = "%s:%s:votes" % (instance.__class__.__name__, instance.id)
    votes = cache.get_or_set(cache_key, _getvalue, None)
    likes, dislikes = votes
    # XXX: use an Enum?
    if likes - dislikes >= 10:
        status = "likealot"
    elif likes - dislikes > 0:
        status = "like"
    else:
        status = "neutral"
    return {"likes": likes, "dislikes": dislikes, "status": status}
