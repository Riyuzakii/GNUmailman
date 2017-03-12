# -*- coding: utf-8 -*-
# Copyright (C) 1998-2015 by the Free Software Foundation, Inc.
#
# This file is part of Postorius.
#
# Postorius is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# Postorius is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# Postorius.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import, unicode_literals

from django.conf.urls import url, include

from postorius.views import list as list_views
from postorius.views import user as user_views
from postorius.views import domain as domain_views
from postorius.views import rest as rest_views


list_patterns = [
    url(r'^csv_view/$', list_views.csv_view, name='csv_view'),
    url(r'^members/options/(?P<email>.+)$', list_views.list_member_options,
        name='list_member_options'),
    url(r'^members/(?P<role>\w+)/$', list_views.list_members_view,
        name='list_members'),
    url(r'^$', list_views.ListSummaryView.as_view(),
        name='list_summary'),
    url(r'^subscribe$', list_views.ListSubscribeView.as_view(),
        name='list_subscribe'),
    url(r'^anonymous_subscribe$',
        list_views.ListAnonymousSubscribeView.as_view(),
        name='list_anonymous_subscribe'),
    url(r'^change_subscription$', list_views.ChangeSubscriptionView.as_view(),
        name='change_subscription'),
    url(r'^unsubscribe/$', list_views.ListUnsubscribeView.as_view(),
        name='list_unsubscribe'),
    url(r'^subscription_requests$', list_views.list_subscription_requests,
        name='list_subscription_requests'),
    url(r'^handle_subscription_request/(?P<request_id>[^/]+)/'
        '(?P<action>[accept|reject|discard|defer]+)$',
        list_views.handle_subscription_request,
        name='handle_subscription_request'),
    url(r'^mass_subscribe/$', list_views.list_mass_subscribe,
        name='mass_subscribe'),
    url(r'^mass_removal/$', list_views.ListMassRemovalView.as_view(),
        name='mass_removal'),
    url(r'^delete$', list_views.list_delete, name='list_delete'),
    url(r'^held_messages$', list_views.list_moderation,
        name='list_held_messages'),
    url(r'^held_messages/moderate$', list_views.moderate_held_message,
        name='moderate_held_message'),
    url(r'^bans/$', list_views.list_bans, name='list_bans'),
    url(r'^header-matches/$', list_views.list_header_matches,
        name='list_header_matches'),
    url(r'^remove/(?P<role>[^/]+)/(?P<address>.+)$', list_views.remove_role,
        name='remove_role'),
    url(r'^settings/(?P<visible_section>[^/]+)?$', list_views.list_settings,
        name='list_settings'),
    url(r'^unsubscribe_all$', list_views.remove_all_subscribers,
        name='unsubscribe_all'),
]

urlpatterns = [
    url(r'^$', list_views.list_index),
    url(r'^accounts/subscriptions/$', user_views.user_subscriptions,
        name='ps_user_profile'),
    url(r'^accounts/per-address-preferences/$',
        user_views.UserAddressPreferencesView.as_view(),
        name='user_address_preferences'),
    # if this URL changes, update Mailman's Member.options_url
    url(r'^accounts/per-subscription-preferences/$',
        user_views.UserSubscriptionPreferencesView.as_view(),
        name='user_subscription_preferences'),
    url(r'^accounts/mailmansettings/$',
        user_views.UserMailmanSettingsView.as_view(),
        name='user_mailmansettings'),
    url(r'^accounts/list-options/(?P<list_id>[^/]+)/$',
        user_views.UserListOptionsView.as_view(),
        name='user_list_options'),
    # /domains/
    url(r'^domains/$', domain_views.domain_index, name='domain_index'),
    url(r'^domains/new/$', domain_views.domain_new, name='domain_new'),
    url(r'^domains/(?P<domain>[^/]+)/$', domain_views.domain_edit,
        name='domain_edit'),
    url(r'^domains/(?P<domain>[^/]+)/delete$', domain_views.domain_delete,
        name='domain_delete'),
    # /lists/
    url(r'^lists/$', list_views.list_index, name='list_index'),
    url(r'^lists/new/$', list_views.list_new, name='list_new'),
    url(r'^lists/(?P<list_id>[^/]+)/', include(list_patterns)),
    url(r'^api/list/(?P<list_id>[^/]+)/held_message/(?P<held_id>\d+)/$',
        rest_views.get_held_message, name='rest_held_message'),
    url(r'^api/list/(?P<list_id>[^/]+)/held_message/(?P<held_id>\d+)/'
        'attachment/(?P<attachment_id>\d+)/$',
        rest_views.get_attachment_for_held_message,
        name='rest_attachment_for_held_message'),
]
