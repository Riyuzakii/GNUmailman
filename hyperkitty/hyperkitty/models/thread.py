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

from collections import namedtuple
from django.conf import settings
from django.db import models
from django.db.models.signals import post_delete, pre_save
from django.contrib import admin
from django.dispatch import receiver
from django.utils.timezone import now, utc
from django_mailman3.lib.cache import cache

from hyperkitty.lib.signals import new_thread
from .common import get_votes


import logging
logger = logging.getLogger(__name__)


class Thread(models.Model):
    """
    A thread of archived email, from a mailing-list. It is identified by both
    the list name and the thread id.
    """
    mailinglist = models.ForeignKey("MailingList", related_name="threads")
    thread_id = models.CharField(max_length=255, db_index=True)
    date_active = models.DateTimeField(db_index=True, default=now)
    category = models.ForeignKey(
        "ThreadCategory", related_name="threads", null=True,
        on_delete=models.SET_NULL)
    starting_email = models.OneToOneField(
        "Email", related_name="started_thread", null=True,
        on_delete=models.SET_NULL)

    class Meta:
        unique_together = ("mailinglist", "thread_id")

    @property
    def participants(self):
        """Set of email senders in this thread"""
        from .email import Email
        Participant = namedtuple("Participant", ["name", "address"])
        return [
            Participant(name=e["sender_name"], address=e["sender__address"])
            for e in Email.objects.filter(thread_id=self.id).values(
                "sender__address", "sender_name").distinct()
            ]

    @property
    def participants_count(self):
        return cache.get_or_set(
            "Thread:%s:participants_count" % self.id,
            lambda: len(self.participants),
            None)

    def replies_after(self, date):
        return self.emails.filter(date__gt=date)

    # def _get_category(self):
    #     if not self.category_id:
    #         return None
    #     return self.category_obj.name
    # def _set_category(self, name):
    #     if not name:
    #         self.category_id = None
    #         return
    #     session = object_session(self)
    #     try:
    #         category = session.query(Category).filter_by(name=name).one()
    #     except NoResultFound:
    #         category = Category(name=name)
    #         session.add(category)
    #     self.category_id = category.id
    # category = property(_get_category, _set_category)

    @property
    def emails_count(self):
        return cache.get_or_set(
            "Thread:%s:emails_count" % self.id,
            lambda: self.emails.count(),
            None)

    @property
    def subject(self):
        return cache.get_or_set(
            "Thread:%s:subject" % self.id,
            lambda: self.starting_email.subject,
            None)

    def get_votes(self):
        return get_votes(self)

    @property
    def prev_thread(self):  # TODO: Make it a relationship
        return Thread.objects.filter(
                mailinglist=self.mailinglist,
                date_active__lt=self.date_active
            ).order_by("-date_active").first()

    @property
    def next_thread(self):  # TODO: Make it a relationship
        return Thread.objects.filter(
                mailinglist=self.mailinglist,
                date_active__gt=self.date_active
            ).order_by("date_active").first()

    def is_unread_by(self, user):
        if not user.is_authenticated():
            return False
        try:
            last_view = LastView.objects.get(thread=self, user=user)
        except LastView.DoesNotExist:
            return True
        except LastView.MultipleObjectsReturned:
            last_view_duplicate, last_view = LastView.objects.filter(
                thread=self, user=user).order_by("view_date").all()
            last_view_duplicate.delete()
        return self.date_active.replace(tzinfo=utc) > last_view.view_date

    def find_starting_email(self):
        # Find and set the staring email if it was not specified
        from .email import Email  # circular import
        if self.starting_email is not None:
            return
        try:
            self.starting_email = self.emails.get(parent_id__isnull=True)
        except Email.DoesNotExist:
            self.starting_email = self.emails.order_by("date").first()

    def on_pre_save(self):
        self.find_starting_email()

    def on_new_thread(self):
        self.mailinglist.on_thread_added(self)

    def on_post_delete(self):
        self.mailinglist.on_thread_deleted(self)


@receiver(pre_save, sender=Thread)
def on_pre_save(sender, **kwargs):
    kwargs["instance"].on_pre_save()


@receiver(new_thread)
def on_new_thread(sender, **kwargs):
    kwargs["thread"].on_new_thread()


@receiver(post_delete, sender=Thread)
def on_post_delete(sender, **kwargs):
    kwargs["instance"].on_post_delete()


# @receiver(new_thread)
# def cache_thread_subject(sender, **kwargs):
#     thread = kwargs["instance"]
#     thread.subject


class LastView(models.Model):
    thread = models.ForeignKey("Thread", related_name="lastviews")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="lastviews")
    view_date = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        """Unicode representation"""
        return u"Last view of %s by %s was %s" % (
            unicode(self.thread), unicode(self.user),
            self.view_date.isoformat())

    def num_unread(self):
        if self.thread.date_active.replace(tzinfo=utc) <= self.view_date:
            return 0  # avoid the expensive query below
        else:
            return self.thread.emails.filter(date__gt=self.view_date).count()

admin.site.register(LastView)  # noqa: E305
