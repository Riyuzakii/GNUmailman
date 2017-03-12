# -*- coding: utf-8 -*-
#
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
# Author: Aamir Khan <syst3m.w0rm@gmail.com>
# Author: Aurelien Bompard <abompard@fedoraproject.org>
#

from django.conf.urls import include, url
from django.views.generic.base import TemplateView

from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from hyperkitty.api import (
    mailinglist as api_mailinglist, email as api_email,
    thread as api_thread, tag as api_tag)
from hyperkitty.views import (
    index, accounts, users, mlist, message, thread, search, categories, tags,
    mailman, compat)


# flake8: noqa


# List archives and overview
list_patterns = [
    url(r'^(?P<year>\d{4})/(?P<month>\d\d?)/(?P<day>\d\d?)/$',
        mlist.archives, name='hk_archives_with_day'),
    url(r'^(?P<year>\d{4})/(?P<month>\d\d?)/$',
        mlist.archives, name='hk_archives_with_month'),
    url(r'^latest$', mlist.archives, name='hk_archives_latest'),
    url(r'^$', mlist.overview, name='hk_list_overview'),
    url(r'^recent-activity$',
        mlist.recent_activity, name='hk_list_recent_activity'),
    url(r'^export/(?P<filename>[^/]+)\.mbox.gz$',
        mlist.export_mbox, name='hk_list_export_mbox'),
]


# Messages
message_patterns = [
    url(r'^$', message.index, name='hk_message_index'),
    url(r'^attachment/(?P<counter>\d+)/(?P<filename>.+)$',
        message.attachment, name='hk_message_attachment'),
    url(r'^vote$', message.vote, name='hk_message_vote'),
    url(r'^reply$', message.reply, name='hk_message_reply'),
    url(r'^delete$', message.delete, name='hk_message_delete'),
]


# Threads
thread_patterns = [
    url(r'^$', thread.thread_index, name='hk_thread'),
    url(r'^replies$', thread.replies, name='hk_thread_replies'),
    url(r'^tags$', thread.tags, name='hk_tags'),
    url(r'^suggest-tags$', thread.suggest_tags, name='hk_suggest_tags'),
    url(r'^favorite$', thread.favorite, name='hk_favorite'),
    url(r'^category$', thread.set_category, name='hk_thread_set_category'),
    url(r'^reattach$', thread.reattach, name='hk_thread_reattach'),
    url(r'^reattach-suggest$',
        thread.reattach_suggest, name='hk_thread_reattach_suggest'),
    url(r'^delete$', message.delete, name='hk_thread_delete'),
]


# REST API
api_patterns = [
    url(r'^$', TemplateView.as_view(template_name="hyperkitty/api.html")),
    url(r'^lists/$',
        api_mailinglist.MailingListList.as_view(), name="hk_api_mailinglist_list"),
    url(r'^list/(?P<name>[^/@]+@[^/@]+)/$',
        api_mailinglist.MailingListDetail.as_view(), name="hk_api_mailinglist_detail"),
    url(r'^list/(?P<mlist_fqdn>[^/@]+@[^/@]+)\/threads/$',
        api_thread.ThreadList.as_view(), name="hk_api_thread_list"),
    url(r'^list/(?P<mlist_fqdn>[^/@]+@[^/@]+)\/thread/(?P<thread_id>[^/]+)/$',
        api_thread.ThreadDetail.as_view(), name="hk_api_thread_detail"),
    url(r'^list/(?P<mlist_fqdn>[^/@]+@[^/@]+)/emails/$',
        api_email.EmailList.as_view(), name="hk_api_email_list"),
    url(r'^list/(?P<mlist_fqdn>[^/@]+@[^/@]+)\/email/(?P<message_id_hash>.*)/$',
        api_email.EmailDetail.as_view(), name="hk_api_email_detail"),
    url(r'^list/(?P<mlist_fqdn>[^/@]+@[^/@]+)/thread/(?P<thread_id>[^/]+)/emails/$',
        api_email.EmailList.as_view(), name="hk_api_thread_email_list"),
    #url(r'^sender/(?P<address>[^/@]+@[^/@]+)/$',
    #    api_sender.SenderDetail.as_view(), name="hk_api_sender_detail"),
    url(r'^sender/(?P<mailman_id>[^/]+)/emails/$',
        api_email.EmailListBySender.as_view(), name="hk_api_sender_email_list"),
    url(r'^tags/$', api_tag.TagList.as_view(), name="hk_api_tag_list"),
    #url(r'^', include(restrouter.urls)),
    #url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
]


