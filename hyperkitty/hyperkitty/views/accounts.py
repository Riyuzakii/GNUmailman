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

from __future__ import absolute_import, unicode_literals

from six.moves.urllib.error import HTTPError

import dateutil.parser
import mailmanclient

from allauth.account.models import EmailAddress
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse
from django.shortcuts import render
from django_mailman3.lib.mailman import (
    get_mailman_client, get_mailman_user_id, get_subscriptions)
from django_mailman3.lib.paginator import paginate

from hyperkitty.models import Favorite, LastView, MailingList, Email, Vote
from hyperkitty.lib.view_helpers import is_mlist_authorized


import logging
logger = logging.getLogger(__name__)


@login_required
def user_profile(request):
    # Get the messages and paginate them
    email_addresses = EmailAddress.objects.filter(
        user=request.user).values("email")
    last_posts = Email.objects.filter(
        sender__address__in=email_addresses).order_by("-date")
    last_posts = paginate(last_posts,
                          request.GET.get("lppage"),
                          request.GET.get("lpcount", "10"))

    context = {
        "last_posts": last_posts,
        "subpage": "profile",
    }
    return render(request, "hyperkitty/user_profile/profile.html", context)


@login_required
def favorites(request):
    # Favorite threads
    favs = Favorite.objects.filter(
        user=request.user).order_by("-thread__date_active")
    favs = paginate(favs, request.GET.get('favpage'))
    return render(request, 'hyperkitty/user_profile/favorites.html', {
                "favorites": favs,
                "subpage": "favorites",
            })


@login_required
def last_views(request):
    # Last viewed threads
    lviews = LastView.objects.filter(
        user=request.user).order_by("-view_date")
    lviews = paginate(lviews, request.GET.get('lvpage'))
    return render(request, 'hyperkitty/user_profile/last_views.html', {
                "last_views": lviews,
                "subpage": "last_views",
            })


@login_required
def votes(request):
    all_votes = paginate(
        request.user.votes.all(), request.GET.get('vpage'))
    return render(request, 'hyperkitty/user_profile/votes.html', {
                "votes": all_votes,
                "subpage": "votes",
            })


@login_required
def subscriptions(request):
    profile = request.user.hyperkitty_profile
    mm_user_id = get_mailman_user_id(request.user)
    subs = []
    for mlist_id in get_subscriptions(request.user):
        try:
            mlist = MailingList.objects.get(list_id=mlist_id)
        except MailingList.DoesNotExist:
            mlist = None  # no archived email yet
        posts_count = likes = dislikes = 0
        first_post = all_posts_url = None
        if mlist is not None:
            list_name = mlist.name
            posts_count = profile.emails.filter(
                mailinglist__name=mlist.name).count()
            likes, dislikes = profile.get_votes_in_list(mlist.name)
            first_post = profile.get_first_post(mlist)
            if mm_user_id is not None:
                all_posts_url = "%s?list=%s" % (
                    reverse("hk_user_posts", args=[mm_user_id]),
                    mlist.name)
        else:
            list_name = get_mailman_client().get_list(mlist_id).fqdn_listname
        likestatus = "neutral"
        if likes - dislikes >= 10:
            likestatus = "likealot"
        elif likes - dislikes > 0:
            likestatus = "like"
        subs.append({
            "list_name": list_name,
            "mlist": mlist,
            "posts_count": posts_count,
            "first_post": first_post,
            "likes": likes,
            "dislikes": dislikes,
            "likestatus": likestatus,
            "all_posts_url": all_posts_url,
        })
    return render(request, 'hyperkitty/user_profile/subscriptions.html', {
                "subscriptions": subs,
                "subpage": "subscriptions",
            })


def public_profile(request, user_id):
    class FakeMailmanUser(object):
        display_name = None
        created_on = None
        addresses = []
        subscription_list_ids = []
        user_id = None
    try:
        client = get_mailman_client()
        mm_user = client.get_user(user_id)
    except HTTPError:
        raise Http404("No user with this ID: %s" % user_id)
    except mailmanclient.MailmanConnectionError:
        mm_user = FakeMailmanUser()
        mm_user.user_id = user_id
    # XXX: don't list subscriptions, there's a privacy issue here.
    # # Subscriptions
    # subscriptions = get_subscriptions(mm_user, db_user)
    all_votes = Vote.objects.filter(email__sender__mailman_id=user_id)
    likes = all_votes.filter(value=1).count()
    dislikes = all_votes.filter(value=-1).count()
    likestatus = "neutral"
    if likes - dislikes >= 10:
        likestatus = "likealot"
    elif likes - dislikes > 0:
        likestatus = "like"
    # This is only used for the Gravatar. No email display on the public
    # profile, we have enough spam as it is, thank you very much.
    try:
        addresses = [unicode(addr) for addr in mm_user.addresses]
    except (KeyError, IndexError):
        addresses = []
    fullname = mm_user.display_name
    if not fullname:
        fullname = Email.objects.filter(sender__mailman_id=user_id).exclude(
                sender_name="", sender_name__isnull=True
            ).values_list("sender_name", flat=True).first()
    if mm_user.created_on is not None:
        creation = dateutil.parser.parse(mm_user.created_on)
    else:
        creation = None
    posts_count = Email.objects.filter(sender__mailman_id=user_id).count()
    is_user = request.user.is_authenticated() and bool(
        set([str(a) for a in mm_user.addresses]) &
        set(request.user.hyperkitty_profile.addresses))
    context = {
        "fullname": fullname,
        "creation": creation,
        "posts_count": posts_count,
        "likes": likes,
        "dislikes": dislikes,
        "likestatus": likestatus,
        "addresses": addresses,
        "is_user": is_user,
    }
    return render(request, "hyperkitty/user_public_profile.html", context)


def posts(request, user_id):
    mlist_fqdn = request.GET.get("list")
    if mlist_fqdn is None:
        mlist = None
        return HttpResponse("Not implemented yet", status=500)
    else:
        try:
            mlist = MailingList.objects.get(name=mlist_fqdn)
        except MailingList.DoesNotExist:
            raise Http404("No archived mailing-list by that name.")
        if not is_mlist_authorized(request, mlist):
            return render(request, "hyperkitty/errors/private.html", {
                            "mlist": mlist,
                          }, status=403)

    fullname = Email.objects.filter(
            sender__mailman_id=user_id, sender_name__isnull=False
        ).exclude(sender_name="").values_list(
        "sender_name", flat=True).first()
    # Get the messages and paginate them
    emails = Email.objects.filter(
        mailinglist=mlist, sender__mailman_id=user_id)
    emails = paginate(emails, request.GET.get("page"))

    for email in emails:
        email.myvote = email.votes.filter(user=request.user).first()

    context = {
        'user_id': user_id,
        'mlist': mlist,
        'emails': emails,
        'fullname': fullname,
    }
    return render(request, "hyperkitty/user_posts.html", context)
