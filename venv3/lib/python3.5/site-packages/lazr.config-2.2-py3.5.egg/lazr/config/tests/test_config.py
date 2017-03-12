# Copyright 2008-2015 Canonical Ltd.  All rights reserved.
#
# This file is part of lazr.config.
#
# lazr.config is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# lazr.config is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public
# License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with lazr.config.  If not, see <http://www.gnu.org/licenses/>.

"""Tests of lazr.config."""

from __future__ import absolute_import, print_function, unicode_literals

__metaclass__ = type
__all__ = [
    'TestConfig',
    ]


import unittest
import pkg_resources
try:
    from configparser import MissingSectionHeaderError, NoSectionError
except ImportError:
    # Python 2
    from ConfigParser import MissingSectionHeaderError, NoSectionError
try:
    from io import StringIO
except ImportError:
    # Python 2
    from StringIO import StringIO

from operator import attrgetter
from zope.interface.exceptions import DoesNotImplement
from zope.interface.verify import verifyObject

from lazr.config import ConfigSchema, ImplicitTypeSchema
from lazr.config.interfaces import (
    ConfigErrors, IStackableConfig, InvalidSectionNameError, NoCategoryError,
    NoConfigError, RedefinedSectionError, UnknownKeyError,
    UnknownSectionError)


class TestConfig(unittest.TestCase):
    def setUp(self):
        # Python 2.6 does not have assertMultilineEqual
        self.meq = getattr(self, 'assertMultiLineEqual', self.assertEqual)

    def _testfile(self, conf_file):
        return pkg_resources.resource_filename(
            'lazr.config.tests.testdata', conf_file)

    def test_missing_category(self):
        schema = ConfigSchema(self._testfile('base.conf'))
        self.assertRaises(NoCategoryError, schema.getByCategory, 'non-section')

    def test_missing_file(self):
        self.assertRaises(IOError, ConfigSchema, '/does/not/exist')

    def test_must_be_ascii(self):
        self.assertRaises(UnicodeError,
                          ConfigSchema, self._testfile('bad-nonascii.conf'))

    def test_missing_schema_section(self):
        schema = ConfigSchema(self._testfile('base.conf'))
        self.assertRaises(NoSectionError, schema.__getitem__, 'section-4')

    def test_missing_header_section(self):
        self.assertRaises(MissingSectionHeaderError,
                          ConfigSchema, self._testfile('bad-sectionless.conf'))

    def test_redefined_section(self):
        self.assertRaises(RedefinedSectionError,
                          ConfigSchema,
                          self._testfile('bad-redefined-section.conf'))
        # XXX sinzui 2007-12-13:
        # ConfigSchema should raise RedefinedKeyError when a section redefines
        # a key.

    def test_invalid_section_name(self):
        self.assertRaises(InvalidSectionNameError,
                          ConfigSchema,
                          self._testfile('bad-invalid-name.conf'))

    def test_invalid_characters(self):
        self.assertRaises(InvalidSectionNameError,
                          ConfigSchema,
                          self._testfile('bad-invalid-name-chars.conf'))

    def test_load_missing_file(self):
        schema = ConfigSchema(self._testfile('base.conf'))
        self.assertRaises(IOError, schema.load, '/no/such/file.conf')

    def test_no_name_argument(self):
        config = """
[meta]
metakey: unsupported
[unknown-section]
key1 = value1
[section_1]
keyn: unknown key
key1: bad character in caf\xc3)
[section_3.template]
key1: schema suffixes are not permitted
"""
        schema = ConfigSchema(self._testfile('base.conf'))
        self.assertRaises(AttributeError, schema.loadFile, StringIO(config))

    def test_missing_section(self):
        schema = ConfigSchema(self._testfile('base.conf'))
        config = schema.load(self._testfile('local.conf'))
        self.assertRaises(NoSectionError, config.__getitem__, 'section-4')

    def test_undeclared_optional_section(self):
        schema = ConfigSchema(self._testfile('base.conf'))
        config = schema.load(self._testfile('local.conf'))
        self.assertRaises(NoSectionError,
                          config.__getitem__, 'section_3.app_a')

    def test_nonexistent_category_name(self):
        schema = ConfigSchema(self._testfile('base.conf'))
        config = schema.load(self._testfile('local.conf'))
        self.assertRaises(NoCategoryError,
                          config.getByCategory, 'non-section')

    def test_all_config_errors(self):
        schema = ConfigSchema(self._testfile('base.conf'))
        config = schema.loadFile(StringIO("""
[meta]
metakey: unsupported
[unknown-section]
key1 = value1
[section_1]
keyn: unknown key
key1: bad character in caf\xc3)
[section_3.template]
key1: schema suffixes are not permitted
"""), 'bad config')
        try:
            config.validate()
        except ConfigErrors as errors:
            sorted_errors = sorted(
                errors.errors, key=attrgetter('__class__.__name__'))
            self.assertEqual(str(errors),
                             'ConfigErrors: bad config is not valid.')
        else:
            self.fail('ConfigErrors expected')
        self.assertEqual(len(sorted_errors), 4)
        self.assertEqual([error.__class__ for error in sorted_errors],
                         [UnicodeEncodeError, UnknownKeyError,
                          UnknownKeyError, UnknownSectionError])

    def test_not_stackable(self):
        schema = ConfigSchema(self._testfile('base.conf'))
        config = schema.load(self._testfile('local.conf'))
        self.assertRaises(DoesNotImplement,
                          verifyObject, IStackableConfig, config.extends)

    def test_bad_pop(self):
        schema = ConfigSchema(self._testfile('base.conf'))
        config = schema.load(self._testfile('local.conf'))
        config.push('one', '')
        config.push('two', '')
        self.assertRaises(NoConfigError, config.pop, 'bad-name')

    def test_cannot_pop_bottom(self):
        schema = ConfigSchema(self._testfile('base.conf'))
        config = schema.load(self._testfile('local.conf'))
        config.pop('local.conf')
        self.assertRaises(NoConfigError, config.pop, 'base.conf')

    def test_multiline_preserves_indentation(self):
        schema = ImplicitTypeSchema(self._testfile('base.conf'))
        config = schema.load(self._testfile('local.conf'))
        convert = config['section_1']._convert
        orig = """\
multiline value 1
    multiline value 2"""
        new = convert(orig)
        self.meq(new, orig)

    def test_multiline_strips_leading_and_trailing_whitespace(self):
        schema = ImplicitTypeSchema(self._testfile('base.conf'))
        config = schema.load(self._testfile('local.conf'))
        convert = config['section_1']._convert
        orig = """
    multiline value 1
    multiline value 2
    """
        new = convert(orig)
        self.meq(new, orig.strip())

    def test_multiline_key(self):
        schema = ImplicitTypeSchema(self._testfile('base.conf'))
        config = schema.load(self._testfile('local.conf'))
        self.meq(config['section_33'].key2, """\
multiline value 1
multiline value 2""")

    def test_lp1397779(self):
        # Fix DuplicateSectionErrors when you .push() a config that has a
        # section already defined in the config.
        schema = ConfigSchema(self._testfile('base.conf'))
        config = schema.load(self._testfile('local.conf'))
        self.assertEqual(config['section_1']['key1'], 'foo')
        config.push('dupsec', """\
[section_1]
key1: baz
[section_1]
key1: qux
""")
        self.assertEqual(config['section_1']['key1'], 'qux')
