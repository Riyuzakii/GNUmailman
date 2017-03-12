# Copyright (C) 2010-2017 The Free Software Foundation, Inc.
#
# This file is part of mailman.client.
#
# mailman.client is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by the
# Free Software Foundation, version 3 of the License.
#
# mailman.client is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public
# License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with mailman.client.  If not, see <http://www.gnu.org/licenses/>.

"""Client code."""

from __future__ import absolute_import, unicode_literals

import six
import json
import warnings

from base64 import b64encode
from collections import Sequence, MutableMapping
from httplib2 import Http
from mailmanclient.constants import (
    __version__, DEFAULT_PAGE_ITEM_COUNT, MISSING)
from operator import itemgetter
from six.moves.urllib_error import HTTPError
from six.moves.urllib_parse import (
    urlencode, urljoin, urlsplit, urlunsplit, parse_qs)


__metaclass__ = type
__all__ = [
    'Client',
    'MailmanConnectionError',
]


class MailmanConnectionError(Exception):
    """Custom Exception to catch connection errors."""


class Connection:
    """A connection to the REST client."""

    def __init__(self, baseurl, name=None, password=None):
        """Initialize a connection to the REST API.

        :param baseurl: The base url to access the Mailman 3 REST API.
        :param name: The Basic Auth user name.  If given, the `password` must
            also be given.
        :param password: The Basic Auth password.  If given the `name` must
            also be given.
        """
        if baseurl[-1] != '/':
            baseurl += '/'
        self.baseurl = baseurl
        self.name = name
        self.password = password
        if name is not None and password is None:
            raise TypeError('`password` is required when `name` is given')
        if name is None and password is not None:
            raise TypeError('`name` is required when `password` is given')
        if name is None:
            self.basic_auth = None
        else:
            auth = '{0}:{1}'.format(name, password)
            self.basic_auth = b64encode(auth.encode('utf-8')).decode('utf-8')

    def call(self, path, data=None, method=None):
        """Make a call to the Mailman REST API.

        :param path: The url path to the resource.
        :type path: str
        :param data: Data to send, implies POST (default) or PUT.
        :type data: dict
        :param method: The HTTP method to call.  Defaults to GET when `data`
            is None or POST if `data` is given.
        :type method: str
        :return: The response content, which will be None, a dictionary, or a
            list depending on the actual JSON type returned.
        :rtype: None, list, dict
        :raises HTTPError: when a non-2xx status code is returned.
        """
        headers = {
            'User-Agent': 'GNU Mailman REST client v{0}'.format(__version__),
            }
        if data is not None:
            data = urlencode(data, doseq=True)
            headers['Content-Type'] = 'application/x-www-form-urlencoded'
        if method is None:
            if data is None:
                method = 'GET'
            else:
                method = 'POST'
        method = method.upper()
        if self.basic_auth:
            headers['Authorization'] = 'Basic ' + self.basic_auth
        url = urljoin(self.baseurl, path)
        try:
            response, content = Http().request(url, method, data, headers)
            # If we did not get a 2xx status code, make this look like a
            # urllib2 exception, for backward compatibility.
            if response.status // 100 != 2:
                raise HTTPError(url, response.status, content, response, None)
            if len(content) == 0:
                return response, None
            # XXX Work around for http://bugs.python.org/issue10038
            if isinstance(content, six.binary_type):
                content = content.decode('utf-8')
            return response, json.loads(content)
        except HTTPError:
            raise
        except IOError:
            raise MailmanConnectionError('Could not connect to Mailman API')


