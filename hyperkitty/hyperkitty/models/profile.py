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


from allauth.account.models import EmailAddress
from django.conf import settings
from django.contrib import admin
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from .email import Email


import logging
logger = logging.getLogger(__name__)


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL,
                                related_name="hyperkitty_profile")
    karma = models.IntegerField(default=1)

    def __unicode__(self):
        return u'%s' % (unicode(self.user))

    @property
    def emails(self):
        return Email.objects.filter(
            sender__address__in=self.addresses).order_by("date")

    @property
    def addresses(self):
        return list(EmailAddress.objects.filter(
            user=self.user).filter(
            verified=True).order_by("email").values_list(
            "email", flat=True))

    def get_votes_in_list(self, list_name):
        # TODO: Caching ?
        votes = self.user.votes.filter(email__mailinglist__name=list_name)
        likes = votes.filter(value=1).count()
        dislikes = votes.filter(value=-1).count()
        return likes, dislikes

    def get_first_post(self, mlist):
        return self.emails.filter(
            mailinglist=mlist).order_by("archived_date").first()

admin.site.register(Profile)  # noqa: E305


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_profile(sender, **kwargs):
    user = kwargs["instance"]
    if not Profile.objects.filter(user=user).exists():
        Profile.objects.create(user=user)
