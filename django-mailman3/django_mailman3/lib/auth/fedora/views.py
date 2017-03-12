# -*- coding: utf-8 -*-
# Copyright (C) 1998-2012 by the Free Software Foundation, Inc.
#
# This file is part of HyperKitty.
#
# HyperKitty is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# HyperKitty is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# HyperKitty.  If not, see <http://www.gnu.org/licenses/>.
#
# Author: Aurelien Bompard <abompard@fedoraproject.org>
#

from __future__ import absolute_import, unicode_literals

from django.shortcuts import render
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

from openid.consumer.discover import DiscoveryFailure
from openid.consumer import consumer
from openid.extensions.sreg import SRegRequest
from openid.extensions.ax import FetchRequest, AttrInfo

from allauth.socialaccount.app_settings import QUERY_EMAIL
from allauth.socialaccount.models import SocialLogin
from allauth.socialaccount.helpers import render_authentication_error
from allauth.socialaccount.helpers import complete_social_login
from allauth.socialaccount import providers

from allauth.socialaccount.providers.openid.views import _openid_consumer
from allauth.socialaccount.providers.openid.utils import (
    SRegFields, AXAttributes)
from allauth.socialaccount.providers.openid.forms import LoginForm
from .provider import FedoraProvider
from allauth.socialaccount.providers.base import AuthError


class LoginView(View):

    form_class = LoginForm
    template_name = 'openid/login.html'
    provider = FedoraProvider
    callback_view = 'fedora_callback'

    def get(self, request, *args, **kwargs):
        if 'openid' in request.GET or self.provider.endpoint:
            return self.post(request, *args, **kwargs)
        form = LoginForm(initial={'next': request.GET.get('next'),
                                  'process': request.GET.get('process')})
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        data = dict(list(request.GET.items()) + list(request.POST.items()))
        if self.provider.endpoint:
            data['openid'] = self.provider.endpoint
        form = LoginForm(data)
        if form.is_valid():
            client = _openid_consumer(request)
            try:
                auth_request = client.begin(form.cleaned_data['openid'])
                if QUERY_EMAIL:
                    sreg = SRegRequest()
                    for name in SRegFields:
                        sreg.requestField(field_name=name,
                                          required=True)
                    auth_request.addExtension(sreg)
                    ax = FetchRequest()
                    for name in AXAttributes:
                        ax.add(AttrInfo(name,
                                        required=True))
                    auth_request.addExtension(ax)
                callback_url = reverse(self.callback_view)
                SocialLogin.stash_state(request)
                redirect_url = auth_request.redirectURL(
                    request.build_absolute_uri('/'),
                    request.build_absolute_uri(callback_url))
                return HttpResponseRedirect(redirect_url)
            # UnicodeDecodeError:
            # see https://github.com/necaris/python3-openid/issues/1
            except (UnicodeDecodeError, DiscoveryFailure) as e:
                if request.method == 'POST':
                    form._errors["openid"] = form.error_class([e])
                else:
                    return render_authentication_error(
                        request, self.provider.id, exception=e)
        return render(request, self.template_name, {'form': form})


class CallbackView(View):

    provider = FedoraProvider

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        client = _openid_consumer(request)
        response = client.complete(
            dict(list(request.GET.items()) + list(request.POST.items())),
            request.build_absolute_uri(request.path))
        if response.status == consumer.SUCCESS:
            login = providers.registry \
                .by_id(self.provider.id) \
                .sociallogin_from_response(request, response)
            login.state = SocialLogin.unstash_state(request)
            ret = complete_social_login(request, login)
        else:
            if response.status == consumer.CANCEL:
                error = AuthError.CANCELLED
            else:
                error = AuthError.UNKNOWN
            ret = render_authentication_error(
                request,
                self.provider.id,
                error=error)
        return ret
