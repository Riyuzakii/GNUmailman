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


class Tagging(models.Model):

    thread = models.ForeignKey("Thread")
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    tag = models.ForeignKey("Tag")

    def __unicode__(self):
        return 'Tag %s on %s by %s' % (
            unicode(self.tag), unicode(self.thread), unicode(self.user))


class Tag(models.Model):

    name = models.CharField(max_length=255, db_index=True, unique=True)
    threads = models.ManyToManyField(
        "Thread", through="Tagging", related_name="tags")
    users = models.ManyToManyField(
        settings.AUTH_USER_MODEL, through="Tagging", related_name="tags")

    class Meta:
        ordering = ["name"]

    def __unicode__(self):
        return 'Tag %s' % (unicode(self.name))

admin.site.register(Tag)  # noqa: E305