class RESTBase:
    """
    Base class for data coming from the REST API.

    Subclasses can (and sometimes must) define some attributes to handle a
    particular entity.

    :cvar _properties: the list of expected entity properties. This is required
      for API elements that behave like an object, with REST data accessed
      through attributes. If this value is None, the REST data is used to
      list available properties.
    :cvar _writable_properties: list of properties that can be written to using
        a `PATCH` request. If this value is `None`, all properties are
        writable.
    :cvar _read_only_properties: list of properties that cannot be written to
      (defaults to `self_link` only).
    :cvar _autosave: automatically send a `PATCH` request to the API when a
        value is changed. Otherwise, the `save()` method must be called.
    """

    _properties = None
    _writable_properties = None
    _read_only_properties = ['self_link']
    _autosave = False

    def __init__(self, connection, url, data=None):
        """
        :param connection: An API connection object.
        :type connection: Connection.
        :param url: The url of the API endpoint.
        :type url: str.
        :param data: The initial data to use.
        :type data: dict.
        """
        self._connection = connection
        self._url = url
        self._rest_data = data
        self._changed_rest_data = {}

    def __repr__(self):
        return '<{0} at {1}>'.format(self.__class__.__name__, self._url)

    @property
    def rest_data(self):
        """Get data from API and cache it (only once per instance)."""
        if self._rest_data is None:
            response, content = self._connection.call(self._url)
            if isinstance(content, dict) and 'http_etag' in content:
                del content['http_etag']  # We don't care about etags.
            self._rest_data = content
        return self._rest_data

    def _get(self, key):
        if self._properties is not None:
            # Some REST key/values may not be returned by Mailman if the value
            # is None.
            if key in self._properties:
                return self.rest_data.get(key)
            raise KeyError(key)
        else:
            return self.rest_data[key]

    def _set(self, key, value):
        if (key in self._read_only_properties or (
                self._writable_properties is not None
                and key not in self._writable_properties)):
            raise ValueError('value is read-only')
        # Don't check that the key is in _properties, the accepted values for
        # write may be different from the returned values (eg: User.password
        # and User.cleartext_password).
        if key in self.rest_data and self.rest_data[key] == value:
            return  # Nothing to do
        self._changed_rest_data[key] = value
        if self._autosave:
            self.save()

    def _reset_cache(self):
        self._changed_rest_data = {}
        self._rest_data = None

    def save(self):
        response, content = self._connection.call(
            self._url, self._changed_rest_data, method='PATCH')
        self._reset_cache()


class RESTObject(RESTBase):
    """Base class for REST data that behaves like an object with attributes."""

    def __getattr__(self, name):
        try:
            return self._get(name)
        except KeyError:
            # Transform the KeyError into the more appropriate AttributeError
            raise AttributeError(
                "'{0}' object has no attribute '{1}'".format(
                    self.__class__.__name__, name))

    def __setattr__(self, name, value):
        # RESTObject must list REST-specific properties or we won't be able to
        # store the _connection, _url, etc.
        assert self._properties is not None
        if name not in self._properties:
            return super(RESTObject, self).__setattr__(name, value)
        return self._set(name, value)

    def delete(self):
        self._connection.call(self._url, method='DELETE')
        self._reset_cache()


class RESTDict(RESTBase, MutableMapping):
    """Base class for REST data that behaves like a dictionary."""

    def __repr__(self):
        return repr(self.rest_data)

    def __unicode__(self):
        return unicode(self.rest_data)

    def __getitem__(self, key):
        return self._get(key)

    def __setitem__(self, key, value):
        self._set(key, value)

    def __delitem__(self, key):
        raise NotImplementedError("REST dictionnary keys can't be deleted.")

    def __iter__(self):
        for key in self.rest_data:
            if self._properties is not None and key not in self._properties:
                continue
            yield key

    def __len__(self):
        return len(self.rest_data)

    def get(self, key, default=None):
        return self.rest_data.get(key, default)

    def keys(self):
        return list(self)

    def update(self, other):
        # Optimize the update to call save() only once
        _old_autosave = self._autosave
        self._autosave = False
        super(RESTDict, self).update(other)
        self._autosave = _old_autosave
        if self._autosave:
            self.save()


class RESTList(RESTBase, Sequence):
    """
    Base class for REST data that behaves like a list.

    The `_factory` attribute is a callable that will be applied on each
    returned member of the list.
    """

    _factory = lambda x: x  # flake8: noqa

    @property
    def rest_data(self):
        if self._rest_data is None:
            response, content = self._connection.call(self._url)
            if 'entries' not in content:
                self._rest_data = []
            else:
                self._rest_data = content['entries']
        return self._rest_data

    def __repr__(self):
        return repr(self.rest_data)

    def __unicode__(self):
        return unicode(self.rest_data)

    def __getitem__(self, key):
        return self._factory(self.rest_data[key])

    def __delitem__(self, key):
        self[key].delete()
        self._reset_cache()

    def __len__(self):
        return len(self.rest_data)

    def __iter__(self):
        for entry in self.rest_data:
            yield self._factory(entry)

    def clear(self):
        self._connection.call(self._url, method='DELETE')
        self._reset_cache()


class PreferencesMixin:
    """Mixin for objects that have preferences."""

    @property
    def preferences(self):
        if getattr(self, '_preferences', None) is None:
            path = '{0}/preferences'.format(self.self_link)
            self._preferences = Preferences(self._connection, path)
        return self._preferences


