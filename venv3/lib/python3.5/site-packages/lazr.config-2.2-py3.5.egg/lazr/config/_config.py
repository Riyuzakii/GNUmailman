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

"""Implementation classes for config."""

from __future__ import absolute_import, print_function, unicode_literals

__metaclass__ = type
__all__ = [
    'Config',
    'ConfigData',
    'ConfigSchema',
    'ImplicitTypeSchema',
    'ImplicitTypeSection',
    'Section',
    'SectionSchema',
    'as_boolean',
    'as_host_port',
    'as_log_level',
    'as_timedelta',
    'as_username_groupname',
    ]


import datetime
import grp
import logging
import os
import pwd
import re
import sys

from os.path import abspath, basename, dirname
from textwrap import dedent

try:
    from io import StringIO
    from configparser import NoSectionError, RawConfigParser
except ImportError:
    # Python 2.
    from StringIO import StringIO
    from ConfigParser import NoSectionError, RawConfigParser


from zope.interface import implementer

from lazr.config.interfaces import (
    ConfigErrors, ICategory, IConfigData, IConfigLoader, IConfigSchema,
    InvalidSectionNameError, ISection, ISectionSchema, IStackableConfig,
    NoCategoryError, NoConfigError, RedefinedSectionError, UnknownKeyError,
    UnknownSectionError)
from lazr.delegates import delegate_to

_missing = object()


def read_content(filename):
    """Return the content of a file at filename as a string."""
    with open(filename, 'rt') as fp:
        return fp.read()


@implementer(ISectionSchema)
class SectionSchema:
    """See `ISectionSchema`."""

    def __init__(self, name, options, is_optional=False, is_master=False):
        """Create an `ISectionSchema` from the name and options.

        :param name: A string. The name of the ISectionSchema.
        :param options: A dict of the key-value pairs in the ISectionSchema.
        :param is_optional: A boolean. Is this section schema optional?
        :raise `RedefinedKeyError`: if a keys is redefined in SectionSchema.
        """
        # This method should raise RedefinedKeyError if the schema file
        # redefines a key, but SafeConfigParser swallows redefined keys.
        self.name = name
        self._options = options
        self.optional = is_optional
        self.master = is_master

    def __iter__(self):
        """See `ISectionSchema`"""
        for key in self._options.keys():
            yield key

    def __contains__(self, name):
        """See `ISectionSchema`"""
        return name in self._options

    def __getitem__(self, key):
        """See `ISectionSchema`"""
        return self._options[key]

    @property
    def category_and_section_names(self):
        """See `ISectionSchema`."""
        if '.' in self.name:
            return tuple(self.name.split('.'))
        else:
            return (None, self.name)

    def clone(self):
        """Return a copy of this section schema."""
        return self.__class__(self.name, self._options.copy(),
                              self.optional, self.master)


@delegate_to(ISectionSchema, context='schema')
@implementer(ISection)
class Section:
    """See `ISection`."""

    def __init__(self, schema, _options=None):
        """Create an `ISection` from schema.

        :param schema: The ISectionSchema that defines this ISection.
        """
        # Use __dict__ because __getattr__ limits access to self.options.
        self.__dict__['schema'] = schema
        if _options is None:
            _options = dict((key, schema[key]) for key in schema)
        self.__dict__['_options'] = _options

    def __getitem__(self, key):
        """See `ISection`"""
        return self._options[key]

    def __getattr__(self, name):
        """See `ISection`."""
        if name in self._options:
            return self._options[name]
        else:
            raise AttributeError(
                "No section key named %s." % name)

    def __setattr__(self, name, value):
        """Callsites cannot mutate the config by direct manipulation."""
        raise AttributeError("Config options cannot be set directly.")

    @property
    def category_and_section_names(self):
        """See `ISection`."""
        return self.schema.category_and_section_names

    def update(self, items):
        """Update the keys with new values.

        :return: A list of `UnknownKeyError`s if the section does not have
            the key. An empty list is returned if there are no errors.
        """
        errors = []
        for key, value in items:
            if key in self._options:
                self._options[key] = value
            else:
                msg = "%s does not have a %s key." % (self.name, key)
                errors.append(UnknownKeyError(msg))
        return errors

    def clone(self):
        """Return a copy of this section.

        The extension mechanism requires a copy of a section to prevent
        mutation.
        """
        return self.__class__(self.schema, self._options.copy())


