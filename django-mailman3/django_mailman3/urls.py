# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 by the Free Software Foundation, Inc.
#
# This file is part of Django-Mailman.
#
# Django-Mailman is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# Django-Mailman is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# Django-Mailman.  If not, see <http://www.gnu.org/licenses/>.
#
# Author: Aurelien Bompard <abompard@fedoraproject.org>
#


from django.conf.urls import url
from django.contrib import admin

from django_mailman3.views.profile import user_profile


urlpatterns = [
    url(r'^user-profile/', user_profile, name='mm_user_profile'),
    ]


# See the django_mailman3.middleware.sslredirect.SSLRedirect class

SSL_URLS = (
    "django.contrib.auth.views.login",
    "django.contrib.auth.views.logout",
    admin.site.urls,
    )