class Page:

    def __init__(self, connection, path, model, count=DEFAULT_PAGE_ITEM_COUNT,
                 page=1):
        self._connection = connection
        self._path = path
        self._count = count
        self._page = page
        self._model = model
        self._entries = []
        self.total_size = 0
        self._create_page()

    def __getitem__(self, key):
        return self._entries[key]

    def __iter__(self):
        for entry in self._entries:
            yield entry

    def __repr__(self):
        return '<Page {0} ({1})'.format(self._page, self._model)

    def __len__(self):
        return len(self._entries)

    def _build_url(self):
        url = list(urlsplit(self._path))
        qs = parse_qs(url[3])
        qs["count"] = self._count
        qs["page"] = self._page
        url[3] = urlencode(qs, doseq=True)
        return urlunsplit(url)

    def _create_page(self):
        self._entries = []
        response, content = self._connection.call(self._build_url())
        self.total_size = content["total_size"]
        for entry in content.get('entries', []):
            instance = self._model(
                self._connection, entry['self_link'], entry)
            self._entries.append(instance)

    @property
    def nr(self):
        return self._page

    @property
    def next(self):
        return self.__class__(
            self._connection, self._path, self._model, self._count,
            self._page + 1)

    @property
    def previous(self):
        if self.has_previous:
            return self.__class__(
                self._connection, self._path, self._model, self._count,
                self._page - 1)

    @property
    def has_previous(self):
        return self._page > 1

    @property
    def has_next(self):
        return self._count * self._page < self.total_size


#
# --- The following classes are part of the API
#

class Client:
    """Access the Mailman REST API root."""

    def __init__(self, baseurl, name=None, password=None):
        """Initialize client access to the REST API.

        :param baseurl: The base url to access the Mailman 3 REST API.
        :param name: The Basic Auth user name.  If given, the `password` must
            also be given.
        :param password: The Basic Auth password.  If given the `name` must
            also be given.
        """
        self._connection = Connection(baseurl, name, password)

    def __repr__(self):
        return '<Client ({0.name}:{0.password}) {0.baseurl}>'.format(
            self._connection)

    @property
    def system(self):
        return self._connection.call('system/versions')[1]

    @property
    def preferences(self):
        return Preferences(self._connection, 'system/preferences')

    @property
    def pipelines(self):
        response, content = self._connection.call('system/pipelines')
        return content

    @property
    def chains(self):
        response, content = self._connection.call('system/chains')
        return content

    @property
    def queues(self):
        response, content = self._connection.call('queues')
        queues = {}
        for entry in content['entries']:
            queues[entry['name']] = Queue(
                self._connection, entry['self_link'], entry)
        return queues

    @property
    def lists(self):
        return self.get_lists()

    def get_lists(self, advertised=None):
        url = 'lists'
        if advertised:
            url += '?advertised=true'
        response, content = self._connection.call(url)
        if 'entries' not in content:
            return []
        return [MailingList(self._connection, entry['self_link'], entry)
                for entry in content['entries']]

    def get_list_page(self, count=50, page=1, advertised=None):
        url = 'lists'
        if advertised:
            url += '?advertised=true'
        return Page(self._connection, url, MailingList, count, page)

    @property
    def domains(self):
        response, content = self._connection.call('domains')
        if 'entries' not in content:
            return []
        return [Domain(self._connection, entry['self_link'])
                for entry in sorted(content['entries'],
                                    key=itemgetter('mail_host'))]

    @property
    def members(self):
        response, content = self._connection.call('members')
        if 'entries' not in content:
            return []
        return [Member(self._connection, entry['self_link'], entry)
                for entry in content['entries']]

    def get_member(self, fqdn_listname, subscriber_address):
        return self.get_list(fqdn_listname).get_member(subscriber_address)

    def get_member_page(self, count=50, page=1):
        return Page(self._connection, 'members', Member, count, page)

    @property
    def users(self):
        response, content = self._connection.call('users')
        if 'entries' not in content:
            return []
        return [User(self._connection, entry['self_link'], entry)
                for entry in sorted(content['entries'],
                                    key=itemgetter('self_link'))]

    def get_user_page(self, count=50, page=1):
        return Page(self._connection, 'users', User, count, page)

    def create_domain(self, mail_host, base_url=MISSING,
                      description=None, owner=None):
        if base_url is not MISSING:
            warnings.warn(
                'The `base_url` parameter in the `create_domain()` method is '
                'deprecated. It is not used any more and will be removed in '
                'the future.', DeprecationWarning, stacklevel=2)
        data = dict(mail_host=mail_host)
        if description is not None:
            data['description'] = description
        if owner is not None:
            data['owner'] = owner
        response, content = self._connection.call('domains', data)
        return Domain(self._connection, response['location'])

    def delete_domain(self, mail_host):
        response, content = self._connection.call(
            'domains/{0}'.format(mail_host), None, 'DELETE')

    def get_domain(self, mail_host, web_host=MISSING):
        """Get domain by its mail_host or its web_host."""
        if web_host is not MISSING:
            warnings.warn(
                'The `web_host` parameter in the `get_domain()` method is '
                'deprecated. It is not used any more and will be removed in '
                'the future.', DeprecationWarning, stacklevel=2)
        response, content = self._connection.call(
            'domains/{0}'.format(mail_host))
        return Domain(self._connection, content['self_link'])

    def create_user(self, email, password, display_name=''):
        response, content = self._connection.call(
            'users', dict(email=email,
                          password=password,
                          display_name=display_name))
        return User(self._connection, response['location'])

    def get_user(self, address):
        response, content = self._connection.call(
            'users/{0}'.format(address))
        return User(self._connection, content['self_link'], content)

    def get_address(self, address):
        response, content = self._connection.call(
            'addresses/{0}'.format(address))
        return Address(self._connection, content['self_link'], content)

    def get_list(self, fqdn_listname):
        response, content = self._connection.call(
            'lists/{0}'.format(fqdn_listname))
        return MailingList(self._connection, content['self_link'], content)

    def delete_list(self, fqdn_listname):
        response, content = self._connection.call(
            'lists/{0}'.format(fqdn_listname), None, 'DELETE')

    @property
    def bans(self):
        return Bans(self._connection, 'bans', mlist=None)

    def get_bans_page(self, count=50, page=1):
        return Page(self._connection, 'bans', BannedAddress, count, page)


