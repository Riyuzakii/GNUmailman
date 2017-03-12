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
Update the full-text index
"""

from __future__ import absolute_import, print_function, unicode_literals

import errno
import os.path
from tempfile import gettempdir

from django.conf import settings
from django_extensions.management.jobs import BaseJob
from lockfile import AlreadyLocked, LockFailed
from lockfile.pidlockfile import PIDLockFile
from hyperkitty.search_indexes import update_index

import logging
logger = logging.getLogger(__name__)


class Job(BaseJob):
    help = "Update the full-text index"
    when = "minutely"

    def execute(self):
        run_with_lock(remove=False)


def run_with_lock(remove=False):
    lock = PIDLockFile(getattr(
        settings, "HYPERKITTY_JOBS_UPDATE_INDEX_LOCKFILE",
        os.path.join(gettempdir(), "hyperkitty-jobs-update-index.lock")))
    try:
        lock.acquire(timeout=-1)
    except AlreadyLocked:
        if check_pid(lock.read_pid()):
            logger.warning("The job 'update_index' is already running")
            return
        else:
            lock.break_lock()
            lock.acquire(timeout=-1)
    except LockFailed as e:
        logger.warning("Could not obtain a lock for the 'update_index' "
                       "job (%s)", e)
        return
    try:
        update_index(remove=remove)
    except Exception as e:
        logger.exception("Failed to update the fulltext index: %s", e)
    finally:
        lock.release()


def check_pid(pid):
    """ Check For the existence of a unix pid. """
    if pid is None:
        return False
    try:
        os.kill(pid, 0)
    except OSError as e:
        if e.errno == errno.ESRCH:
            # if errno !=3, we may just not be allowed to send the signal
            return False
    return True
