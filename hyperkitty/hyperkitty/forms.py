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
# Author: Aamir Khan <syst3m.w0rm@gmail.com>
# Author: Aurélien Bompard <abompard@fedoraproject.org>
#

from __future__ import absolute_import

from django import forms
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _


class TextInputWithButton(forms.TextInput):
    """
    Render a text field and a button following the Twitter Bootstrap
    directives: http://getbootstrap.com/components/#input-groups-buttons

    Use the 'button_text' class attribute to set the button's text.
    """

    def render(self, name, value, attrs=None):
        button_text = self.attrs.pop("button_text", u"")
        initial_rendering = forms.TextInput.render(
                self, name, value, attrs)
        button = mark_safe(
            u'<span class="input-group-btn"><button type="submit" '
            u'class="btn btn-default">%s</button></span>'
            % button_text)
        return "".join([
            u'<span class="input-append"><div class="input-group">',
            initial_rendering, button, u'</div></span>'])


class AddTagForm(forms.Form):
    tag = forms.CharField(
        label='', help_text=None,
        widget=TextInputWithButton(
            attrs={'placeholder': 'Add a tag...',
                   'class': 'input-medium form-control',
                   'button_text': 'Add',
                   'title': 'use commas to add multiple tags',
                   }
            )
        )
    action = forms.CharField(widget=forms.HiddenInput, initial="add")


class AttachmentFileInput(forms.FileInput):
    attach_first_text = _('Attach a file')
    attach_another_text = _('Attach another file')
    rm_text = _('Remove this file')
    template = """
<span class="attach-files-template">
    %(input)s <a href="#" title="%(rm_text)s">(-)</a>
</span>
<span class="attach-files"></span>
<a href="#" class="attach-files-first">%(attach_first_text)s</a>
<a href="#" class="attach-files-add">%(attach_another_text)s</a>
"""

    def render(self, name, value, attrs=None):
        substitutions = {
            'attach_first_text': self.attach_first_text,
            'attach_another_text': self.attach_another_text,
            'rm_text': self.rm_text,
        }
        substitutions['input'] = super(AttachmentFileInput, self).render(
            name, value, attrs)
        return mark_safe(self.template % substitutions)


class ReplyForm(forms.Form):
    newthread = forms.BooleanField(label="", required=False)
    subject = forms.CharField(
        label="", required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'New subject', 'class': 'form-control'}))
    message = forms.CharField(
        label="",
        widget=forms.Textarea(attrs={'class': 'form-control'}))
    sender = forms.ChoiceField(
        label="", required=False,
        widget=forms.Select(attrs={'class': 'form-control input-sm'}))
    #  attachment = forms.FileField(required=False, widget=AttachmentFileInput)


class PostForm(forms.Form):

    subject = forms.CharField()
    message = forms.CharField(widget=forms.Textarea)
    sender = forms.ChoiceField(
        label="", required=False,
        widget=forms.Select(attrs={'class': 'form-control input-sm'}))
    # attachment = forms.FileField(required=False, label="",
    #                              widget=AttachmentFileInput)


class CategoryForm(forms.Form):
    category = forms.ChoiceField(label="", required=False)


class MessageDeleteForm(forms.Form):
    email = forms.ModelMultipleChoiceField(
        queryset=None, widget=forms.ModelMultipleChoiceField.hidden_widget,
        )
