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

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.sites.models import Site
from django.forms.widgets import HiddenInput
from django.http import Http404
from django.shortcuts import render, redirect
from django.utils.translation import gettext as _
from django_mailman3.models import MailDomain
from django.utils.six.moves.urllib.error import HTTPError
from postorius.auth.decorators import superuser_required
from postorius.models import Domain, Mailman404Error
from postorius.forms import DomainForm


@login_required
@superuser_required
def domain_index(request):
    existing_domains = Domain.objects.all()
    for domain in existing_domains:
        try:
            web_host = MailDomain.objects.get(mail_domain=domain.mail_host)
        except MailDomain.DoesNotExist:
            site = Site.objects.get_current(request)
            web_host = MailDomain.objects.create(
                site=site, mail_domain=domain.mail_host)
        domain.site = web_host.site
    return render(request, 'postorius/domain/index.html', {
                  'domains': existing_domains,
                  })


@login_required
@superuser_required
def domain_new(request):
    form_initial = {'site': Site.objects.get_current(request)}
    if request.method == 'POST':
        form = DomainForm(request.POST, initial=form_initial)
        if form.is_valid():
            domain = Domain(mail_host=form.cleaned_data['mail_host'],
                            description=form.cleaned_data['description'],
                            owner=request.user.email)
            try:
                domain.save()
            except HTTPError as e:
                form.add_error('mail_host', e.reason)
            else:
                messages.success(request, _("New Domain registered"))
                MailDomain.objects.get_or_create(
                    site=form.cleaned_data['site'],
                    mail_domain=form.cleaned_data['mail_host'])
                return redirect("domain_index")
    else:
        form = DomainForm(initial=form_initial)
    return render(request, 'postorius/domain/new.html', {'form': form})


@login_required
@superuser_required
def domain_edit(request, domain):
    try:
        domain_obj = Domain.objects.get(mail_host=domain)
    except Mailman404Error:
        raise Http404('Domain does not exist')
    form_args = []
    if request.method == 'POST':
        form_args.append(request.POST)
    form_initial = {
        'mail_host': domain,
        'description': domain_obj.description,
        'site': MailDomain.objects.get(mail_domain=domain).site,
        }
    form = DomainForm(*form_args, initial=form_initial)
    form.fields["mail_host"].widget = HiddenInput()

    if request.method == 'POST':
        if form.is_valid():
            domain_obj.description = form.cleaned_data['description']
            try:
                web_host = MailDomain.objects.get(mail_domain=domain)
            except MailDomain.DoesNotExist:
                web_host = MailDomain.objects.create(
                    site=form.cleaned_data['site'], mail_domain=domain)
            else:
                web_host.site = form.cleaned_data['site']
                web_host.save()
            try:
                domain_obj.save()
            except HTTPError as e:
                messages.error(request, e)
            else:
                messages.success(request, _("Domain %s updated") % domain)
            return redirect("domain_edit", domain=domain)
        else:
            messages.error(request, _('Please check the errors below'))
    return render(request, 'postorius/domain/edit.html', {
                  'domain': domain, 'form': form})


@login_required
@superuser_required
def domain_delete(request, domain):
    """Deletes a domain but asks for confirmation first.
    """
    if request.method == 'POST':
        try:
            domain_obj = Domain.objects.get(mail_host=domain)
            domain_obj.delete()
            MailDomain.objects.filter(mail_domain=domain).delete()
            messages.success(request,
                             _('The domain %s has been deleted.' % domain))
            return redirect("domain_index")
        except HTTPError as e:
            messages.error(request,
                           _('The domain could not be deleted: %s' % e.msg))
            return redirect("domain_index")
    return render(request, 'postorius/domain/confirm_delete.html',
                  {'domain': domain})
