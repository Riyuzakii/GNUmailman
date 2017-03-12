# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 by the Free Software Foundation, Inc.
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

"""
Inpired by
https://www.caktusgroup.com/blog/2016/02/02/writing-unit-tests-django-migrations/
"""

from __future__ import absolute_import, print_function, unicode_literals

from django.utils.timezone import now
from hyperkitty.tests.utils import MigrationTestCase


class DuplicatePersonUsersTestCase(MigrationTestCase):

    migrate_from = '0008_django_mailman3_profile'
    migrate_to = '0009_duplicate_persona_users'

    def _make_user(self):
        User = self.old_apps.get_model("auth", "User")
        user_persona = User.objects.create(
            username="via_persona", email="user@example.com")
        user_openid = User.objects.create(
            username="via_openid", email="user@example.com")
        SocialAccount = self.old_apps.get_model(
            "socialaccount", "SocialAccount")
        SocialAccount.objects.create(
            user=user_openid, provider="openid",
            uid="http://user.example.com")
        return user_persona

    def test_duplicate_user(self):
        self._make_user()
        new_apps = self.migrate()
        User = new_apps.get_model("auth", "User")
        self.assertEqual(User.objects.all().count(), 1)
        user = User.objects.all().first()
        self.assertEqual(user.username, "via_openid")

    def test_duplicate_user_with_data(self):
        user_persona = self._make_user()

        MailingList = self.old_apps.get_model("hyperkitty", "MailingList")
        ml = MailingList.objects.create(name="list@example.com")

        Thread = self.old_apps.get_model("hyperkitty", "Thread")
        thread = Thread.objects.create(
            mailinglist=ml,
            thread_id="test")

        Sender = self.old_apps.get_model("hyperkitty", "Sender")
        Email = self.old_apps.get_model("hyperkitty", "Email")
        email = Email.objects.create(
            mailinglist=ml,
            sender=Sender.objects.create(address="user@example.com"),
            thread=thread,
            subject="test", content="test",
            date=now(), timezone=0,
            message_id_hash="test")

        Tag = self.old_apps.get_model("hyperkitty", "Tag")
        Tagging = self.old_apps.get_model("hyperkitty", "Tagging")
        Tagging.objects.create(
            user=user_persona,
            tag=Tag.objects.create(name="testtag"),
            thread=thread)

        Favorite = self.old_apps.get_model("hyperkitty", "Favorite")
        Favorite.objects.create(user=user_persona, thread=thread)

        LastView = self.old_apps.get_model("hyperkitty", "LastView")
        LastView.objects.create(user=user_persona, thread=thread)

        Vote = self.old_apps.get_model("hyperkitty", "Vote")
        Vote.objects.create(user=user_persona, email=email, value=1)

        new_apps = self.migrate()
        User = new_apps.get_model("auth", "User")
        user = User.objects.all().first()
        self.assertIsNotNone(user)
        self.assertEqual(user.tags.count(), 1)
        self.assertEqual(user.favorites.count(), 1)
        self.assertEqual(user.lastviews.count(), 1)
        self.assertEqual(user.votes.count(), 1)
