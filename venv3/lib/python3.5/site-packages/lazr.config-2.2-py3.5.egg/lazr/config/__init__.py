# Copyright 2007-2015 Canonical Ltd.  All rights reserved.
#
# This file is part of lazr.config
#
# lazr.config is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# lazr.config is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public
# License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with lazr.config.  If not, see <http://www.gnu.org/licenses/>.

"""A configuration file system."""

import pkg_resources
__version__ = pkg_resources.resource_string(
    "lazr.config", "version.txt").strip()

# While we generally frown on "*" imports, this, combined with the fact we
# only test code from this module, means that we can verify what has been
# exported.
from lazr.config._config import *
from lazr.config._config import __all__
