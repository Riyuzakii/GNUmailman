# -*- coding: utf-8 -*-
# Copyright (C) 1998-2012 by the Free Software Foundation, Inc.
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
Class implementation of Mailman's IArchiver interface
This will be imported by Mailman Core and must thus be Python3-compatible.
"""

from __future__ import absolute_import, unicode_literals

import os
import requests
import traceback

from email.errors import MessageError
from io import StringIO
from mailman.interfaces.archiver import IArchiver
from mailman.config import config
from mailman.config.config import external_configuration
from mailman.core.switchboard import Switchboard
from urllib.parse import urljoin
from zope.interface import implementer

import logging
logger = logging.getLogger("mailman.archiver")


def _log_error(exc):
    logger.error('Exception in the HyperKitty archiver: %s', exc)
    s = StringIO()
    traceback.print_exc(file=s)
    logger.error('%s', s.getvalue())


@implementer(IArchiver)
class Archiver(object):

    name = "hyperkitty"

    def __init__(self):
        self._conf = {}
        self._load_conf()
        queue_directory = os.path.join(
            config.ARCHIVE_DIR, self.name, 'spool')
        self._switchboard = Switchboard(
            self.name, queue_directory, recover=False)

    @property
    def base_url(self):
        return self._conf["base_url"]

    @property
    def api_key(self):
        return self._conf["api_key"]

    def _load_conf(self):
        """
        Find the location of the HyperKitty-specific config file from Mailman's
        main config file and load the values.
        """
        # Read our specific configuration file
        archiver_config = external_configuration(
            config.archiver.hyperkitty.configuration)
        for option in ("base_url", ):
            url = archiver_config.get("general", option)
            if not url.endswith("/"):
                url += "/"
            self._conf[option] = url
        self._conf["api_key"] = archiver_config.get("general", "api_key")

    def _get_url(self, mlist, params):
        params.update({"key": self.api_key})
        url = urljoin(self.base_url, "api/mailman/urls")
        result = requests.get(url, params=params)
        if result.status_code != 200:
            logger.error("HyperKitty failure on %s: %s (%s)",
                         url, result.text, result.status_code)
            return ""
        try:
            result = result.json()
        except ValueError as e:
            logger.exception(
                "Invalid response from HyperKitty on %s: %s", url, e)
            return ""
        return result["url"]

    def list_url(self, mlist):
        """Return the url to the top of the list's archive.

        :param mlist: The IMailingList object.
        :returns: The url string.
        """
        return self._get_url(mlist, {"mlist": mlist.fqdn_listname})

    def permalink(self, mlist, msg):
        """Return the url to the message in the archive.

        This url points directly to the message in the archive.  This method
        only calculates the url, it does not actually archive the message.

        :param mlist: The IMailingList object.
        :param msg: The message object.
        :returns: The url string or None if the message's archive url cannot
            be calculated.
        """
        msg_id = msg['Message-Id'].strip().strip("<>")
        return self._get_url(
            mlist, {"mlist": mlist.fqdn_listname, "msgid": msg_id})

    def archive_message(self, mlist, msg):
        """
        Send the message to the archiver, but process the queue first if it
        contains any held messages.

        :param mlist: The IMailingList object.
        :param msg: The message object.
        :returns: The url string or None if the message's archive url cannot
            be calculated.
        """
        self.process_queue()
        return self._archive_message(mlist, msg)

    def _archive_message(self, mlist, msg, from_filebase=None):
        """Send the message to the archiver. If an exception occurs, queue the
        message for later retry.

        :param mlist: The IMailingList object.
        :param msg: The message object.
        :param from_filebase: If the message already comes from the retry
            queue, set the queue filebase here and it will be properly removed
            on success, or stored for analysis on error.
        :returns: The url string or None if the message's archive url cannot
            be calculated.
        """
        try:
            url = self._send_message(mlist, msg)
            if from_filebase is not None:
                self._switchboard.finish(from_filebase)
            return url
        except Exception as error:
            # Archiving failed, send the message to the queue.
            _log_error(error)
            # Enqueuing can throw an exception, e.g. a permissions problem
            # or a MemoryError due to a really large message.  Try to be
            # graceful.
            try:
                self._switchboard.enqueue(msg, mlist=mlist)
                if from_filebase is not None:
                    self._switchboard.finish(from_filebase)
            except Exception as error:
                # The message wasn't successfully enqueued.
                _log_error(error)
                logger.error(
                    'queuing failed on mailing-list %s for message %s',
                    mlist.list_id, msg['Message-Id'].strip())
                if from_filebase is not None:
                    # Try to preserve the original queue entry for possible
                    # analysis.
                    self._switchboard.finish(from_filebase, preserve=True)

    def _send_message(self, mlist, msg):
        """Send the message to the archiver over HTTP.

        :param mlist: The IMailingList object.
        :param msg: The message object.
        :returns: The url string or None if the message's archive url cannot
            be calculated.
        """
        logger.debug('%s archiver: sending message %s',
                     self.name, msg['Message-Id'].strip())
        url = urljoin(self.base_url, "api/mailman/archive")
        try:
            message_text = msg.as_string()
        except (MessageError, KeyError) as error:
            logger.error(
                'Could not render the message with id %s to text: %s',
                msg['Message-Id'].strip(), error)
            return  # permanent error, don't raise
        try:
            result = requests.post(
                url, params={"key": self.api_key},
                data={"mlist": mlist.fqdn_listname},
                files={"message": ("message.txt", message_text)})
        except requests.exceptions.RequestException as error:
            logger.error(
                'Connection to HyperKitty failed: %s',
                error)
            raise
        if result.status_code != 200:
            logger.error("HyperKitty failure on %s: %s (%s)",
                         url, result.text, result.status_code)
            raise ValueError(result.text)
        try:
            result = result.json()
        except ValueError as e:
            logger.exception(
                "Invalid response from HyperKitty on %s: %s", url, e)
            raise
        archived_url = result["url"]
        logger.info("HyperKitty archived message %s to %s",
                    msg['Message-Id'].strip(), archived_url)
        return archived_url

    def process_queue(self):
        """Go through the queue of held messages to archive and send them to
        HyperKitty.
        If the archiving is successful, remove them from the queue, otherwise
        re-enqueue them.
        """
        self._switchboard.recover_backup_files
        files = self._switchboard.files
        for filebase in files:
            logger.debug('HyperKitty archiver processing queued filebase: %s',
                         filebase)
            try:
                # Ask the switchboard for the message and metadata objects
                # associated with this queue file.
                msg, msgdata = self._switchboard.dequeue(filebase)
            except Exception as error:
                # We don't want the process to die here or no further email can
                # be archived, so we just log and skip the entry, but preserve
                # it for analysis.
                _log_error(error)
                logger.error('Skipping and preserving unparseable message: %s',
                             filebase)
                self._switchboard.finish(filebase, preserve=True)
                continue
            mlist = msgdata["mlist"]
            self._archive_message(mlist, msg, from_filebase=filebase)
