# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

import os.path
import mailbox
from email.message import Message
from email import message_from_file
from StringIO import StringIO
from datetime import datetime
from unittest import SkipTest
from traceback import format_exc

from mock import patch, Mock
from django.conf import settings
from django.core.management import call_command
from django.db import DEFAULT_DB_ALIAS
from django.utils.timezone import utc

from hyperkitty.management.commands.hyperkitty_import import Command
from hyperkitty.lib.incoming import add_to_list
from hyperkitty.models import MailingList, Email
from hyperkitty.tests.utils import TestCase, get_test_file


class CommandTestCase(TestCase):

    def setUp(self):
        self.command = Command()
        self.common_cmd_args = dict(
            verbosity=2, list_address="list@example.com",
            since=None, no_sync_mailman=True, ignore_mtime=False,
        )

    def tearDown(self):
        settings.HYPERKITTY_BATCH_MODE = False

    def test_impacted_threads(self):
        # existing message
        msg1 = Message()
        msg1["From"] = "dummy@example.com"
        msg1["Message-ID"] = "<msg1>"
        msg1["Date"] = "2015-01-01 12:00:00"
        msg1.set_payload("msg1")
        add_to_list("list@example.com", msg1)
        # new message in the imported mbox
        msg2 = Message()
        msg2["From"] = "dummy@example.com"
        msg2["Message-ID"] = "<msg2>"
        msg2["Date"] = "2015-02-01 12:00:00"
        msg2.set_payload("msg2")
        mbox = mailbox.mbox(os.path.join(self.tmpdir, "test.mbox"))
        mbox.add(msg2)
        # do the import
        output = StringIO()
        with patch("hyperkitty.management.commands.hyperkitty_import"
                   ".compute_thread_order_and_depth") as mock_compute:
            kw = self.common_cmd_args.copy()
            kw["stdout"] = kw["stderr"] = output
            call_command('hyperkitty_import',
                         os.path.join(self.tmpdir, "test.mbox"), **kw)
        self.assertEqual(mock_compute.call_count, 1)
        thread = mock_compute.call_args[0][0]
        self.assertEqual(thread.emails.count(), 1)
        self.assertEqual(thread.starting_email.message_id, "msg2")

    def test_since_auto(self):
        # When there's mail already and the "since" option is not used, it
        # defaults to the last email's date
        msg1 = Message()
        msg1["From"] = "dummy@example.com"
        msg1["Message-ID"] = "<msg1>"
        msg1["Date"] = "2015-01-01 12:00:00"
        msg1.set_payload("msg1")
        add_to_list("list@example.com", msg1)
        mailbox.mbox(os.path.join(self.tmpdir, "test.mbox"))
        # do the import
        output = StringIO()
        with patch("hyperkitty.management.commands.hyperkitty_import"
                   ".DbImporter") as DbImporterMock:
            instance = Mock()
            instance.impacted_thread_ids = []
            DbImporterMock.side_effect = lambda *a, **kw: instance
            kw = self.common_cmd_args.copy()
            kw["stdout"] = kw["stderr"] = output
            call_command('hyperkitty_import',
                         os.path.join(self.tmpdir, "test.mbox"), **kw)
        self.assertEqual(DbImporterMock.call_args[0][1]["since"],
                         datetime(2015, 1, 1, 12, 0, tzinfo=utc))

    def test_since_override(self):
        # The "since" option is used
        msg1 = Message()
        msg1["From"] = "dummy@example.com"
        msg1["Message-ID"] = "<msg1>"
        msg1["Date"] = "2015-01-01 12:00:00"
        msg1.set_payload("msg1")
        add_to_list("list@example.com", msg1)
        mailbox.mbox(os.path.join(self.tmpdir, "test.mbox"))
        # do the import
        output = StringIO()
        with patch("hyperkitty.management.commands.hyperkitty_import"
                   ".DbImporter") as DbImporterMock:
            instance = Mock()
            instance.impacted_thread_ids = []
            DbImporterMock.side_effect = lambda *a, **kw: instance
            kw = self.common_cmd_args.copy()
            kw["stdout"] = kw["stderr"] = output
            kw["since"] = "2010-01-01 00:00:00 UTC"
            call_command('hyperkitty_import',
                         os.path.join(self.tmpdir, "test.mbox"), **kw)
        self.assertEqual(DbImporterMock.call_args[0][1]["since"],
                         datetime(2010, 1, 1, tzinfo=utc))

    def test_lowercase_list_name(self):
        msg = Message()
        msg["From"] = "dummy@example.com"
        msg["Message-ID"] = "<msg1>"
        msg["Date"] = "2015-02-01 12:00:00"
        msg.set_payload("msg1")
        mbox = mailbox.mbox(os.path.join(self.tmpdir, "test.mbox"))
        mbox.add(msg)
        # do the import
        output = StringIO()
        kw = self.common_cmd_args.copy()
        kw["stdout"] = kw["stderr"] = output
        kw["list_address"] = "LIST@example.com"
        call_command('hyperkitty_import',
                     os.path.join(self.tmpdir, "test.mbox"), **kw)
        self.assertEqual(MailingList.objects.count(), 1)
        ml = MailingList.objects.first()
        self.assertEqual(ml.name, "list@example.com")

    def test_wrong_encoding(self):
        """badly encoded message, only fails on PostgreSQL"""
        db_engine = settings.DATABASES[DEFAULT_DB_ALIAS]["ENGINE"]
        if db_engine == "django.db.backends.sqlite3":
            raise SkipTest  # SQLite will accept anything
        with open(get_test_file("payload-utf8-wrong.txt")) as email_file:
            msg = message_from_file(email_file)
        mbox = mailbox.mbox(os.path.join(self.tmpdir, "test.mbox"))
        mbox.add(msg)
        # Second message
        msg = Message()
        msg["From"] = "dummy@example.com"
        msg["Message-ID"] = "<msg1>"
        msg["Date"] = "2015-02-01 12:00:00"
        msg.set_payload("msg1")
        mbox.add(msg)
        # do the import
        output = StringIO()
        kw = self.common_cmd_args.copy()
        kw["stdout"] = kw["stderr"] = output
        call_command('hyperkitty_import',
                     os.path.join(self.tmpdir, "test.mbox"), **kw)
        # Message 1 must have been rejected, but no crash
        self.assertIn("Message wrong.encoding failed to import, skipping",
                      output.getvalue())
        # Message 2 must have been accepted
        self.assertEqual(MailingList.objects.count(), 1)
        self.assertEqual(Email.objects.count(), 1)

    def test_weird_timezone(self):
        # An email has a timezone with a strange offset (seen in the wild).
        # Make sure it does not break our _is_old_enough() method.
        mbox = mailbox.mbox(os.path.join(self.tmpdir, "test.mbox"))
        # First message is already imported
        msg1 = Message()
        msg1["From"] = "dummy@example.com"
        msg1["Message-ID"] = "<msg1>"
        msg1["Date"] = "2008-01-01 12:00:00"
        msg1.set_payload("msg1")
        add_to_list("list@example.com", msg1)
        # Second message is in the mbox to import
        msg2 = Message()
        msg2["From"] = "dummy@example.com"
        msg2["Message-ID"] = "<msg2>"
        msg2["Date"] = "Sat, 30 Aug 2008 16:40:31 +05-30"
        msg2.set_payload("msg2")
        mbox.add(msg2)
        # do the import
        output = StringIO()
        kw = self.common_cmd_args.copy()
        kw["stdout"] = kw["stderr"] = output
        try:
            call_command('hyperkitty_import',
                         os.path.join(self.tmpdir, "test.mbox"), **kw)
        except ValueError as e:
            self.fail(format_exc(e))
        # Message must have been accepted
        self.assertEqual(MailingList.objects.count(), 1)
        self.assertEqual(Email.objects.count(), 2)

    def test_unixfrom(self):
        # Make sure the UNIX From line is forwarded to the incoming function.
        msg = mailbox.mboxMessage()
        msg["From"] = "dummy@example.com"
        msg["Message-ID"] = "<msg1>"
        msg["Date"] = "2008-01-01 12:00:00"
        msg.set_payload("msg1")
        msg.set_from("dummy@example.com Mon Jul 21 11:44:51 2008")
        mbox = mailbox.mbox(os.path.join(self.tmpdir, "test.mbox"))
        mbox.add(msg)
        # do the import
        output = StringIO()
        kw = self.common_cmd_args.copy()
        kw["stdout"] = kw["stderr"] = output
        call_command('hyperkitty_import',
                     os.path.join(self.tmpdir, "test.mbox"), **kw)
        # Message must have been accepted
        self.assertEqual(MailingList.objects.count(), 1)
        self.assertEqual(Email.objects.count(), 1)
        email = Email.objects.first()
        self.assertEqual(
            email.archived_date,
            datetime(2008, 7, 21, 11, 44, 51, tzinfo=utc))

    def test_impacted_threads_batch(self):
        # Fix GL issue #86
        mbox = mailbox.mbox(os.path.join(self.tmpdir, "test.mbox"))
        for i in range(250):
            msg = Message()
            msg["From"] = "dummy@example.com"
            msg["Message-ID"] = "<msg%d>" % i
            msg["Date"] = "2015-01-01 12:00:00"
            msg.set_payload("msg%d" % i)
            mbox.add(msg)
        # do the import
        output = StringIO()
        with patch("hyperkitty.management.commands.hyperkitty_import"
                   ".compute_thread_order_and_depth") as mock_compute:
            kw = self.common_cmd_args.copy()
            kw["stdout"] = kw["stderr"] = output
            call_command('hyperkitty_import',
                         os.path.join(self.tmpdir, "test.mbox"), **kw)
        called_thread_ids = set([
            call[0][0].starting_email.message_id
            for call in mock_compute.call_args_list
            ])
        self.assertEqual(
            called_thread_ids,
            set([("msg%d" % i) for i in range(250)]))
