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

from allauth.account.models import EmailAddress
from allauth.account.signals import (
    email_confirmed, user_signed_up, user_logged_in, email_removed)
from allauth.socialaccount.signals import social_account_added
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from django_mailman3.lib.mailman import (
    add_address_to_mailman_user, get_mailman_user, sync_email_addresses)
from django_mailman3.models import Profile


import logging
logger = logging.getLogger(__name__)


# Create a Profile when a User is created
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_profile(sender, **kwargs):
    user = kwargs["instance"]
    if not Profile.objects.filter(user=user).exists():
        Profile.objects.create(user=user)


# Allauth


@receiver(user_logged_in)
def on_user_logged_in(sender, **kwargs):
    # Sent when a user logs in.
    user = kwargs["user"]
    if not Profile.objects.filter(user=user).exists():
        Profile.objects.create(user=user)
    sync_email_addresses(user)


@receiver(user_signed_up)
def on_user_signed_up(sender, **kwargs):
    # Sent when a user signs up for an account.
    user = kwargs["user"]
    if not Profile.objects.filter(user=user).exists():
        Profile.objects.create(user=user)
    # We want to add the user to Mailman with all its verified email addresses.
    for address in EmailAddress.objects.filter(user=user):
        if address.verified:
            logger.debug("Adding email address %s to user %s",
                         address.email, user.username)
            add_address_to_mailman_user(user, address.email)


@receiver(email_removed)
def on_email_removed(sender, **kwargs):
    # Sent when an email address has been removed.
    # Remove it from Mailman.
    user = kwargs["user"]
    email_address = kwargs["email_address"]
    mm_user = get_mailman_user(user)
    if mm_user is None:
        return  # Could not get the user from Mailman.
    try:
        mm_user.addresses.remove(email_address.email)
    except ValueError:
        pass  # not in Mailman's addresses


@receiver(email_confirmed)
def on_email_confirmed(sender, **kwargs):
    # Sent after the email address in the db was updated and set to confirmed.
    # Associate it with the user and set it to verified in Mailman.
    email_address = kwargs["email_address"]
    logger.debug("Confirmed email %s of user %s",
                 email_address.email, email_address.user.username)
    add_address_to_mailman_user(email_address.user, email_address.email)


# from django_mailman3.lib.mailman import get_mailman_client
# @receiver(email_changed)
# def on_email_changed(sender, **kwargs):
#     # Sent when a primary email address has been changed.
#     user = get_mailman_client().get_user(kwargs['user'].email)
#     # TODO: propagate to Mailman


@receiver(social_account_added)
def on_social_account_added(sender, **kwargs):
    # Sent after a user connects a social account to a their local account.
    # Add to mailman emails that were marked as verified by the social account
    # provider.
    sociallogin = kwargs["sociallogin"]
    logger.debug("Social account %s added for user %s",
                 sociallogin.account, sociallogin.user.username)
    for address in sociallogin.email_addresses:
        if EmailAddress.objects.filter(email=address.email).exists():
            # TODO: should we do something if it belongs so another user?
            continue
        logger.debug("Adding email address %s to user %s",
                     address.email, sociallogin.user.username)
        address.user = sociallogin.user
        address.primary = False  # There already is a primary address.
        address.save()
        if address.verified:
            add_address_to_mailman_user(sociallogin.user, address.email)
