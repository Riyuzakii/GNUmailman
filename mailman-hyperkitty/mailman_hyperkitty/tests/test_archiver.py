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

# pylint: disable=protected-access,too-few-public-methods,no-self-use

import glob
import json
import os
import tempfile
import shutil
from textwrap import dedent
from unittest import TestCase

import requests
from mock import Mock, patch
from mailman.config import config
from mailman.email.message import Message
from mailman.testing.layers import ConfigLayer
from mailman.utilities.email import add_message_hash

from mailman_hyperkitty import Archiver


class FakeResponse:
    """Fake a response from the "requests" library"""

    def __init__(self, status_code, result):
        self.status_code = status_code
        self.result = result

    def json(self):
        return self.result

    @property
    def text(self):
        return json.dumps(self.result)


class FakeDomain:
    """Fake a Mailman domain implementing the IDomain interface"""

    def __init__(self, domain):
        self.mail_host = domain


class FakeList:
    """Fake a Mailman list implementing the IMailingList interface"""

    def __init__(self, name):
        self.fqdn_listname = name
        self.domain = FakeDomain("lists.example.com")
        self.list_id = name.replace("@", ".")


class ArchiverTestCase(TestCase):

    layer = ConfigLayer

    def setUp(self):
        # Set up a temporary directory for the archiver so that it's
        # easier to clean up.
        self._tempdir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self._tempdir)
        config.push('hyperkitty', """
        [paths.testing]
        archive_dir: {tmpdir}/archive
        [archiver.hyperkitty]
        class: mailman_hyperkitty.Archiver
        enable: yes
        configuration: {tmpdir}/mailman-hyperkitty.cfg
        """.format(tmpdir=self._tempdir))
        self.addCleanup(config.pop, 'hyperkitty')
        with open(os.path.join(
                self._tempdir, "mailman-hyperkitty.cfg"), "w") as conf_h:
            conf_h.write(dedent("""
            [general]
            base_url: http://localhost
            api_key: DummyKey
            """))
        # Create the archiver
        self.archiver = Archiver()
        self.mlist = FakeList("list@lists.example.com")
        # Patch requests
        self.requests_patcher = patch("mailman_hyperkitty.requests")
        self.requests = self.requests_patcher.start()
        self.fake_response = None
        self.requests.get.side_effect = \
            lambda url, *a, **kw: self.fake_response
        self.requests.post.side_effect = \
            lambda url, *a, **kw: self.fake_response

    def tearDown(self):
        self.requests_patcher.stop()

    def _get_msg(self):
        msg = Message()
        msg["From"] = "dummy@example.com"
        msg["Message-ID"] = "<dummy>"
        msg["Message-ID-Hash"] = "QKODQBCADMDSP5YPOPKECXQWEQAMXZL3"
        msg.set_payload("Dummy message")
        return msg

    def test_list_url(self):
        self.fake_response = FakeResponse(
            200, {"url": "http://example.com/list/list@lists.example.com/"})
        self.assertEqual(
            self.archiver.list_url(self.mlist),
            "http://example.com/list/list@lists.example.com/"
            )
        self.requests.get.assert_called_with(
            "http://localhost/api/mailman/urls",
            params={'key': 'DummyKey', 'mlist': 'list@lists.example.com'}
            )

    def test_permalink(self):
        msg = self._get_msg()
        url = ("http://example.com/list/list@lists.example.com/"
               "message/{}/".format(msg["Message-ID-Hash"]))
        self.fake_response = FakeResponse(200, {"url": url})
        self.assertEqual(self.archiver.permalink(self.mlist, msg), url)
        self.requests.get.assert_called_with(
            "http://localhost/api/mailman/urls",
            params={'key': 'DummyKey', 'msgid': 'dummy',
                    'mlist': 'list@lists.example.com'}
        )

    def test_archive_message(self):
        msg = self._get_msg()
        url = ("http://example.com/list/list@lists.example.com/"
               "message/{}/".format(msg["Message-ID-Hash"]))
        self.fake_response = FakeResponse(200, {"url": url})
        with patch("mailman_hyperkitty.logger") as logger:
            archive_url = self.archiver.archive_message(self.mlist, msg)
        self.assertTrue(logger.info.called)
        self.assertEqual(archive_url, url)
        self.requests.post.assert_called_with(
            "http://localhost/api/mailman/archive",
            params={'key': 'DummyKey'},
            data={'mlist': 'list@lists.example.com'},
            files={'message': ('message.txt', msg.as_string())},
        )
        # Check that the archive directory was created.
        self.assertTrue(os.path.exists(
            self.archiver._switchboard.queue_directory))
        # Make sure it is empty, since the message has been successfuly
        # archived.
        self.assertEqual(len(os.listdir(
            self.archiver._switchboard.queue_directory)), 0)
        self.assertEqual(len(self.archiver._switchboard.files), 0)

    def test_list_url_permalink_error(self):
        # Don't raise exceptions for list_url and permalink
        self.fake_response = FakeResponse(500, "Fake error")
        with patch("mailman_hyperkitty.logger") as logger:
            self.assertEqual(self.archiver.list_url(self.mlist), "")
            self.assertEqual(
                self.archiver.permalink(self.mlist, self._get_msg()), "")
        # Check error log
        self.assertEqual(logger.error.call_count, 2)
        for call in logger.error.call_args_list:
            self.assertEqual(call[0][3], 500)

    def test_list_url_permalink_invalid(self):
        self.fake_response = Mock()
        self.fake_response.status_code = 200
        self.fake_response.json.side_effect = ValueError
        with patch("mailman_hyperkitty.logger") as logger:
            self.assertEqual(self.archiver.list_url(self.mlist), "")
            self.assertEqual(
                self.archiver.permalink(self.mlist, self._get_msg()), "")
        # Check error log
        self.assertEqual(logger.exception.call_count, 2)
        for call in logger.error.call_args_list:
            self.assertTrue(isinstance(call[0][2], ValueError))

    def test_archive_message_error(self):
        self.fake_response = FakeResponse(500, "Fake error")
        with patch("mailman_hyperkitty.logger") as logger:
            self.archiver.archive_message(self.mlist, self._get_msg())
        # Check error log
        self.assertEqual(logger.error.call_count, 3)
        self.assertTrue(isinstance(
            logger.error.call_args_list[1][0][1], ValueError))
        # Check that the message is stored in the spool.
        self.assertEqual(len(os.listdir(
            self.archiver._switchboard.queue_directory)), 1)
        self.assertEqual(len(self.archiver._switchboard.files), 1)

    def test_archive_message_unavailable(self):
        self.requests.exceptions.RequestException = \
            requests.exceptions.RequestException
        self.requests.post.side_effect = requests.exceptions.RequestException
        with patch("mailman_hyperkitty.logger") as logger:
            self.archiver.archive_message(self.mlist, self._get_msg())
        # Check error log
        self.assertTrue(logger.error.called)
        self.assertTrue(isinstance(
            logger.error.call_args_list[0][0][1],
            requests.exceptions.RequestException))
        # Check that the message is stored in the spool.
        self.assertEqual(len(os.listdir(
            self.archiver._switchboard.queue_directory)), 1)
        self.assertEqual(len(self.archiver._switchboard.files), 1)

    def test_archive_message_invalid(self):
        self.fake_response = Mock()
        self.fake_response.status_code = 200
        self.fake_response.json.side_effect = ValueError
        with patch("mailman_hyperkitty.logger") as logger:
            self.archiver.archive_message(self.mlist, self._get_msg())
        # Check error log
        self.assertEqual(logger.exception.call_count, 1)
        self.assertTrue(isinstance(
            logger.exception.call_args_list[0][0][2], ValueError))
        # Check that the message is stored in the spool.
        self.assertEqual(len(os.listdir(
            self.archiver._switchboard.queue_directory)), 1)
        self.assertEqual(len(self.archiver._switchboard.files), 1)

    def test_archive_message_replay(self):
        # If there are messages in the spool directory, they must be processed
        # before any other message.

        # Create a previously failed message in the spool queue.
        msg_1 = self._get_msg()
        msg_1["Message-ID"] = "<dummy-1>"
        del msg_1["Message-ID-Hash"]
        add_message_hash(msg_1)
        self.archiver._switchboard.enqueue(msg_1, mlist=self.mlist)
        # Now send another message
        msg_2 = self._get_msg()
        msg_2["Message-ID"] = "<dummy-2>"
        del msg_2["Message-ID-Hash"]
        add_message_hash(msg_2)

        self.fake_response = FakeResponse(200, {"url": "dummy"})
        with patch("mailman_hyperkitty.logger") as logger:
            self.archiver.archive_message(self.mlist, msg_2)
        # Two messages must have been archived
        self.assertEqual(logger.info.call_count, 2)

        self.assertEqual(self.requests.post.call_args_list, [
                (("http://localhost/api/mailman/archive",), dict(
                    params={'key': 'DummyKey'},
                    data={'mlist': 'list@lists.example.com'},
                    files={'message': ('message.txt', msg_1.as_string())},
                )),
                (("http://localhost/api/mailman/archive",), dict(
                    params={'key': 'DummyKey'},
                    data={'mlist': 'list@lists.example.com'},
                    files={'message': ('message.txt', msg_2.as_string())},
                )),
            ])
        # Make sure the spool directory is empty now.
        self.assertEqual(len(os.listdir(
            self.archiver._switchboard.queue_directory)), 0)
        self.assertEqual(len(self.archiver._switchboard.files), 0)

    def test_queued_archive_message_error(self):
        # If a queue message is being retried and the archiving fails again, it
        # stays in the queue.
        self.fake_response = FakeResponse(500, "Fake error")
        self.archiver._switchboard.enqueue(self._get_msg(), mlist=self.mlist)
        with patch("mailman_hyperkitty.logger") as logger:
            self.archiver.process_queue()
        # Check error log
        self.assertEqual(logger.error.call_count, 3)
        self.assertEqual(logger.error.call_args_list[0][0][3], 500)
        self.assertTrue(isinstance(
            logger.error.call_args_list[1][0][1], ValueError))
        # Check that the message is still stored in the spool.
        self.assertEqual(len(os.listdir(
            self.archiver._switchboard.queue_directory)), 1)
        self.assertEqual(len(self.archiver._switchboard.files), 1)

    def test_queued_message_unparseable(self):
        self.fake_response = FakeResponse(200, {"url": "dummy"})
        with open(os.path.join(
                self.archiver._switchboard.queue_directory,
                "123456789+dummy.pck"), "w") as fh:
            fh.write("invalid pickle data")
        self.assertEqual(len(self.archiver._switchboard.files), 1)
        # Now process the queue.
        with patch("mailman_hyperkitty.logger") as logger:
            self.archiver.process_queue()
        # Check error log
        self.assertEqual(logger.error.call_count, 3)
        # Check that the message has been preserved for analysis
        self.assertEqual(len(glob.glob(os.path.join(
            config.switchboards["bad"].queue_directory, "*.psv")
            )), 1)

    def test_queued_message_enqueue_exception(self):
        self.fake_response = FakeResponse(500, "Fake error")
        self.archiver._switchboard.enqueue(self._get_msg(), mlist=self.mlist)
        # Now, cause .enqueue() to throw an exception and process the queue.
        self.archiver._switchboard.enqueue = Mock()
        self.archiver._switchboard.enqueue.side_effect = OSError('Oops!')
        with patch("mailman_hyperkitty.logger") as logger:
            self.archiver.process_queue()
        self.assertEqual(logger.error.call_count, 6)
        # Check error log
        self.assertEqual(logger.error.call_args_list[0][0][3], 500)
        self.assertTrue(isinstance(
            logger.error.call_args_list[1][0][1], ValueError))
        self.assertTrue(isinstance(
            logger.error.call_args_list[3][0][1], OSError))
        # Check that the message has been preserved for analysis
        self.assertEqual(len(glob.glob(os.path.join(
            config.switchboards["bad"].queue_directory, "*.psv")
            )), 1)

    def test_queued_message_finish_exception(self):
        self.fake_response = FakeResponse(200, {"url": "dummy"})
        self.archiver._switchboard.enqueue(self._get_msg(), mlist=self.mlist)
        # Now, cause .finish() to throw an exception and process the queue.
        with patch('mailman.core.switchboard.os.rename',
                   side_effect=OSError('Oops!')), \
                patch("mailman_hyperkitty.logger") as logger:
            self.archiver.process_queue()
        # Check error log
        self.assertEqual(logger.error.call_count, 3)
        self.assertTrue(isinstance(
            logger.error.call_args_list[0][0][1], OSError))
        # Check that the message is still stored in the spool.
        self.assertEqual(len(os.listdir(
            self.archiver._switchboard.queue_directory)), 1)
        self.assertEqual(len(self.archiver._switchboard.files), 1)

    def test_archive_message_unserializable(self):
        msg = self._get_msg()
        msg["content-type"] = 'text/plain; charset="UTF-8"'
        msg.set_payload(b"this contains encoded unicode \xc3\xa9 \xc3\xa0")
        # If you try to serialize this message to text, it will cause a:
        # KeyError: 'content-transfer-encoding'
        with patch("mailman_hyperkitty.logger") as logger:
            self.archiver.archive_message(self.mlist, msg)
        # Check error log
        self.assertEqual(logger.error.call_count, 1)
        self.assertTrue(isinstance(
            logger.error.call_args_list[0][0][2], KeyError))
        # Check that the message is not stored in the spool.
        self.assertEqual(len(os.listdir(
            self.archiver._switchboard.queue_directory)), 0)
        self.assertEqual(len(self.archiver._switchboard.files), 0)
