# Copyright (C) 2014-2015 by the Free Software Foundation, Inc.
#
# This file is part of HyperKitty.
#
# HyperKitty is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# GNU Mailman is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# GNU Mailman.  If not, see <http://www.gnu.org/licenses/>.
#
# Author: Aurelien Bompard <abompard@fedoraproject.org>
#

import sys
from setuptools import setup, find_packages


setup(
    name            = 'mailman-hyperkitty',
    version         = '1.0.2',
    description     = 'Mailman archiver plugin for HyperKitty',
    long_description= open("README.rst").read(),
    author='HyperKitty Developers',
    author_email='hyperkitty-devel@lists.fedorahosted.org',
    url="https://gitlab.com/mailman/mailman-hyperkitty/",
    license         = 'GPLv3',
    keywords        = 'email',
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Topic :: Communications :: Email :: Mailing List Servers",
        "Programming Language :: Python :: 3",
        ],
    packages        = find_packages(),
    include_package_data = True,
    install_requires = [
        'setuptools',
        'mailman',
        'requests',
        'zope.interface',
        ],
    test_suite = 'nose2.collector.collector',
    )