class ImplicitTypeSection(Section):
    """See `ISection`.

    ImplicitTypeSection supports implicit conversion of key values to
    simple datatypes. It accepts the same section data as Section; the
    datatype information is not embedded in the schema or the config file.
    """
    re_types = re.compile(r'''
        (?P<false> ^false$) |
        (?P<true> ^true$) |
        (?P<none> ^none$) |
        (?P<int> ^[+-]?\d+$) |
        (?P<str> ^.*)
        ''', re.IGNORECASE | re.VERBOSE)

    def _convert(self, value):
        """Return the value as the datatype the str appears to be.

        Conversion rules:
        * bool: a single word, 'true' or 'false', case insensitive.
        * int: a single word that is a number. Signed is supported,
            hex and octal numbers are not.
        * str: anything else.
        """
        match = self.re_types.match(value)
        if match.group('false'):
            return False
        elif match.group('true'):
            return True
        elif match.group('none'):
            return None
        elif match.group('int'):
            return int(value)
        else:
            # match.group('str'); just return the sripped value.
            return value.strip()

    def __getitem__(self, key):
        """See `ISection`."""
        value = super(ImplicitTypeSection, self).__getitem__(key)
        return self._convert(value)

    def __getattr__(self, name):
        """See `ISection`."""
        value = super(ImplicitTypeSection, self).__getattr__(name)
        return self._convert(value)


