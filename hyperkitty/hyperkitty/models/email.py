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

import re
from email.charset import Charset, QP
from email.encoders import encode_base64
from email.header import Header
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.nonmultipart import MIMENonMultipart

from django.conf import settings
from django.core.cache.utils import make_template_fragment_key
from django.db import models, IntegrityError
from django.db.models.signals import (
    post_init, pre_save, post_save, pre_delete, post_delete)
from django.dispatch import receiver
from django.utils.timezone import now, get_fixed_timezone
from django_mailman3.lib.cache import cache

from hyperkitty.lib.analysis import compute_thread_order_and_depth
from .common import get_votes
from .mailinglist import MailingList
from .thread import Thread
from .vote import Vote

import logging
logger = logging.getLogger(__name__)


class Email(models.Model):
    """
    An archived email, from a mailing-list. It is identified by both the list
    name and the message id.
    """
    mailinglist = models.ForeignKey("MailingList", related_name="emails")
    message_id = models.CharField(max_length=255, db_index=True)
    message_id_hash = models.CharField(max_length=255, db_index=True)
    sender = models.ForeignKey("Sender", related_name="emails")
    sender_name = models.CharField(max_length=255, null=True, blank=True)
    subject = models.CharField(max_length=512, db_index=True)
    content = models.TextField()
    date = models.DateTimeField(db_index=True)
    timezone = models.SmallIntegerField()
    in_reply_to = models.CharField(
        max_length=255, null=True, blank=True, db_index=True)
    parent = models.ForeignKey(
        "self", blank=True, null=True, on_delete=models.SET_NULL,
        related_name="children")
    thread = models.ForeignKey("Thread", related_name="emails")
    archived_date = models.DateTimeField(default=now, db_index=True)
    thread_depth = models.IntegerField(default=0)
    thread_order = models.IntegerField(default=0, db_index=True)

    ADDRESS_REPLACE_RE = re.compile(r"([\w.+-]+)@([\w.+-]+)")

    class Meta:
        unique_together = ("mailinglist", "message_id")

    def get_votes(self):
        return get_votes(self)

    def vote(self, value, user):
        # Checks if the user has already voted for this message.
        existing = self.votes.filter(user=user).first()
        if existing is not None and existing.value == value:
            return  # Vote already recorded (should I raise an exception?)
        if value not in (0, 1, -1):
            raise ValueError("A vote can only be +1 or -1 (or 0 to cancel)")
        if existing is not None:
            # vote changed or cancelled
            if value == 0:
                existing.delete()
            else:
                existing.value = value
                existing.save()
        else:
            # new vote
            vote = Vote(email=self, user=user, value=value)
            vote.save()

    def set_parent(self, parent):
        if self.id == parent.id:
            raise ValueError("An email can't be its own parent")
        # Compute the subthread
        subthread = [self]

        def _collect_children(current_email):
            children = list(current_email.children.all())
            if not children:
                return
            subthread.extend(children)
            for child in children:
                _collect_children(child)
        _collect_children(self)
        # now set my new parent value
        old_parent_id = self.parent_id
        self.parent = parent
        self.save(update_fields=["parent_id"])
        # If my future parent is in my current subthread, I need to set its
        # parent to my current parent
        if parent in subthread:
            parent.parent_id = old_parent_id
            parent.save(update_fields=["parent_id"])
            # do it after setting the new parent_id to avoid having two
            # parent_ids set to None at the same time (IntegrityError)
        if self.thread_id != parent.thread_id:
            # we changed the thread, reattach the subthread
            former_thread = self.thread
            for child in subthread:
                child.thread = parent.thread
                child.save(update_fields=["thread_id"])
                if child.date > parent.thread.date_active:
                    parent.thread.date_active = child.date
            parent.thread.save()
            # if we were the starting email, or former thread may be empty
            if former_thread.emails.count() == 0:
                former_thread.delete()
        compute_thread_order_and_depth(parent.thread)

    def as_message(self, escape_addresses=True):
        # http://wordeology.com/computer/how-to-send-good-unicode-email-with-python.html
        # http://stackoverflow.com/questions/31714221/how-to-send-an-email-with-quoted
        # http://stackoverflow.com/questions/9403265/how-do-i-use-python/9509718#9509718
        charset = Charset('utf-8')
        charset.header_encoding = QP
        charset.body_encoding = QP
        msg = MIMEMultipart()

        # Headers
        unixfrom = "From %s %s" % (
            self.sender.address, self.archived_date.strftime("%c"))
        header_from = self.sender.address
        if self.sender_name and self.sender_name != self.sender.address:
            header_from = "%s <%s>" % (self.sender_name, header_from)
        header_to = self.mailinglist.name
        if escape_addresses:
            header_from = header_from.replace("@", " at ")
            header_to = header_to.replace("@", " at ")
            unixfrom = unixfrom.replace("@", " at ")
        msg.set_unixfrom(unixfrom)
        headers = (
            ("From", header_from),
            ("To", header_to),
            ("Subject", self.subject),
            )
        for header_name, header_value in headers:
            if not header_value:
                continue
            try:
                msg[header_name] = header_value.encode('ascii')
            except UnicodeEncodeError:
                msg[header_name] = Header(
                    header_value.encode('utf-8'), charset).encode()
        tz = get_fixed_timezone(self.timezone)
        header_date = self.date.astimezone(tz).replace(microsecond=0)
        # Date format: http://tools.ietf.org/html/rfc5322#section-3.3
        msg["Date"] = header_date.strftime("%a, %d %b %Y %H:%M:%S %z")
        msg["Message-ID"] = "<%s>" % self.message_id
        if self.in_reply_to:
            msg["In-Reply-To"] = self.in_reply_to

        # Body
        content = self.ADDRESS_REPLACE_RE.sub(r"\1(a)\2", self.content)
        # Don't use MIMEText, it won't encode to quoted-printable
        textpart = MIMENonMultipart("text", "plain", charset='utf-8')
        textpart.set_payload(content, charset=charset)
        msg.attach(textpart)

        # Attachments
        for attachment in self.attachments.order_by("counter"):
            mimetype = attachment.content_type.split('/', 1)
            part = MIMEBase(mimetype[0], mimetype[1])
            part.set_payload(attachment.content)
            encode_base64(part)
            part.add_header('Content-Disposition', 'attachment',
                            filename=attachment.name)
            msg.attach(part)

        return msg

    @property
    def display_fixed(self):
        return "@@" in self.content

    def _set_message_id_hash(self):
        from hyperkitty.lib.utils import get_message_id_hash  # circular import
        if not self.message_id_hash:
            self.message_id_hash = get_message_id_hash(self.message_id)

    def _refresh_count_cache(self):
        cache.delete("Thread:%s:emails_count" % self.thread_id)
        cache.delete("Thread:%s:participants_count" % self.thread_id)
        cache.delete("MailingList:%s:recent_participants_count"
                     % self.mailinglist_id)
        cache.delete(make_template_fragment_key(
            "thread_participants", [self.thread_id]))
        cache.delete("MailingList:%s:p_count_for:%s:%s"
                     % (self.mailinglist_id, self.date.year, self.date.month))
        # don't warm up the cache in batch mode (mass import)
        if not getattr(settings, "HYPERKITTY_BATCH_MODE", False):
            try:
                self.thread.emails_count
                self.thread.participants_count
                self.mailinglist.recent_participants_count
                self.mailinglist.get_participants_count_for_month(
                    self.date.year, self.date.month)
            except (Thread.DoesNotExist, MailingList.DoesNotExist):
                pass  # it's post_delete, those may have been deleted too

    def on_post_init(self):
        self._set_message_id_hash()

    def on_post_created(self):
        # refresh the count cache
        self._refresh_count_cache()

    def on_pre_save(self):
        self._set_message_id_hash()
        # Make sure there is only one email with parent_id == None in a thread
        if self.parent_id is not None:
            return
        starters = Email.objects.filter(
                thread=self.thread, parent_id__isnull=True
            ).values_list("id", flat=True)
        if len(starters) > 0 and list(starters) != [self.id]:
            raise IntegrityError("There can be only one email with "
                                 "parent_id==None in the same thread")

    def on_post_save(self):
        pass

    def on_pre_delete(self):
        # Reset parent_id
        children = self.children.order_by("date")
        if not children:
            return
        if self.parent is None:
            #  Temporarily set the email's parent_id to not None, to allow the
            #  next email to be the starting email (there's a check on_save for
            #  duplicate thread starters)
            self.parent = self
            self.save(update_fields=["parent"])
            starter = children[0]
            starter.parent = None
            starter.save(update_fields=["parent"])
            children.all().update(parent=starter)
        else:
            children.update(parent=self.parent)

    def on_post_delete(self):
        # refresh the count cache
        self._refresh_count_cache()
        # update_or_clean_thread
        try:
            thread = Thread.objects.get(id=self.thread_id)
        except Thread.DoesNotExist:
            return
        if thread.emails.count() == 0:
            thread.delete()
        else:
            if thread.starting_email is None:
                thread.find_starting_email()
                thread.save(update_fields=["starting_email"])
            compute_thread_order_and_depth(thread)


