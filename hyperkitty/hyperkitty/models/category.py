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

from django.contrib import admin
from django.db import models
from paintstore.fields import ColorPickerField


class ThreadCategory(models.Model):
    name = models.CharField(max_length=255, db_index=True, unique=True)
    color = ColorPickerField()

    class Meta:
        verbose_name_plural = "Thread categories"

    def __unicode__(self):
        return u'Thread category "%s"' % (unicode(self.name))


class ThreadCategoryAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        obj.name = obj.name.lower()
        return super(ThreadCategoryAdmin, self).save_model(
                     request, obj, form, change)

admin.site.register(ThreadCategory, ThreadCategoryAdmin)  # noqa: E305