@implementer(IConfigSchema, IConfigLoader)
class ConfigSchema:
    """See `IConfigSchema`."""

    _section_factory = Section

    def __init__(self, filename, file_object=None):
        """Load a configuration schema from the provided filename.

        :param filename: The name of the file to load from, or if
            `file_object` is given, to pretend to load from.
        :type filename: string
        :param file_object: If given, optional file-like object to read from
            instead of actually opening the named file.
        :type file_object: An object with a readline() method.
        :raise `UnicodeDecodeError`: if the string contains non-ascii
            characters.
        :raise `RedefinedSectionError`: if a SectionSchema name is redefined.
        :raise `InvalidSectionNameError`: if a SectionSchema name is
            ill-formed.
        """
        # XXX sinzui 2007-12-13:
        # RawConfigParser permits redefinition and non-ascii characters.
        # The raw schema data is examined before creating a config.
        self.filename = filename
        self.name = basename(filename)
        self._section_schemas = {}
        self._category_names = []
        if file_object is None:
            raw_schema = self._getRawSchema(filename)
        else:
            raw_schema = file_object
        parser = RawConfigParser()
        parser.readfp(raw_schema, filename)
        self._setSectionSchemasAndCategoryNames(parser)

    def _getRawSchema(self, filename):
        """Return the contents of the schema at filename as a StringIO.

        This method verifies that the file is ascii encoded and that no
        section name is redefined.
        """
        raw_schema = read_content(filename)
        # Verify that the string is ascii.
        raw_schema.encode('ascii', 'strict')
        # Verify that no sections are redefined.
        section_names = []
        for section_name in re.findall(r'^\s*\[[^\]]+\]', raw_schema, re.M):
            if section_name in section_names:
                raise RedefinedSectionError(section_name)
            else:
                section_names.append(section_name)
        return StringIO(raw_schema)

    def _setSectionSchemasAndCategoryNames(self, parser):
        """Set the SectionSchemas and category_names from the config."""
        category_names = set()
        templates = {}
        # Retrieve all the templates first because section() does not follow
        # the order of the conf file.
        for name in parser.sections():
            (section_name, category_name,
             is_template, is_optional,
             is_master) = self._parseSectionName(name)
            if is_template or is_master:
                templates[category_name] = dict(parser.items(name))
        for name in parser.sections():
            (section_name, category_name,
             is_template, is_optional,
             is_master) = self._parseSectionName(name)
            if is_template:
                continue
            options = dict(templates.get(category_name, {}))
            options.update(parser.items(name))
            self._section_schemas[section_name] = SectionSchema(
                section_name, options, is_optional, is_master)
            if category_name is not None:
                category_names.add(category_name)
        self._category_names = sorted(category_names)

    _section_name_pattern = re.compile(r'\w[\w.-]+\w')

    def _parseSectionName(self, name):
        """Return a tuple of names and kinds embedded in the name.

        :return: (section_name, category_name, is_template, is_optional).
            section_name is always a string. category_name is a string or
            None if there is no prefix. is_template and is_optional
            are False by default, but will be true if the name's suffix
            ends in '.template' or '.optional'.
        """
        name_parts = name.split('.')
        is_template = name_parts[-1] == 'template'
        is_optional = name_parts[-1] == 'optional'
        is_master = name_parts[-1] == 'master'
        if is_template or is_optional:
            # The suffix is not a part of the section name.
            # Example: [name.optional] or [category.template]
            del name_parts[-1]
        count = len(name_parts)
        if count == 1 and is_template:
            # Example: [category.template]
            category_name = name_parts[0]
            section_name = name_parts[0]
        elif count == 1:
            # Example: [name]
            category_name = None
            section_name = name_parts[0]
        elif count == 2:
            # Example: [category.name]
            category_name = name_parts[0]
            section_name = '.'.join(name_parts)
        else:
            raise InvalidSectionNameError('[%s] has too many parts.' % name)
        if self._section_name_pattern.match(section_name) is None:
            raise InvalidSectionNameError(
                '[%s] name does not match [\w.-]+.' % name)
        return (section_name, category_name,
                is_template, is_optional, is_master)

    @property
    def section_factory(self):
        """See `IConfigSchema`."""
        return self._section_factory

    @property
    def category_names(self):
        """See `IConfigSchema`."""
        return self._category_names

    def __iter__(self):
        """See `IConfigSchema`."""
        for value in self._section_schemas.values():
            yield value

    def __contains__(self, name):
        """See `IConfigSchema`."""
        return name in self._section_schemas.keys()

    def __getitem__(self, name):
        """See `IConfigSchema`."""
        try:
            return self._section_schemas[name]
        except KeyError:
            raise NoSectionError(name)

    def getByCategory(self, name, default=_missing):
        """See `IConfigSchema`."""
        if name not in self.category_names:
            if default is _missing:
                raise NoCategoryError(name)
            return default
        section_schemas = []
        for key in self._section_schemas:
            section = self._section_schemas[key]
            category, dummy = section.category_and_section_names
            if name == category:
                section_schemas.append(section)
        return section_schemas

    def _getRequiredSections(self):
        """return a dict of `Section`s from the required `SectionSchemas`."""
        sections = {}
        for section_schema in self:
            if not section_schema.optional:
                sections[section_schema.name] = self.section_factory(
                    section_schema)
        return sections

    def load(self, filename):
        """See `IConfigLoader`."""
        conf_data = read_content(filename)
        return self._load(filename, conf_data)

    def loadFile(self, source_file, filename=None):
        """See `IConfigLoader`."""
        conf_data = source_file.read()
        if filename is None:
            filename = getattr(source_file, 'name')
            assert filename is not None, (
                'filename must be provided if the file-like object '
                'does not have a name attribute.')
        return self._load(filename, conf_data)

    def _load(self, filename, conf_data):
        """Return a Config parsed from conf_data."""
        config = Config(self)
        config.push(filename, conf_data)
        return config


class ImplicitTypeSchema(ConfigSchema):
    """See `IConfigSchema`.

    ImplicitTypeSchema creates a config that supports implicit datatyping
    of section key values.
    """

    _section_factory = ImplicitTypeSection