class Domain(RESTObject):

    _properties = ('description', 'mail_host', 'self_link')

    def __repr__(self):
        return '<Domain "{0}">'.format(self.mail_host)

    @property
    def web_host(self):
        warnings.warn(
            'The `Domain.web_host` attribute is deprecated. It is not used '
            'any more and will be removed in the future.',
            DeprecationWarning, stacklevel=2)
        return 'http://{}'.format(self.mail_host)

    @property
    def base_url(self):
        warnings.warn(
            'The `Domain.base_url` attribute is deprecated. It is not used '
            'any more and will be removed in the future.',
            DeprecationWarning, stacklevel=2)
        return 'http://{}'.format(self.mail_host)

    @property
    def owners(self):
        url = self._url + '/owners'
        response, content = self._connection.call(url)
        if 'entries' not in content:
            return []
        else:
            return [item for item in content['entries']]

    @property
    def lists(self):
        return self.get_lists()

    def get_lists(self, advertised=None):
        url = 'domains/{0}/lists'.format(self.mail_host)
        if advertised:
            url += '?advertised=true'
        response, content = self._connection.call(url)
        if 'entries' not in content:
            return []
        return [MailingList(self._connection, entry['self_link'], entry)
                for entry in content['entries']]

    def get_list_page(self, count=50, page=1, advertised=None):
        url = 'domains/{0}/lists'.format(self.mail_host)
        if advertised:
            url += '?advertised=true'
        return Page(self._connection, url, MailingList, count, page)

    def create_list(self, list_name):
        fqdn_listname = '{0}@{1}'.format(list_name, self.mail_host)
        response, content = self._connection.call(
            'lists', dict(fqdn_listname=fqdn_listname))
        return MailingList(self._connection, response['location'])

    # def remove_owner(self, owner):
    #     TODO: add this when API supports it.
    #     pass

    def remove_all_owners(self):
        url = self._url + '/owners'
        response, content = self._connection.call(
            url, method='DELETE')
        return response

    def add_owner(self, owner):
        url = self._url + '/owners'
        response, content = self._connection.call(
            url, {'owner': owner})


