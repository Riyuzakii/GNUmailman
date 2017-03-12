# -*- coding: utf-8 -*-
#
# Copyright (C) 2014-2015 by the Free Software Foundation, Inc.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301,
# USA.
#
# Author: Aurelien Bompard <abompard@fedoraproject.org>

"""
Utilities for management commands.
"""

import logging
import sys


class DualStreamsHandler(logging.StreamHandler):
    """
    Emits messages below and including INFO to the first stream, and messages
    above and including WARNING to the second stream. Useful when the first
    stream is stdout and the second stream is stderr.
    """

    def __init__(self, stream_low=None, stream_high=None):
        super(DualStreamsHandler, self).__init__()
        if stream_low is None:
            stream_low = sys.stdout
        self.stream_low = stream_low
        if stream_high is None:
            stream_high = sys.stderr
        self.stream_high = stream_high

    def emit(self, record):
        """Wraps the original emit method to dynamically switch the stream."""
        self.stream = self.stream_low
        if record.levelno > logging.INFO:
            self.stream = self.stream_high
        super(DualStreamsHandler, self).emit(record)


def setup_logging(command, verbosity):
    """
    Sets up logging to send messages up to INFO level to stdout and messages
    from WARNING level and up to stderr. This is done regardless of the logging
    settings in Django (which may be sending everything to a log file).
    Existing logging settings are not changed.
    """
    if verbosity >= 3:
        debuglevel = logging.DEBUG
    else:
        debuglevel = logging.INFO
    handler = DualStreamsHandler(
        stream_low=command.stdout, stream_high=command.stderr)
    formatter = logging.Formatter(fmt='%(message)s')
    handler.setFormatter(formatter)
    root_logger = logging.getLogger()
    root_logger.setLevel(debuglevel)
    root_logger.addHandler(handler)