@implementer(IConfigData)
class ConfigData:
    """See `IConfigData`."""

    def __init__(self, filename, sections, extends=None, errors=None):
        """Set the configuration data."""
        self.filename = filename
        self.name = basename(filename)
        self._sections = sections
        self._category_names = self._getCategoryNames()
        self._extends = extends
        if errors is None:
            self._errors = []
        else:
            self._errors = errors

    def _getCategoryNames(self):
        """Return a tuple of category names that the `Section`s belong to."""
        category_names = set()
        for section_name in self._sections:
            section = self._sections[section_name]
            category, dummy = section.category_and_section_names
            if category is not None:
                category_names.add(category)
        return tuple(category_names)

    @property
    def category_names(self):
        """See `IConfigData`."""
        return self._category_names

    def __iter__(self):
        """See `IConfigData`."""
        for value in self._sections.values():
            yield value

    def __contains__(self, name):
        """See `IConfigData`."""
        return name in self._sections.keys()

    def __getitem__(self, name):
        """See `IConfigData`."""
        try:
            return self._sections[name]
        except KeyError:
            raise NoSectionError(name)

    def getByCategory(self, name, default=_missing):
        """See `IConfigData`."""
        if name not in self.category_names:
            if default is _missing:
                raise NoCategoryError(name)
            return default
        sections = []
        for key in self._sections:
            section = self._sections[key]
            category, dummy = section.category_and_section_names
            if name == category:
                sections.append(section)
        return sections


