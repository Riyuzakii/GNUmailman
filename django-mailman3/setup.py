# Copyright (C) 2016 by the Free Software Foundation, Inc.
#
# This file is part of Django-Mailman.
#
# Django-Mailman is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by the
# Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# Django-Mailman is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License
# for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Django-Mailman.  If not, see <http://www.gnu.org/licenses/>.

from setuptools import setup, find_packages


setup(
    name="django-mailman3",
    version='1.0.2',
    description="Django library to help interaction with Mailman",
    long_description=open('README.rst').read(),
    maintainer="Mailman Developers",
    maintainer_email="mailman-developers@python.org",
    license='GPLv3',
    keywords='mailman django',
    url="https://gitlab.com/mailman/django-mailman3",
    classifiers=[
        "Framework :: Django",
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Topic :: Communications :: Email :: Mailing List Servers",
        "Programming Language :: Python :: 2",
        ],
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Django >= 1.8',
        'mailmanclient',
        'django-allauth',
        'django-gravatar2 >= 1.0.6',
        'pytz',
    ],
)
