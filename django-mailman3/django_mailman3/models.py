# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 by the Free Software Foundation, Inc.
#
# This file is part of Django-Mailman.
#
# Django-Mailman is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# Django-Mailman is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# Django-Mailman.  If not, see <http://www.gnu.org/licenses/>.
#
# Author: Aurelien Bompard <abompard@fedoraproject.org>
#

from __future__ import absolute_import, unicode_literals

import pytz

from django.conf import settings
from django.contrib import admin
from django.contrib.sites.models import Site
from django.db import models


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL,
                                related_name="mailman_profile")
    TIMEZONES = sorted([(tz, tz) for tz in pytz.common_timezones])
    timezone = models.CharField(max_length=100, choices=TIMEZONES, default="")

    def __unicode__(self):
        return '<Mailman profile for %s>' % (unicode(self.user.username))


admin.site.register(Profile)


class MailDomain(models.Model):
    site = models.ForeignKey(Site, related_name="mailman_domains")
    mail_domain = models.CharField(max_length=255, db_index=True, unique=True)

    def __unicode__(self):
        return '<Mailman domain %s>' % (unicode(self.mail_domain))


admin.site.register(MailDomain)
