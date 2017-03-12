# -*- coding: utf-8 -*-
# Copyright (C) 1998-2016 by the Free Software Foundation, Inc.
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


from __future__ import absolute_import, unicode_literals

from django.views.generic import TemplateView
from django_mailman3.lib.mailman import get_mailman_client

from postorius.models import List
from postorius.auth.utils import set_user_access_props


class MailmanClientMixin(object):

    """Adds a mailmanclient.Client instance."""

    def client(self):
        if getattr(self, '_client', None) is None:
            self._client = get_mailman_client()
        return self._client


class MailingListView(TemplateView, MailmanClientMixin):

    """A generic view for everything based on a mailman.client
    list object.

    Sets self.mailing_list to list object if list_id is in **kwargs.
    """

    def _get_list(self, list_id, page):
        return List.objects.get_or_404(fqdn_listname=list_id)

    def dispatch(self, request, *args, **kwargs):
        # get the list object.
        if 'list_id' in kwargs:
            self.mailing_list = self._get_list(kwargs['list_id'],
                                               int(kwargs.get('page', 1)))
            set_user_access_props(request.user, self.mailing_list)
        # set the template
        if 'template' in kwargs:
            self.template = kwargs['template']
        return super(MailingListView, self).dispatch(request, *args, **kwargs)