@delegate_to(IConfigData, context='data')
@implementer(IStackableConfig)
class Config:
    """See `IStackableConfig`."""
    # LAZR config classes may access ConfigData private data.
    # pylint: disable-msg=W0212

    def __init__(self, schema):
        """Set the schema and configuration."""
        self._overlays = (
            ConfigData(schema.filename, schema._getRequiredSections()), )
        self.schema = schema

    def __getattr__(self, name):
        """See `IStackableConfig`."""
        if name in self.data._sections:
            return self.data._sections[name]
        elif name in self.data._category_names:
            return Category(name, self.data.getByCategory(name))
        raise AttributeError("No section or category named %s." % name)

    @property
    def data(self):
        """See `IStackableConfig`."""
        return self.overlays[0]

    @property
    def extends(self):
        """See `IStackableConfig`."""
        if len(self.overlays) == 1:
            # The ConfigData made from the schema defaults extends nothing.
            return None
        else:
            return self.overlays[1]

    @property
    def overlays(self):
        """See `IStackableConfig`."""
        return self._overlays

    def validate(self):
        """See `IConfigData`."""
        if len(self.data._errors) > 0:
            message = "%s is not valid." % self.name
            raise ConfigErrors(message, errors=self.data._errors)
        return True

    def push(self, conf_name, conf_data):
        """See `IStackableConfig`.

        Create a new ConfigData object from the raw conf_data, and
        place it on top of the overlay stack. If the conf_data extends
        another conf, a ConfigData object will be created for that first.
        """
        conf_data = dedent(conf_data)
        confs = self._getExtendedConfs(conf_name, conf_data)
        confs.reverse()
        for conf_name, parser, encoding_errors in confs:
            if self.data.filename == self.schema.filename == conf_name:
                # Do not parse the schema file twice in a row.
                continue
            config_data = self._createConfigData(
                conf_name, parser, encoding_errors)
            self._overlays = (config_data, ) + self._overlays

    def _getExtendedConfs(self, conf_filename, conf_data, confs=None):
        """Return a list of tuple (conf_name, parser, encoding_errors).

        :param conf_filename: The path and name of the conf file.
        :param conf_data: Unparsed config data.
        :param confs: A list of confs that extend filename.
        :return: A list of confs ordered from extender to extendee.
        :raises IOError: If filename cannot be read.

        This method parses the config data and checks for encoding errors.
        It checks parsed config data for the extends key in the meta section.
        It reads the unparsed config_data from the extended filename.
        It passes filename, data, and the working list to itself.
        """
        if confs is None:
            confs = []
        encoding_errors = self._verifyEncoding(conf_data)
        # LP: #1397779.  In Python 3, RawConfigParser grew a `strict` keyword
        # option and in Python 3.2, this argument changed its default from
        # False to True.  This breaks behavior compatibility with Python 2, so
        # under Python 3, always force strict=False.
        kws = {}
        if sys.version_info >= (3,):
            kws['strict'] = False
        parser = RawConfigParser(**kws)
        parser.readfp(StringIO(conf_data), conf_filename)
        confs.append((conf_filename, parser, encoding_errors))
        if parser.has_option('meta', 'extends'):
            base_path = dirname(conf_filename)
            extends_name = parser.get('meta', 'extends')
            extends_filename = abspath('%s/%s' % (base_path, extends_name))
            extends_data = read_content(extends_filename)
            self._getExtendedConfs(extends_filename, extends_data, confs)
        return confs

    def _createConfigData(self, conf_name, parser, encoding_errors):
        """Return a new ConfigData object created from a parsed conf file.

        :param conf_name: the full name of the config file, may be a filepath.
        :param parser: the parsed config file; an instance of ConfigParser.
        :param encoding_errors: a list of encoding error in the config file.
        :return: a new ConfigData object.

        This method extracts the sections, keys, and values from the parser
        to construct a new ConfigData object. The list of encoding errors are
        incorporated into the the list of data-related errors for the
        ConfigData.
        """
        sections = {}
        for section in self.data:
            sections[section.name] = section.clone()
        errors = list(self.data._errors)
        errors.extend(encoding_errors)
        extends = None
        masters = set()
        for section_name in parser.sections():
            if section_name == 'meta':
                extends, meta_errors = self._loadMetaData(parser)
                errors.extend(meta_errors)
                continue
            if (section_name.endswith('.template') or
                section_name.endswith('.optional') or
                section_name.endswith('.master')):
                # This section is a schema directive.
                continue
            # Calculate the section master name.
            # Check for sections which extend .masters.
            if '.' in section_name:
                category, section = section_name.split('.')
                master_name = category + '.master'
            else:
                master_name = None
            if (section_name not in self.schema and
                master_name not in self.schema):
                # Any section not in the the schema is an error.
                msg = "%s does not have a %s section." % (
                    self.schema.name, section_name)
                errors.append(UnknownSectionError(msg))
                continue
            if section_name not in self.data:
                # Is there a master section?
                try:
                    section_schema = self.schema[master_name]
                except NoSectionError:
                    # There's no master for this section, so just treat it
                    # like a regular category.
                    pass
                else:
                    assert section_schema.master, '.master is not a master?'
                    schema = section_schema.clone()
                    schema.name = section_name
                    section = self.schema.section_factory(schema)
                    section.update(parser.items(section_name))
                    sections[section_name] = section
                    masters.add(master_name)
                    continue
                # Create the optional section from the schema.
                section_schema = self.schema[section_name]
                sections[section_name] = self.schema.section_factory(
                    section_schema)
            # Update the section with the parser options.
            items = parser.items(section_name)
            section_errors = sections[section_name].update(items)
            errors.extend(section_errors)
        # master sections are like templates.  They show up in the schema but
        # not in the config.
        for master in masters:
            sections.pop(master, None)
        return ConfigData(conf_name, sections, extends, errors)

    def _verifyEncoding(self, config_data):
        """Verify that the data is ASCII encoded.

        :return: a list of UnicodeDecodeError errors. If there are no
            errors, return an empty list.
        """
        errors = []
        try:
            if isinstance(config_data, bytes):
                config_data.decode('ascii', 'strict')
            else:
                config_data.encode('ascii', 'strict')
        except UnicodeError as error:
            errors.append(error)
        return errors

    def _loadMetaData(self, parser):
        """Load the config meta data from the ConfigParser.

        The meta section is reserved for the LAZR config parser.

        :return: a list of errors if there are errors, or an empty list.
        """
        extends = None
        errors = []
        for key in parser.options('meta'):
            if key == "extends":
                extends = parser.get('meta', 'extends')
            else:
                # Any other key is an error.
                msg = "The meta section does not have a %s key." % key
                errors.append(UnknownKeyError(msg))
        return (extends, errors)

    def pop(self, conf_name):
        """See `IStackableConfig`."""
        index = self._getIndexOfOverlay(conf_name)
        removed_overlays = self.overlays[:index]
        self._overlays = self.overlays[index:]
        return removed_overlays

    def _getIndexOfOverlay(self, conf_name):
        """Return the index of the config named conf_name.

        The bottom of the stack cannot never be returned because it was
        made from the schema.
        """
        schema_index = len(self.overlays) - 1
        for index, config_data in enumerate(self.overlays):
            if index == schema_index and config_data.name == conf_name:
                raise NoConfigError("Cannot pop the schema's default config.")
            if config_data.name == conf_name:
                return index + 1
        # The config data was not found in the overlays.
        raise NoConfigError('No config with name: %s.' % conf_name)


