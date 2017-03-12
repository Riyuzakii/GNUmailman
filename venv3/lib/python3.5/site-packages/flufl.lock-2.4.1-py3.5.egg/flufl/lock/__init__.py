# Copyright (C) 2004-2015 Barry A. Warsaw
#
# This file is part of flufl.lock
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

"""Package init."""

from __future__ import absolute_import, print_function, unicode_literals

__metaclass__ = type
__all__ = [
    'AlreadyLockedError',
    'Lock',
    'LockError',
    'NotLockedError',
    'TimeOutError',
    '__version__',
    ]


__version__ = '2.4.1'


# Public API.
from flufl.lock._lockfile import (
    AlreadyLockedError, Lock, LockError, NotLockedError, TimeOutError)