class MailingList(RESTObject):

    _properties = ('display_name', 'fqdn_listname', 'list_id', 'list_name',
                   'mail_host', 'member_count', 'volume', 'self_link')

    def __init__(self, connection, url, data=None):
        super(MailingList, self).__init__(connection, url, data)
        self._settings = None

    def __repr__(self):
        return '<List "{0}">'.format(self.fqdn_listname)

    @property
    def owners(self):
        url = self._url + '/roster/owner'
        response, content = self._connection.call(url)
        if 'entries' not in content:
            return []
        else:
            return [item['email'] for item in content['entries']]

    @property
    def moderators(self):
        url = self._url + '/roster/moderator'
        response, content = self._connection.call(url)
        if 'entries' not in content:
            return []
        else:
            return [item['email'] for item in content['entries']]

    @property
    def members(self):
        url = 'lists/{0}/roster/member'.format(self.fqdn_listname)
        response, content = self._connection.call(url)
        if 'entries' not in content:
            return []
        return [Member(self._connection, entry['self_link'], entry)
                for entry in sorted(content['entries'],
                                    key=itemgetter('address'))]

    @property
    def nonmembers(self):
        url = 'members/find'
        data = {'role': 'nonmember',
                'list_id': self.list_id}
        response, content = self._connection.call(url, data)
        if 'entries' not in content:
            return []
        return [Member(self._connection, entry['self_link'], entry)
                for entry in sorted(content['entries'],
                                    key=itemgetter('address'))]

    def get_member_page(self, count=50, page=1):
        url = 'lists/{0}/roster/member'.format(self.fqdn_listname)
        return Page(self._connection, url, Member, count, page)

    def find_members(self, address, role='member', page=None, count=50):
        data = {
            'subscriber': address,
            'role': role,
            'list_id': self.list_id,
            }
        url = 'members/find?{}'.format(urlencode(data, doseq=True))
        if page is None:
            response, content = self._connection.call(url, data)
            if 'entries' not in content:
                return []
            return [Member(self._connection, entry['self_link'], entry)
                    for entry in content['entries']]
        else:
            return Page(self._connection, url, Member, count, page)

    @property
    def settings(self):
        if self._settings is None:
            self._settings = Settings(
                self._connection,
                'lists/{0}/config'.format(self.fqdn_listname))
        return self._settings

    @property
    def held(self):
        """Return a list of dicts with held message information."""
        response, content = self._connection.call(
            'lists/{0}/held'.format(self.fqdn_listname), None, 'GET')
        if 'entries' not in content:
            return []
        return [HeldMessage(self._connection, entry['self_link'], entry)
                for entry in content['entries']]

    def get_held_page(self, count=50, page=1):
        url = 'lists/{0}/held'.format(self.fqdn_listname)
        return Page(self._connection, url, HeldMessage, count, page)

    def get_held_message(self, held_id):
        url = 'lists/{0}/held/{1}'.format(self.fqdn_listname, held_id)
        return HeldMessage(self._connection, url)

    @property
    def requests(self):
        """Return a list of dicts with subscription requests."""
        response, content = self._connection.call(
            'lists/{0}/requests'.format(self.fqdn_listname), None, 'GET')
        if 'entries' not in content:
            return []
        else:
            entries = []
            for entry in content['entries']:
                request = dict(email=entry['email'],
                               token=entry['token'],
                               token_owner=entry['token_owner'],
                               list_id=entry['list_id'],
                               request_date=entry['when'])
                entries.append(request)
        return entries

    @property
    def archivers(self):
        url = 'lists/{0}/archivers'.format(self.list_id)
        return ListArchivers(self._connection, url, self)

    @archivers.setter
    def archivers(self, new_value):
        url = 'lists/{0}/archivers'.format(self.list_id)
        archivers = ListArchivers(self._connection, url, self)
        archivers.update(new_value)
        archivers.save()

    def add_owner(self, address):
        self.add_role('owner', address)

    def add_moderator(self, address):
        self.add_role('moderator', address)

    def add_role(self, role, address):
        data = dict(list_id=self.list_id,
                    subscriber=address,
                    role=role)
        self._connection.call('members', data)

    def remove_owner(self, address):
        self.remove_role('owner', address)

    def remove_moderator(self, address):
        self.remove_role('moderator', address)

    def remove_role(self, role, address):
        url = 'lists/%s/%s/%s' % (self.fqdn_listname, role, address)
        self._connection.call(url, method='DELETE')

    def moderate_message(self, request_id, action):
        """Moderate a held message.

        :param request_id: Id of the held message.
        :type request_id: Int.
        :param action: Action to perform on held message.
        :type action: String.
        """
        path = 'lists/{0}/held/{1}'.format(
            self.fqdn_listname, str(request_id))
        response, content = self._connection.call(
            path, dict(action=action), 'POST')
        return response

    def discard_message(self, request_id):
        """Shortcut for moderate_message."""
        return self.moderate_message(request_id, 'discard')

    def reject_message(self, request_id):
        """Shortcut for moderate_message."""
        return self.moderate_message(request_id, 'reject')

    def defer_message(self, request_id):
        """Shortcut for moderate_message."""
        return self.moderate_message(request_id, 'defer')

    def accept_message(self, request_id):
        """Shortcut for moderate_message."""
        return self.moderate_message(request_id, 'accept')

    def moderate_request(self, request_id, action):
        """
        Moderate a subscription request.

        :param action: accept|reject|discard|defer
        :type action: str.
        """
        path = 'lists/{0}/requests/{1}'.format(self.list_id, request_id)
        response, content = self._connection.call(path, {'action': action})
        return response

    def manage_request(self, token, action):
        """Alias for moderate_request, kept for compatibility"""
        warnings.warn(
            'The `manage_request()` method has been replaced by '
            '`moderate_request()` and will be removed in the future.',
            DeprecationWarning, stacklevel=2)
        return self.moderate_request(token, action)

    def accept_request(self, request_id):
        """Shortcut to accept a subscription request."""
        return self.moderate_request(request_id, 'accept')

    def reject_request(self, request_id):
        """Shortcut to reject a subscription request."""
        return self.moderate_request(request_id, 'reject')

    def discard_request(self, request_id):
        """Shortcut to discard a subscription request."""
        return self.moderate_request(request_id, 'discard')

    def defer_request(self, request_id):
        """Shortcut to defer a subscription request."""
        return self.moderate_request(request_id, 'defer')

    def get_member(self, email):
        """Get a membership.

        :param address: The email address of the member for this list.
        :return: A member proxy object.
        """
        # In order to get the member object we query the REST API for
        # the member. Incase there is no matching subscription, an
        # HTTPError is returned instead.
        try:
            path = 'lists/{0}/member/{1}'.format(self.list_id, email)
            response, content = self._connection.call(path)
            return Member(self._connection, content['self_link'], content)
        except HTTPError:
            raise ValueError('%s is not a member address of %s' %
                             (email, self.fqdn_listname))

    def subscribe(self, address, display_name=None, pre_verified=False,
                  pre_confirmed=False, pre_approved=False):
        """Subscribe an email address to a mailing list.

        :param address: Email address to subscribe to the list.
        :type address: str
        :param display_name: The real name of the new member.
        :param pre_verified: True if the address has been verified.
        :type pre_verified: bool
        :param pre_confirmed: True if membership has been approved by the user.
        :type pre_confirmed: bool
        :param pre_approved: True if membership is moderator-approved.
        :type pre_approved: bool
        :type display_name: str
        :return: A member proxy object.
        """
        data = dict(
            list_id=self.list_id,
            subscriber=address,
            display_name=display_name,
            )
        if pre_verified:
            data['pre_verified'] = True
        if pre_confirmed:
            data['pre_confirmed'] = True
        if pre_approved:
            data['pre_approved'] = True
        response, content = self._connection.call('members', data)
        # If a member is not immediately subscribed (i.e. verificatoin,
        # confirmation or approval need), the response content is returned.
        if response.status == 202:
            return content
        # I the subscription is executed immediately, a member object
        # is returned.
        return Member(self._connection, response['location'])

    def unsubscribe(self, email):
        """Unsubscribe an email address from a mailing list.

        :param address: The address to unsubscribe.
        """
        # In order to get the member object we need to
        # iterate over the existing member list

        try:
            path = 'lists/{0}/member/{1}'.format(self.list_id, email)
            self._connection.call(path, method='DELETE')
        except HTTPError:
            # The member link does not exist, i.e. he is not a member
            raise ValueError('%s is not a member address of %s' %
                             (email, self.fqdn_listname))

    @property
    def bans(self):
        url = 'lists/{0}/bans'.format(self.list_id)
        return Bans(self._connection, url, mlist=self)

    def get_bans_page(self, count=50, page=1):
        url = 'lists/{0}/bans'.format(self.list_id)
        return Page(self._connection, url, BannedAddress, count, page)

    @property
    def header_matches(self):
        url = 'lists/{0}/header-matches'.format(self.list_id)
        return HeaderMatches(self._connection, url, self)


