# Copyright (C) 2015-2017 The Free Software Foundation, Inc.
#
# This file is part of GNU Mailman.
#
# GNU Mailman is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# GNU Mailman is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# GNU Mailman.  If not, see <http://www.gnu.org/licenses/>.

"""Helpers for VCR"""

import vcr

from functools import update_wrapper
from six import binary_type, text_type
from six.moves.urllib.parse import urlparse, urlunparse, parse_qsl, urlencode


__all__ = [
    'get_vcr',
    ]


def filter_response_headers(response):
    for header in ('Date', 'Server', 'date', 'server'):
        # The headers are lowercase on Python 2 and capitalized on Python 3
        if header in response['headers']:
            del response['headers'][header]
    return response


def reorder_request_params(request):
    def reorder_params(params):
        parsed = parse_qsl(params)
        if parsed:
            return urlencode(sorted(parsed, key=lambda kv: kv[0]))
        else:
            # Parsing failed, it may be a simple string.
            return params
    # sort the URL query-string by key names.
    uri_parts = urlparse(request.uri)
    if uri_parts.query:
        request.uri = urlunparse((
            uri_parts.scheme, uri_parts.netloc, uri_parts.path,
            uri_parts.params, reorder_params(uri_parts.query),
            uri_parts.fragment,
            ))
    # convert the request body to text and sort the parameters.
    if isinstance(request.body, binary_type):
        try:
            request._body = request._body.decode('utf-8')
        except UnicodeDecodeError:
            pass
    if isinstance(request.body, text_type):
        request._body = reorder_params(request._body)
    return request


def get_vcr(**kwargs):
    return vcr.VCR(
        filter_headers=['authorization', 'user-agent', 'date'],
        before_record=reorder_request_params,
        before_record_response=filter_response_headers,
        **kwargs
        )


class vcr_testcase:
    """
    Decorator for TestCases that use VCR.
    It automatically sets up a different cassette for each test function.
    """

    def __init__(self, vcr_instance):
        self.vcr = vcr_instance

    def __call__(self, testcase):
        return self.decorate_class(testcase)

    def decorate_class(self, testcase):
        """Create a subclass that will add setUp instructions."""
        vcr_instance = self.vcr

        class VCRTestCase(testcase):
            vcr = vcr_instance

            def setUp(self):
                cm = self.vcr.use_cassette('.'.join([
                    # testcase.__module__.rpartition('.')[2],
                    testcase.__name__, self._testMethodName, 'yaml']))
                self.cassette = cm.__enter__()
                self.addCleanup(cm.__exit__, None, None, None)
                super(VCRTestCase, self).setUp()

        return update_wrapper(
            VCRTestCase, testcase,
            assigned=('__module__', '__name__'), updated=[])