@implementer(ICategory)
class Category:
    """See `ICategory`."""

    def __init__(self, name, sections):
        """Initialize the Category its name and a list of sections."""
        self.name = name
        self._sections = {}
        for section in sections:
            self._sections[section.name] = section

    def __getattr__(self, name):
        """See `ICategory`."""
        full_name = "%s.%s" % (self.name, name)
        if full_name in self._sections:
            return self._sections[full_name]
        raise AttributeError("No section named %s." % name)


def as_boolean(value):
    """Turn a string into a boolean.

    :param value: A string with one of the following values
        (case-insensitive): true, yes, 1, on, enable, enabled (for True), or
        false, no, 0, off, disable, disabled (for False).  Everything else is
        an error.
    :type value: string
    :return: True or False.
    :rtype: boolean
    """
    value = value.lower()
    if value in ('true', 'yes', '1', 'on', 'enabled', 'enable'):
        return True
    if value in ('false', 'no', '0', 'off', 'disabled', 'disable'):
        return False
    raise ValueError('Invalid boolean value: %s' % value)


def as_host_port(value, default_host='localhost', default_port=25):
    """Return a 2-tuple of (host, port) from a value like 'host:port'.

    :param value: The configuration value.
    :type value: string
    :param default_host: Optional host name to use if the configuration value
        is missing the host name.
    :type default_host: string
    :param default_port: Optional port number to use if the configuration
        value is missing the port number.
    :type default_port: integer
    :return: a 2-tuple of the form (host, port)
    :rtype: 2-tuple of (string, integer)
    """
    if ':' in value:
        host, port = value.split(':')
        if host == '':
            host = default_host
        port = int(port)
    else:
        host = value
        port = default_port
    return host, port


def as_username_groupname(value=None):
    """Turn a string of the form user:group into the user and group names.

    :param value: The configuration value.
    :type value: a string containing exactly one colon, or None
    :return: a 2-tuple of (username, groupname).  If `value` was None, then
        the current user and group names are returned.
    :rtype: 2-tuple of type (string, string)
    """
    if value:
        user, group = value.split(':', 1)
    else:
        user  = pwd.getpwuid(os.getuid()).pw_name
        group = grp.getgrgid(os.getgid()).gr_name
    return user, group


def _sortkey(item):
    """Return a value that sorted(..., key=_sortkey) can use."""
    order = dict(
        w=0,    # weeks
        d=1,    # days
        h=2,    # hours
        m=3,    # minutes
        s=4,    # seconds
        )
    return order.get(item[-1])

def as_timedelta(value):
    """Convert a value string to the equivalent timedeta."""
    # Technically, the regex will match multiple decimal points in the
    # left-hand side, but that's okay because the float/int conversion below
    # will properly complain if there's more than one dot.
    components = sorted(re.findall(r'([\d.]+[smhdw])', value), key=_sortkey)
    # Complain if the components are out of order.
    if ''.join(components) != value:
        raise ValueError
    keywords = dict((interval[0].lower(), interval)
                    for interval in ('weeks', 'days', 'hours',
                                     'minutes', 'seconds'))
    keyword_arguments = {}
    for interval in components:
        if len(interval) == 0:
            raise ValueError
        keyword = keywords.get(interval[-1].lower())
        if keyword is None:
            raise ValueError
        if keyword in keyword_arguments:
            raise ValueError
        if '.' in interval[:-1]:
            converted = float(interval[:-1])
        else:
            converted = int(interval[:-1])
        keyword_arguments[keyword] = converted
    if len(keyword_arguments) == 0:
        raise ValueError
    return datetime.timedelta(**keyword_arguments)

def as_log_level(value):
    """Turn a string into a log level.

    :param value: A string with a value (case-insensitive) equal to one of the
        symbolic logging levels.
    :type value: string
    :return: A logging level constant.
    :rtype: int
    """
    value = value.upper()
    return getattr(logging, value)