class ListArchivers(RESTDict):
    """
    Represents the activation status for each site-wide available archiver
    for a given list.
    """

    _autosave = True

    def __init__(self, connection, url, mlist):
        """
        :param connection: An API connection object.
        :type connection: Connection.
        :param url: The API url of the list's archiver endpoint.
        :type url: str.
        :param mlist: The corresponding list object.
        :type mlist: MailingList.
        """
        super(ListArchivers, self).__init__(connection, url)
        self._mlist = mlist

    def __repr__(self):
        return '<Archivers on "{0}">'.format(self._mlist.list_id)


class Bans(RESTList):
    """
    The list of banned addresses from a mailing-list or from the whole site.
    """

    def __init__(self, connection, url, data=None, mlist=None):
        """
        :param mlist: The corresponding list object, or None if it is a global
            ban list.
        :type mlist: MailingList or None.
        """
        super(Bans, self).__init__(connection, url, data)
        self._mlist = mlist
        self._factory = lambda data: BannedAddress(
            self._connection, data['self_link'], data)

    def __repr__(self):
        if self._mlist is None:
            return '<Global bans>'
        else:
            return '<Bans on "{0}">'.format(self._mlist.list_id)

    def __contains__(self, item):
        # Accept email addresses and BannedAddress objects
        if isinstance(item, BannedAddress):
            item = item.email
        if self._rest_data is not None:
            return item in [data['email'] for data in self._rest_data]
        else:
            # Avoid getting the whole list just to check membership
            try:
                response, content = self._connection.call(
                    '{}/{}'.format(self._url, item))
            except HTTPError as e:
                if e.code == 404:
                    return False
                else:
                    raise
            else:
                return True

    def add(self, email):
        response, content = self._connection.call(self._url, dict(email=email))
        self._reset_cache()
        return BannedAddress(self._connection, response['location'])

    def find_by_email(self, email):
        for ban in self:
            if ban.email == email:
                return ban
        return None

    def remove(self, email):
        ban = self.find_by_email(email)
        if ban is not None:
            ban.delete()
            self._reset_cache()
        else:
            raise ValueError('The address {} is not banned'.format(email))


