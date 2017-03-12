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

from django.conf import settings
from django.contrib import admin
from django.db import models
from django.db.models.signals import pre_save, pre_delete
from django.dispatch import receiver
from django_mailman3.lib.cache import cache


class Vote(models.Model):
    """
    A User's vote on a message
    """
    email = models.ForeignKey("Email", related_name="votes")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="votes")
    value = models.SmallIntegerField(db_index=True)

    class Meta:
        unique_together = ("email", "user")

    def _clean_cache(self):
        """Delete cached vote values for Email and Thread instance"""
        cache.delete("Thread:%s:votes" % self.email.thread_id)
        # re-populate the cache?
        cache.delete("Email:%s:votes" % self.email_id)

    def on_pre_save(self):
        self._clean_cache()

    def on_pre_delete(self):
        self._clean_cache()

admin.site.register(Vote)  # noqa: E305


@receiver(pre_save, sender=Vote)
def on_pre_save(sender, **kwargs):
    kwargs["instance"].on_pre_save()


@receiver(pre_delete, sender=Vote)
def on_pre_delete(sender, **kwargs):
    kwargs["instance"].on_pre_delete()
