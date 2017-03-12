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

import datetime
from enum import Enum
from six.moves.urllib.error import HTTPError

import dateutil.parser
from django.conf import settings
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.timezone import now, utc
from django_mailman3.lib.cache import cache
from django_mailman3.lib.mailman import get_mailman_client
from mailmanclient import MailmanConnectionError

from .sender import Sender
from .thread import Thread

import logging
logger = logging.getLogger(__name__)


class ArchivePolicy(Enum):
    """
    Copy from mailman.interfaces.archiver.ArchivePolicy since we can't import
    mailman (PY3-only).

    This should probably be moved to mailman.client.
    """
    never = 0
    private = 1
    public = 2


class MailingList(models.Model):
    """
    An archived mailing-list.
    """
    name = models.CharField(max_length=254, primary_key=True)
    list_id = models.CharField(max_length=254, null=True, unique=True)
    display_name = models.CharField(max_length=255)
    description = models.TextField()
    subject_prefix = models.CharField(max_length=255)
    archive_policy = models.IntegerField(
        choices=[(p.value, p.name) for p in ArchivePolicy],
        default=ArchivePolicy.public.value)
    created_at = models.DateTimeField(default=now)

    MAILMAN_ATTRIBUTES = (
        "display_name", "description", "subject_prefix",
        "archive_policy", "created_at", "list_id",
    )

    @property
    def is_private(self):
        return self.archive_policy == ArchivePolicy.private.value

    @property
    def is_new(self):
        return self.created_at and \
                now() - self.created_at <= datetime.timedelta(days=30)

    def get_recent_dates(self):
        today = now()
        # today -= datetime.timedelta(days=400) #debug
        # the upper boundary is excluded in the search, add one day
        end_date = today + datetime.timedelta(days=1)
        begin_date = end_date - datetime.timedelta(days=32)
        return begin_date, end_date

    def get_participants_count_between(self, begin_date, end_date):
        # We filter on emails dates instead of threads dates because that would
        # also include last month's participants when threads carry from one
        # month to the next
        # TODO: caching?
        return self.emails.filter(
                date__gte=begin_date, date__lt=end_date
            ).values("sender_id").distinct().count()

    def get_threads_between(self, begin_date, end_date):
        return self.threads.filter(
                starting_email__date__lt=end_date,
                date_active__gte=begin_date
            ).order_by("-date_active")

    @property
    def recent_participants_count(self):
        begin_date, end_date = self.get_recent_dates()
        return cache.get_or_set(
            "MailingList:%s:recent_participants_count" % self.name,
            lambda: self.get_participants_count_between(begin_date, end_date),
            3600 * 6)  # 6 hours

    @property
    def recent_threads(self):
        begin_date, end_date = self.get_recent_dates()
        # Only cache the list of thread ids, or it may go over memcached's size
        # limit (1MB)
        cache_key = "MailingList:%s:recent_threads" % self.name
        thread_ids = cache.get(cache_key)
        if thread_ids is None:
            threads = self.get_threads_between(begin_date, end_date)
            cache.set(cache_key, [t.id for t in threads], 3600 * 12)  # 12h
        else:
            threads = Thread.objects.filter(id__in=thread_ids)
        return threads

    @property
    def recent_threads_count(self):
        begin_date, end_date = self.get_recent_dates()
        cache_key = "MailingList:%s:recent_threads_count" % self.name
        result = cache.get(cache_key)
        if result is None:
            result = self.get_threads_between(begin_date, end_date).count()
            cache.set(cache_key, result, 3600 * 12)  # 12 hours
        return result

    def _recent_threads_cache_rebuild(self):
        begin_date, end_date = self.get_recent_dates()
        cache_key = "MailingList:%s:recent_threads" % self.name
        cache.delete(cache_key)
        cache.delete("%s_count" % cache_key)
        # don't warm up the cache in batch mode (mass import)
        if not getattr(settings, "HYPERKITTY_BATCH_MODE", False):
            thread_ids = list(self.get_threads_between(
                begin_date, end_date).values_list("id", flat=True))
            cache.set(cache_key, thread_ids, 3600 * 12)  # 12 hours
            cache.set("%s_count" % cache_key, len(thread_ids), 3600 * 12)

    def on_thread_added(self, thread):
        cache_key = "MailingList:%s:recent_threads" % self.name
        recent_thread_ids = cache.get(cache_key)
        if recent_thread_ids is not None and len(recent_thread_ids) >= 1000:
            # It's a high-volume list, just append to the cache
            recent_thread_ids.append(thread.id)
            cache.set(cache_key, recent_thread_ids, 3600 * 12)  # 12 hours
            cache.set("%s_count" % cache_key,
                      len(recent_thread_ids), 3600 * 12)  # 12 hours
        else:
            # Low-volume list, rebuild the cache
            self._recent_threads_cache_rebuild()

    def on_thread_deleted(self, thread):
        self._recent_threads_cache_rebuild()

    def get_participants_count_for_month(self, year, month):
        def _get_value():
            begin_date = datetime.datetime(year, month, 1, tzinfo=utc)
            end_date = begin_date + datetime.timedelta(days=32)
            end_date = end_date.replace(day=1)
            return self.get_participants_count_between(begin_date, end_date)
        return cache.get_or_set(
            "MailingList:%s:p_count_for:%s:%s" % (self.name, year, month),
            _get_value, None)

    @property
    def top_posters(self):
        def _get_posters():
            from .email import Email  # avoid circular imports
            begin_date, end_date = self.get_recent_dates()
            query = Email.objects.filter(
                mailinglist=self,
                date__gte=begin_date,
                date__lt=end_date,
            ).only("sender", "sender_name"
            ).select_related("sender__address")
            posters = {}
            for email in query:
                key = (email.sender.address, email.sender_name)
                if key not in posters:
                    posters[key] = 1
                else:
                    posters[key] += 1
            posters = [
                {"address": p[0], "name": p[1], "count": c}
                for p, c in posters.items()
                ]
            sorted_posters = sorted(
                posters, key=lambda p: p["count"], reverse=True)
            return sorted_posters[:5]
        return cache.get_or_set(
            "MailingList:%s:top_posters" % self.name,
            _get_posters,
            3600 * 6)  # 6 hours
        # It's not actually necessary to convert back to instances since it's
        # only used in templates where access to instance attributes or
        # dictionnary keys is identical

    def update_from_mailman(self):
        try:
            client = get_mailman_client()
            mm_list = client.get_list(self.name)
        except MailmanConnectionError:
            return
        except HTTPError:
            return  # can't update at this time
        if not mm_list:
            return

        def convert_date(value):
            value = dateutil.parser.parse(value)
            if value.tzinfo is None:
                value = value.replace(tzinfo=utc)
            return value
        converters = {
            "created_at": convert_date,
            "archive_policy": lambda p: ArchivePolicy[p].value,
        }
        for propname in self.MAILMAN_ATTRIBUTES:
            try:
                value = getattr(mm_list, propname)
            except AttributeError:
                value = mm_list.settings[propname]
            if propname in converters:
                value = converters[propname](value)
            setattr(self, propname, value)
        self.save()

    def on_pre_save(self):
        # Set the default list_id
        if self.list_id is None:
            self.list_id = self.name.replace("@", ".")


@receiver(pre_save, sender=MailingList)
def MailingList_set_list_id(sender, **kwargs):
    kwargs["instance"].on_pre_save()
