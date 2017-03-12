# -*- coding: utf-8 -*-
# Copyright (C) 1998-2016 by the Free Software Foundation, Inc.
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

import json

from email.parser import Parser as EmailParser
from email.parser import HeaderParser

from django.http import HttpResponse, Http404
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext as _
from django.core.urlresolvers import reverse

from postorius.auth.decorators import list_moderator_required
from postorius.models import List
from django_mailman3.lib.scrub import Scrubber


def parse(message):
    msgobj = EmailParser().parsestr(message)
    header_parser = HeaderParser()

    headers = []
    headers_dict = header_parser.parsestr(message)
    for key in headers_dict.keys():
        headers += ['{}: {}'.format(key, headers_dict[key])]
    content = Scrubber(msgobj).scrub()[0]
    return {
        'body': content,
        'headers': '\n'.join(headers),
    }


def get_attachments(message):
    message = EmailParser().parsestr(message)
    return Scrubber(message).scrub()[1]


@login_required
@list_moderator_required
def get_held_message(request, list_id, held_id=-1):
    """Return a held message as a json object
    """
    if held_id == -1:
        raise Http404(_('Message does not exist'))

    held_message = List.objects.get_or_404(
        fqdn_listname=list_id).get_held_message(held_id)
    if 'raw' in request.GET:
        return HttpResponse(held_message.msg, content_type='text/plain')
    response_data = dict()
    response_data['sender'] = held_message.sender
    response_data['subject'] = held_message.subject
    response_data['reason'] = held_message.reason
    response_data['hold_date'] = held_message.hold_date
    response_data['msg'] = parse(held_message.msg)
    response_data['msgid'] = held_message.request_id
    response_data['attachments'] = []
    attachments = get_attachments(held_message.msg)
    for attachment in attachments:
        counter, name, content_type, encoding, content = attachment
        response_data['attachments'].append(
            (reverse('rest_attachment_for_held_message',
                     args=(list_id, held_id, counter)), name))

    return HttpResponse(json.dumps(response_data),
                        content_type='application/json')


@login_required
@list_moderator_required
def get_attachment_for_held_message(request, list_id, held_id, attachment_id):
    held_message = List.objects.get_or_404(
        fqdn_listname=list_id).get_held_message(held_id)
    attachments = get_attachments(held_message.msg)
    for attachment in attachments:
        if attachment[0] == int(attachment_id):
            response = HttpResponse(attachment[4], content_type=attachment[2])
            response['Content-Disposition'] = \
                'attachment;filename="{}"'.format(attachment[1])
            return response
    raise Http404(_('Attachment does not exist'))
