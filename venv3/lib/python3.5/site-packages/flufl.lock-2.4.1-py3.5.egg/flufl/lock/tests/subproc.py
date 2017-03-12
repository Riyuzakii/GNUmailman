# Copyright (C) 2004-2015 Barry A. Warsaw
#
# This file is part of flufl.lock.
#
# flufl.lock is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, version 3 of the License.
#
# flufl.lock is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License
# for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with flufl.lock.  If not, see <http://www.gnu.org/licenses/>.

"""A helper for setting up subprocess locks."""

from __future__ import absolute_import, print_function, unicode_literals

__metaclass__ = type
__all__ = [
    '_acquire',
    '_waitfor',
    ]


import time
import multiprocessing

from flufl.lock import Lock


def child_locker(filename, lifetime, queue):
    # First, acquire the file lock.
    with Lock(filename, lifetime):
        # Now inform the parent that we've acquired the lock.
        queue.put(True)
        # Keep the file lock for a while.
        time.sleep(lifetime.seconds - 1)


def _acquire(filename, lifetime=None):
    """Acquire the named lock file in a subprocess."""
    queue = multiprocessing.Queue()
    proc = multiprocessing.Process(target=child_locker,
                                   args=(filename, lifetime, queue))
    proc.start()
    while not queue.get():
        time.sleep(0.1)


def child_waitfor(filename, lifetime, queue):
    t0 = time.time()
    # Try to acquire the lock.
    with Lock(filename, lifetime):
        # Tell the parent how long it took to acquire the lock.
        queue.put(time.time() - t0)


def _waitfor(filename, lifetime):
    """Fire off a child that waits for a lock."""
    queue = multiprocessing.Queue()
    proc = multiprocessing.Process(target=child_waitfor,
                                   args=(filename, lifetime, queue))
    proc.start()
    time = queue.get()
    return time
