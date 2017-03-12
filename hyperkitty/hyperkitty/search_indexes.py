# -*- coding: utf-8 -*-
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

from haystack import indexes
from haystack.query import SearchQuerySet
from haystack.management.commands.update_index import \
    Command as UpdateIndexCommand
from hyperkitty.models import Email


class EmailIndex(indexes.SearchIndex, indexes.Indexable):

    text = indexes.CharField(document=True, use_template=True)
    mailinglist = indexes.CharField(model_attr='mailinglist__name')
    subject = indexes.CharField(model_attr='subject', boost=1.25,
                                use_template=True)
    date = indexes.DateTimeField(model_attr='date')
    sender = indexes.CharField(
        model_attr='sender_name', null=True, boost=1.125)
    tags = indexes.MultiValueField(
        model_attr='thread__tags__name', null=True, boost=1.25)
    archived_date = indexes.DateTimeField(model_attr='archived_date')

    def get_model(self):
        return Email

    def get_updated_field(self):
        return 'archived_date'

    def load_all_queryset(self):
        # Pull other objects related to the Email in search results.
        return self.get_model().objects.all().select_related(
            "sender", "thread")


def update_index(remove=False):
    """
    Update the search index with the new emails since the last index update.

    Setting remove to True is extremely slow, it needs to scan the entire
    index and database. It takes about 15 minutes on Fedora's lists, so it is
    not fit for a frequent operation.
    """
    update_cmd = UpdateIndexCommand()
    # Find the last email in the index:
    try:
        last_email = SearchQuerySet().latest('archived_date')
    except Exception:
        # Different backends can raise different exceptions unfortunately
        update_cmd.start_date = None
    else:
        update_cmd.start_date = last_email.archived_date
    # set defaults
    update_cmd.verbosity = 0
    update_cmd.batchsize = None
    update_cmd.end_date = None
    update_cmd.workers = 0
    update_cmd.commit = True
    update_cmd.remove = remove
    try:
        from haystack.management.commands.update_index import \
            DEFAULT_MAX_RETRIES
    except ImportError:
        pass
    else:
        update_cmd.max_retries = DEFAULT_MAX_RETRIES
    update_cmd.update_backend("hyperkitty", "default")