@receiver(post_init, sender=Email)
def Email_on_post_init(sender, **kwargs):
    kwargs["instance"].on_post_init()


@receiver(pre_save, sender=Email)
def Email_on_pre_save(sender, **kwargs):
    kwargs["instance"].on_pre_save()


@receiver(post_save, sender=Email)
def Email_on_post_save(sender, **kwargs):
    if kwargs["created"]:
        kwargs["instance"].on_post_created()
    else:
        kwargs["instance"].on_post_save()


@receiver(pre_delete, sender=Email)
def Email_on_pre_delete(sender, **kwargs):
    kwargs["instance"].on_pre_delete()


@receiver(post_delete, sender=Email)
def Email_on_post_delete(sender, **kwargs):
    kwargs["instance"].on_post_delete()


class Attachment(models.Model):
    email = models.ForeignKey("Email", related_name="attachments")
    counter = models.SmallIntegerField()
    name = models.CharField(max_length=255)
    content_type = models.CharField(max_length=255)
    encoding = models.CharField(max_length=255, null=True)
    size = models.IntegerField()
    content = models.BinaryField()

    class Meta:
        unique_together = ("email", "counter")

    def on_pre_save(self):
        # set the size
        self.size = len(self.content)


@receiver(pre_save, sender=Attachment)
def Attachment_on_pre_save(sender, **kwargs):
    kwargs["instance"].on_pre_save()
