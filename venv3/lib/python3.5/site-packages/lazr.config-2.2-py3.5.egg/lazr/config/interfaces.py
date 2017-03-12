# Copyright 2007-2015 Canonical Ltd.  All rights reserved.
#
# This file is part of lazr.config
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

# pylint: disable-msg=E0211,E0213,W0231
"""Interfaces for process configuration.."""

from __future__ import absolute_import, print_function, unicode_literals

__metaclass__ = type
__all__ = [
    'ConfigErrors',
    'ConfigSchemaError',
    'IConfigData',
    'NoConfigError',
    'ICategory',
    'IConfigLoader',
    'IConfigSchema',
    'InvalidSectionNameError',
    'ISection',
    'ISectionSchema',
    'IStackableConfig',
    'NoCategoryError',
    'RedefinedKeyError',
    'RedefinedSectionError',
    'UnknownKeyError',
    'UnknownSectionError']

from zope.interface import Interface, Attribute


class ConfigSchemaError(Exception):
    """A base class of all `IConfigSchema` errors."""


class RedefinedKeyError(ConfigSchemaError):
    """A key in a section cannot be redefined."""


class RedefinedSectionError(ConfigSchemaError):
    """A section in a config file cannot be redefined."""


class InvalidSectionNameError(ConfigSchemaError):
    """The section name contains more than one category."""


class NoCategoryError(LookupError):
    """No `ISectionSchema`s belong to the category name."""


class UnknownSectionError(ConfigSchemaError):
    """The config has a section that is not in the schema."""


class UnknownKeyError(ConfigSchemaError):
    """The section has a key that is not in the schema."""

class NoConfigError(ConfigSchemaError):
    """No config has the name."""

class ConfigErrors(ConfigSchemaError):
    """The errors in a Config.

    The list of errors can be accessed via the errors attribute.
    """

    def __init__(self, message, errors=None):
        """Initialize the error with a message and errors.

        :param message: a message string
        :param errors: a list of errors in the config, or None
        """
        # Without the suppression above, this produces a warning in Python 2.6.
        self.message = message
        self.errors = errors

    def __str__(self):
        return '%s: %s' % (self.__class__.__name__, self.message)


class ISectionSchema(Interface):
    """Defines the valid keys and default values for a configuration group."""
    name = Attribute("The section name.")
    optional = Attribute("Is the section optional in the config?")
    category_and_section_names = Attribute(
        "A 2-Tuple of the category and specific name parts.")

    def __iter__():
        """Iterate over the keys."""

    def __contains__(name):
        """Return True or False if name is a key."""

    def __getitem__(key):
        """Return the default value of the key.

        :raise `KeyError`: if the key does not exist.
        """


class ISection(ISectionSchema):
    """Defines the values for a configuration group."""
    schema = Attribute("The ISectionSchema that defines this ISection.")

    def __getattr__(name):
        """Return the named key.

        :name: a key name.
        :return: the value of the matching key.
        :raise: AttributeError if there is no key with the name.
        """

class IConfigLoader(Interface):
    """A configuration file loader."""

    def load(filename):
        """Load a configuration from the file at filename."""

    def loadFile(source_file, filename=None):
        """Load a configuration from the open source_file.

        :param source_file: A file-like object that supports read() and
            readline()
        :param filename: The name of the configuration. If filename is None,
            The name will be taken from source_file.name.
        """


class IConfigSchema(Interface):
    """A process configuration schema.

    The config file contains sections enclosed in square brackets ([]).
    The section name may be divided into major and minor categories using a
    dot (.). Beneath each section is a list of key-value pairs, separated
    by a colon (:).

    Multiple sections with the same major category may have their keys defined
    in another section that appends the '.template' or '.master' suffixes to
    the category name. A section with '.optional' suffix is not
    required. Lines that start with a hash (#) are comments.
    """
    name = Attribute('The basename of the config filename.')
    filename = Attribute('The path to config file')
    category_names = Attribute('The list of section category names.')

    def __iter__():
        """Iterate over the `ISectionSchema`s."""

    def __contains__(name):
        """Return True or False if the name matches a `ISectionSchema`."""

    def __getitem__(name):
        """Return the `ISectionSchema` with the matching name.

        :raise `NoSectionError`: if the no ISectionSchema has the name.
        """

    def getByCategory(name):
        """Return a list of ISectionSchemas that belong to the category name.

        `ISectionSchema` names may be made from a category name and a group
        name, separated by a dot (.). The category is synonymous with a
        arbitrary resource such as a database or a vhost. Thus database.bugs
        and database.answers are two sections that both use the database
        resource.

        :raise `CategoryNotFound`: if no sections have a name that starts
            with the category name.
        """


class IConfigData(IConfigSchema):
    """A process configuration.

    See `IConfigSchema` for more information about the config file format.
    """


class IStackableConfig(IConfigSchema):
    """A configuration that is built from configs that extend each other.

    A config may extend another config so that a configuration for a
    process need only define the localized sections and keys. The
    configuration is constructed from a stack of data that defines,
    and redefines, the sections and keys in the configuration. Each config
    overlays its data to define the final configuration.

    A config file declares that is extends another using the 'extends' key
    in the 'meta' section of the config data file:
        [meta]
        extends: common.conf

    The push() and pop() methods can be used to test processes where the
    test environment must be configured differently.
    """
    schema = Attribute("The schema that defines the config.")
    data = Attribute("The current ConfigData. use by the config.")
    extends = Attribute("The ConfigData that this config extends.")
    overlays = Attribute("The stack of ConfigData that define this config.")


    def __getattr__(name):
        """Return the named section.

        :name: a section or category name.
        :return: the matching `ISection` or `ICategory`.
        :raise: AttributeError if there is no section or category with the
            name.
        """

    def validate():
        """Return True if the config is valid for the schema.

        :raise `ConfigErrors`: if the are errors. A list of all schema
            problems can be retrieved via the errors property.
        """

    def push(conf_name, conf_data):
        """Overlay the config with unparsed config data.

        :param conf_name: the name of the config.
        :param conf_data: a string of unparsed config data.

        This method appends the parsed `IConfigData` to the overlays property.
        """

    def pop(conf_name):
        """Remove conf_name from the overlays stack.

        :param conf_name: the name of the `IConfigData` to remove.
        :return: the tuple of `IConfigData` that was removed from overlays.
        :raise NoConfigError: if no `IConfigData` has the conf_name.

        This method removes the named ConfigData from the stack; ConfigData
        above the named ConfigData are removed too.
        """


class ICategory(Interface):
    """A group of related sections.

    The sections within a category are access as attributes of the
    `ICategory`.
    """

    def __getattr__(name):
        """Return the named section.

        :name: a section name.
        :return: the matching `ISection`.
        :raise: AttributeError if there is no section with the name.
        """