class BannedAddress(RESTObject):

    _properties = ('email', 'list_id', 'self_link')
    _writable_properties = []

    def __repr__(self):
        return self.email

    @property
    def mailinglist(self):
        return MailingList(
            self._connection, 'lists/{0}'.format(self.list_id))


class HeaderMatches(RESTList):
    """
    The list of header matches for a mailing-list.
    """

    def __init__(self, connection, url, mlist):
        """
        :param mlist: The corresponding list object.
        :type mlist: MailingList.
        """
        super(HeaderMatches, self).__init__(connection, url)
        self._mlist = mlist
        self._factory = lambda data: HeaderMatch(
            self._connection, data['self_link'], data)

    def __repr__(self):
        return '<HeaderMatches for "{0}">'.format(self._mlist.list_id)

    def add(self, header, pattern, action=None):
        """
        :param header: The header to consider.
        :type  header: str
        :param pattern: The regular expression to use for filtering.
        :type  pattern: str
        :param action: The action to take when the header matches the pattern.
            This can be 'accept', 'discard', 'reject', or 'hold'.
        :type  action: str
        """
        data = dict(header=header, pattern=pattern)
        if action is not None:
            data['action'] = action
        response, content = self._connection.call(self._url, data)
        self._reset_cache()
        return HeaderMatch(self._connection, response['location'])


class HeaderMatch(RESTObject):

    _properties = ('header', 'pattern', 'position', 'action', 'self_link')
    _writable_properties = ('header', 'pattern', 'position', 'action')

    def __repr__(self):
        return '<HeaderMatch on "{0}">'.format(self.header)


class Member(RESTObject, PreferencesMixin):

    _properties = ('delivery_mode', 'email', 'list_id', 'moderation_action',
                   'role', 'self_link')
    _writable_properties = ('address', 'delivery_mode', 'moderation_action')

    def __repr__(self):
        return '<Member "{0}" on "{1}">'.format(self.email, self.list_id)

    def __unicode__(self):
        return '<Member "{0}" on "{1}">'.format(self.email, self.list_id)

    @property
    def address(self):
        return Address(self._connection, self.rest_data['address'])

    @property
    def user(self):
        return User(self._connection, self.rest_data['user'])

    def unsubscribe(self):
        """Unsubscribe the member from a mailing list.
        """
        # TODO: call .delete() instead?
        self._connection.call(self.self_link, method='DELETE')