urlpatterns = [
    # Index
    url(r'^$', index.index, name='hk_root'),
    url(r'^find-list$', index.find_list, name='hk_find_list'),

    # User profile
    url(r'^profile/', include([
        url(r'^$', accounts.user_profile, name='hk_user_profile'),
        url(r'^favorites$', accounts.favorites, name='hk_user_favorites'),
        url(r'^last_views$', accounts.last_views, name='hk_user_last_views'),
        url(r'^votes$', accounts.votes, name='hk_user_votes'),
        url(r'^subscriptions$', accounts.subscriptions,
            name='hk_user_subscriptions'),
    ])),

    # Users
    url(r'^users/$', users.users, name='hk_users_overview'),
    url(r'^users/(?P<user_id>[^/]+)/$', accounts.public_profile, name='hk_public_user_profile'),
    url(r'^users/(?P<user_id>[^/]+)/posts$', accounts.posts, name='hk_user_posts'),

    # List archives and overview
    url(r'^list/(?P<mlist_fqdn>[^/@]+@[^/@]+)/', include(list_patterns)),

    # Messages
    url(r'^list/(?P<mlist_fqdn>[^/@]+@[^/@]+)/message/'
        r'(?P<message_id_hash>\w+)/', include(message_patterns)),
    url(r'^list/(?P<mlist_fqdn>[^/@]+@[^/@]+)/message/new$',
        message.new_message, name='hk_message_new'),

    # Threads
    url(r'^list/(?P<mlist_fqdn>[^/@]+@[^/@]+)/thread/(?P<threadid>\w+)/',
        include(thread_patterns)),

    # Search
    url(r'^search$', search.search, name='hk_search'),


    # Categories and Tags
    url(r'^categories/$', categories.categories, name='hk_categories_overview'),
    url(r'^tags/$', tags.tags, name='hk_tags_overview'),

    # Mailman archiver API
    url(r'^api/mailman/urls$', mailman.urls, name='hk_mailman_urls'),
    url(r'^api/mailman/archive$', mailman.archive, name='hk_mailman_archive'),

    # REST API
    url(r'^api/', include(api_patterns)),

    # Robots.txt
    url(r'^robots\.txt$', TemplateView.as_view(template_name="robots.txt", content_type="text/plain")),

    # Mailman 2.X compatibility
    url(r'^listinfo/?$', compat.summary),
    url(r'^listinfo/(?P<list_name>[^/]+)/?$', compat.summary),
    url(r'^pipermail/(?P<list_name>[^/]+)/?$', compat.summary),
    url(r'^pipermail/(?P<list_name>[^/]+)/(?P<year>\d\d\d\d)-(?P<month_name>\w+)/?$', compat.arch_month),
    url(r'^pipermail/(?P<list_name>[^/]+)/(?P<year>\d\d\d\d)-(?P<month_name>\w+)/(?P<summary_type>[a-z]+)\.html$', compat.arch_month),
    url(r'^pipermail/(?P<list_name>[^/]+)/(?P<year>\d\d\d\d)-(?P<month_name>\w+)\.txt.gz', compat.arch_month_mbox),
    #url(r'^pipermail/(?P<list_name>[^/]+)/(?P<year>\d\d\d\d)-(?P<month_name>\w+)/(?P<msg_num>\d+)\.html$', compat.message),
    url(r'^list/(?P<list_name>[^@]+)@[^/]+/(?P<year>\d\d\d\d)-(?P<month_name>\w+)/?$', compat.arch_month),
    #url(r'^list/(?P<list_name>[^@]+)@[^/]+/(?P<year>\d\d\d\d)-(?P<month_name>\w+)/(?P<msg_num>\d+)\.html$', compat.message),

    # URL compatibility with previous versions
    url(r'^list/(?P<list_id>[^@/]+)/', compat.redirect_list_id),
    url(r'^lists/', compat.redirect_lists),

]
#) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += staticfiles_urlpatterns()
