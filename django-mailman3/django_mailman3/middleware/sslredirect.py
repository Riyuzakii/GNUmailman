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

from importlib import import_module
from django.conf import settings
from django.http import HttpResponsePermanentRedirect
from django.core.urlresolvers import RegexURLPattern, RegexURLResolver


class SSLRedirect(object):
    """
    Redirect protected URLs to SSL. Keeps SSL on when you are authenticated.

    You can declare the protected URLs by listing them in your URLconf module
    in the SSL_URLS list. This list can contain other URLconf modules, view
    names, or view functions.

    If those other included URLconf modules also contain an SSL_URLS variable,
    only the listed URLs will be protected. Otherwise, all URLs in this URLconf
    module will be protected.
    """

    _protected_urls = None

    def _walk_module(self, module):
        """Recurse into URLconf modules to populate self._protected_urls"""
        def add_patterns(patterns):
            for pattern in patterns:
                if isinstance(pattern, RegexURLPattern):
                    self._protected_urls.append(pattern.callback)
                elif isinstance(pattern, RegexURLResolver):
                    add_patterns(pattern.url_patterns)
        if not hasattr(module, "SSL_URLS"):
            # Nothing specified, add all URLs
            add_patterns(module.urlpatterns)
            return
        for module_or_view in module.SSL_URLS:
            if callable(module_or_view):
                self._protected_urls.append(module_or_view)
                continue
            if isinstance(module_or_view, tuple):
                # see the django.conf.urls.include method
                urlconf_module, app_name_, namespace_ = module_or_view
                add_patterns(urlconf_module)
                continue
            try:
                submodule = import_module(module_or_view)
            except ImportError:
                # Its a function name, resolve it and add it
                submodule, dot_, func_name = module_or_view.rpartition(".")
                submodule = import_module(submodule)
                self._protected_urls.append(getattr(submodule, func_name))
            else:
                # Its a URLconf module, recurse into it
                self._walk_module(submodule)

    @property
    def protected_urls(self):
        if self._protected_urls is None:
            self._protected_urls = []
            self._walk_module(import_module(settings.ROOT_URLCONF))
        return self._protected_urls

    def process_view(self, request, view_func, view_args, view_kwargs):
        if not settings.USE_SSL:  # User-disabled (e.g: development server)
            return
        if self._is_secure(request):
            return  # Already in HTTPS, never redirect back to HTTP
        want_secure = view_func in self.protected_urls
        if request.user.is_authenticated():
            want_secure = True
        if want_secure:
            return self._redirect(request, want_secure)

    def _is_secure(self, request):
        if request.is_secure():
            return True
        # Handle the Webfaction case until this gets resolved in the
        # request.is_secure()
        if 'HTTP_X_FORWARDED_SSL' in request.META:
            return request.META['HTTP_X_FORWARDED_SSL'] == 'on'
        return False

    def _redirect(self, request, secure):
        # Note: this method is also capable of redirecting to HTTP, but we
        # don't use this feature.
        protocol = secure and "https" or "http"
        newurl = "%s://%s%s" % (
            protocol, request.get_host(), request.get_full_path())
        if settings.DEBUG and request.method == 'POST':
            raise RuntimeError(
                "Django can't perform a SSL redirect while maintaining "
                "POST data. Please structure your views so that redirects "
                "only occur during GETs.")
        return HttpResponsePermanentRedirect(newurl)
