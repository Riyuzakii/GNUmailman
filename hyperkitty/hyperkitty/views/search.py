# -*- coding: utf-8 -*-
#
# Copyright (C) 1998-2012 by the Free Software Foundation, Inc.
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

from django.conf import settings
from django.forms import ValidationError
from django.http import Http404
from django.shortcuts import render
from django.utils.translation import ugettext as _
from django_mailman3.lib.mailman import get_subscriptions
from django_mailman3.lib.paginator import paginate
from haystack import DEFAULT_ALIAS
from haystack.query import EmptySearchQuerySet, RelatedSearchQuerySet
from haystack.forms import SearchForm

from hyperkitty.models import MailingList, ArchivePolicy
from hyperkitty.lib.view_helpers import is_mlist_authorized


def search(request):
    """ Returns messages corresponding to a query """
    mlist_fqdn = request.GET.get("mlist")
    if mlist_fqdn is None:
        mlist = None
    else:
        try:
            mlist = MailingList.objects.get(name=mlist_fqdn)
        except MailingList.DoesNotExist:
            raise Http404("No archived mailing-list by that name.")
        if not is_mlist_authorized(request, mlist):
            return render(request, "hyperkitty/errors/private.html", {
                            "mlist": mlist,
                          }, status=403)
    query = ''
    results = EmptySearchQuerySet()
    sqs = RelatedSearchQuerySet()

    # Remove private non-subscribed lists
    if mlist is not None:
        sqs = sqs.filter(mailinglist__exact=mlist.name)
    else:
        excluded_mlists = MailingList.objects.filter(
            archive_policy=ArchivePolicy.private.value)
        if request.user.is_authenticated():
            subscriptions = get_subscriptions(request.user)
            excluded_mlists = excluded_mlists.exclude(
                list_id__in=subscriptions.keys())
        excluded_mlists = excluded_mlists.values_list("name", flat=True)
        sqs = sqs.exclude(mailinglist__in=excluded_mlists)

    # Sorting
    sort_mode = request.GET.get('sort')
    if sort_mode == "date-asc":
        sqs = sqs.order_by("date")
    elif sort_mode == "date-desc":
        sqs = sqs.order_by("-date")

    # Handle data
    if request.GET.get('q'):
        form = SearchForm(
            request.GET, searchqueryset=sqs, load_all=True)
        if form.is_valid():
            query = form.cleaned_data['q']
            results = form.search()
    else:
        form = SearchForm(searchqueryset=sqs, load_all=True)

    try:
        emails = paginate(
            results,
            request.GET.get('page'),
            request.GET.get('count'),
            )
    except Exception as e:
        backend = settings.HAYSTACK_CONNECTIONS[DEFAULT_ALIAS]["ENGINE"]
        if backend == "haystack.backends.whoosh_backend.WhooshEngine":
            from whoosh.qparser.common import QueryParserError
            search_exception = QueryParserError
        if backend == "xapian_backend.XapianEngine":
            from xapian import QueryParserError
            search_exception = QueryParserError
        if not isinstance(e, search_exception):
            raise
        emails = paginate([])
        form.add_error("q", ValidationError(
            _('Parsing error: %(error)s'),
            params={"error": e}, code="parse",
            ))
    for email in emails:
        if request.user.is_authenticated():
            email.object.myvote = email.object.votes.filter(
                user=request.user).first()
        else:
            email.object.myvote = None

    context = {
        'mlist': mlist,
        'form': form,
        'emails': emails,
        'query': query,
        'sort_mode': sort_mode,
        'suggestion': None,
    }
    if results.query.backend.include_spelling:
        context['suggestion'] = form.get_suggestion()

    return render(request, "hyperkitty/search_results.html", context)
