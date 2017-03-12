# Copyright (C) 2013-2017 The Free Software Foundation, Inc.
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

"""nose2 test infrastructure."""

import os
import re
import errno
import doctest
import mailmanclient

from contextlib2 import ExitStack
from mailmanclient.testing.documentation import setup, teardown
from nose2.events import Plugin
from .vcr_helpers import get_vcr


__all__ = [
    'NosePlugin',
    ]


DOT = '.'
FLAGS = doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE | doctest.REPORT_NDIFF
TOPDIR = os.path.dirname(mailmanclient.__file__)


class NosePlugin(Plugin):
    configSection = 'mailman'

    def __init__(self):
        super(NosePlugin, self).__init__()
        self.patterns = []
        self.stderr = False
        self.record = False

        def set_stderr(ignore):
            self.stderr = True
        self.addArgument(self.patterns, 'P', 'pattern',
                         'Add a test matching pattern')
        self.addFlag(set_stderr, 'E', 'stderr',
                     'Enable stderr logging to sub-runners')

        def set_record(ignore):
            self.record = True
        self.addFlag(set_record, 'R', 'rerecord',
                     """Force re-recording of test responses.  Requires
                     Mailman to be running.""")
        self._data_path = os.path.join(TOPDIR, 'tests', 'data', 'tape.yaml')
        self._resources = ExitStack()
        self._recorder = get_vcr()

    def startTestRun(self, event):
        # Check to see if we're running the test suite in record mode.  If so,
        # delete any existing recording.
        if self.record:
            try:
                os.remove(self._data_path)
            except OSError as error:
                if error.errno != errno.ENOENT:
                    raise
        # This will automatically create the recording file.
        self._resources.enter_context(
            self._recorder.use_cassette(self._data_path))

    def stopTestRun(self, event):
        # Stop all recording.
        self._resources.close()

    def getTestCaseNames(self, event):
        if len(self.patterns) == 0:
            # No filter patterns, so everything should be tested.
            return
        # Does the pattern match the fully qualified class name?
        for pattern in self.patterns:
            full_class_name = '{}.{}'.format(
                event.testCase.__module__, event.testCase.__name__)
            if re.search(pattern, full_class_name):
                # Don't suppress this test class.
                return
        names = filter(event.isTestMethod, dir(event.testCase))
        for name in names:
            full_test_name = '{}.{}.{}'.format(
                event.testCase.__module__,
                event.testCase.__name__,
                name)
            for pattern in self.patterns:
                if re.search(pattern, full_test_name):
                    break
            else:
                event.excludedNames.append(name)

    def handleFile(self, event):
        path = event.path[len(TOPDIR)+1:]
        if len(self.patterns) > 0:
            for pattern in self.patterns:
                if re.search(pattern, path):
                    break
            else:
                # Skip this doctest.
                return
        base, ext = os.path.splitext(path)
        if ext != '.rst':
            return
        test = doctest.DocFileTest(
            path, package=mailmanclient,
            optionflags=FLAGS,
            setUp=setup,
            tearDown=teardown)
        # Suppress the extra "Doctest: ..." line.
        test.shortDescription = lambda: None
        event.extraTests.append(test)

    # def startTest(self, event):
    #     import sys; print('vvvvv', event.test, file=sys.stderr)

    # def stopTest(self, event):
    #     import sys; print('^^^^^', event.test, file=sys.stderr)