class User(RESTObject, PreferencesMixin):

    _properties = ('created_on', 'display_name', 'is_server_owner',
                   'password', 'self_link', 'user_id')
    _writable_properties = ('cleartext_password', 'display_name',
                            'is_server_owner')

    def __init__(self, connection, url, data=None):
        super(User, self).__init__(connection, url, data)
        self._subscriptions = None
        self._subscription_list_ids = None

    def __repr__(self):
        return '<User "{0}" ({1})>'.format(self.display_name, self.user_id)

    @property
    def addresses(self):
        return Addresses(
            self._connection, 'users/{0}/addresses'.format(self.user_id))

    def __setattr__(self, name, value):
        """Special case for the password"""
        if name == 'password':
            self._changed_rest_data['cleartext_password'] = value
            if self._autosave:
                self.save()
        else:
            super(User, self).__setattr__(name, value)

    @property
    def subscriptions(self):
        if self._subscriptions is None:
            subscriptions = []
            for address in self.addresses:
                response, content = self._connection.call(
                    'members/find', data={'subscriber': address})
                try:
                    for entry in content['entries']:
                        subscriptions.append(Member(
                            self._connection, entry['self_link'], entry))
                except KeyError:
                    pass
            self._subscriptions = subscriptions
        return self._subscriptions

    @property
    def subscription_list_ids(self):
        if self._subscription_list_ids is None:
            list_ids = []
            for sub in self.subscriptions:
                list_ids.append(sub.list_id)
            self._subscription_list_ids = list_ids
        return self._subscription_list_ids

    def add_address(self, email, absorb_existing=False):
        """
        Adds another email adress to the user record and returns an
        _Address object.

        :param email: The address to add
        :type  email: str.
        :param absorb_existing: set this to True if you want to add the address
            even if it already exists. It will import the existing user into
            the current one, not overwriting any previously set value.
        :type  absorb_existing: bool.
        """
        url = '{0}/addresses'.format(self._url)
        data = {'email': email}
        if absorb_existing:
            data['absorb_existing'] = 1
        response, content = self._connection.call(url, data)
        address = {
            'email': email,
            'self_link': response['location'],
        }
        return Address(self._connection, address['self_link'], address)


class Addresses(RESTList):

    def __init__(self, connection, url, data=None):
        super(Addresses, self).__init__(connection, url, data)
        self._factory = lambda data: Address(
            self._connection, data['self_link'], data)

    def find_by_email(self, email):
        for address in self:
            if address.email == email:
                return address
        return None

    def remove(self, email):
        address = self.find_by_email(email)
        if address is not None:
            address.delete()
            self._reset_cache()
        else:
            raise ValueError('The address {} does not exist'.format(email))


class Address(RESTObject, PreferencesMixin):

    _properties = ('display_name', 'email', 'original_email', 'registered_on',
                   'self_link', 'verified_on')

    def __repr__(self):
        return self.email

    @property
    def user(self):
        if 'user' in self.rest_data:
            return User(self._connection, self.rest_data['user'])
        else:
            return None

    @property
    def verified(self):
        return self.verified_on is not None

    def verify(self):
        self._connection.call(
            'addresses/{0}/verify'.format(self.email), method='POST')
        self._reset_cache()

    def unverify(self):
        self._connection.call(
            'addresses/{0}/unverify'.format(self.email), method='POST')
        self._reset_cache()


class HeldMessage(RESTObject):

    _properties = ('hold_date', 'message_id', 'msg', 'reason', 'request_id',
                   'self_link', 'sender', 'subject', 'type')

    def __repr__(self):
        return '<HeldMessage "{0}" by {1}>'.format(
            self.request_id, self.sender)

    def __unicode__(self):
        return unicode(self.rest_data)

    def moderate(self, action):
        """Moderate a held message.

        :param action: Action to perform on held message.
        :type action: String.
        """
        response, content = self._connection.call(
            self._url, dict(action=action), 'POST')
        return response

    def discard(self):
        """Shortcut for moderate."""
        return self.moderate('discard')

    def reject(self):
        """Shortcut for moderate."""
        return self.moderate('reject')

    def defer(self):
        """Shortcut for moderate."""
        return self.moderate('defer')

    def accept(self):
        """Shortcut for moderate."""
        return self.moderate('accept')


class Preferences(RESTDict):

    _properties = (
        'acknowledge_posts', 'delivery_mode', 'delivery_status',
        'hide_address', 'preferred_language', 'receive_list_copy',
        'receive_own_postings',
        )

    def delete(self):
        response, content = self._connection.call(self._url, method='DELETE')


class Settings(RESTDict):

    _read_only_properties = (
        'bounces_address',
        'created_at',
        'digest_last_sent_at',
        'fqdn_listname',
        'join_address',
        'last_post_at',
        'leave_address',
        'list_id',
        'list_name',
        'mail_host',
        'next_digest_number',
        'no_reply_address',
        'owner_address',
        'post_id',
        'posting_address',
        'request_address',
        'scheme',
        'self_link',
        'volume',
        'web_host',
        )


class Queue(RESTObject):

    _properties = ('name', 'directory', 'files')

    def __repr__(self):
        return '<Queue: {}>'.format(self.name)

    def inject(self, list_id, text):
        self._connection.call(self._url, dict(list_id=list_id, text=text))

    @property
    def files(self):
        # No caching.
        response, content = self._connection.call(self._url)
        return content['files']
