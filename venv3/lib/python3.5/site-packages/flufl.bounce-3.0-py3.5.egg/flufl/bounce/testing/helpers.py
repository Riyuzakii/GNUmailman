import os
import email
import doctest
import logging

from contextlib import closing
from email import message_from_binary_file as parse
from importlib import import_module
from nose2.events import Plugin
from pkg_resources import resource_stream
from unittest import TestCase


DOCTEST_FLAGS = (
    doctest.ELLIPSIS |
    doctest.NORMALIZE_WHITESPACE |
    doctest.REPORT_NDIFF)


def setup(testobj):
    """Test setup."""
    testobj.globs['parse'] = email.message_from_bytes


def initialize(plugin):
    """Initialize logging for the test suite.

    Normally, an application would itself initialize the flufl.bounce logger,
    but when the test suite is run, it is the controlling application.
    Sometimes when you run the test suite, you want additional debugging, so
    you can set the logging level via an environment variable $FLUFL_LOGGING.
    This variable can be a set of semi-colon separated key-value pairs,
    themselves separated by an equal sign.  The keys and values can be
    anything accepted by `logging.basicConfig()`.
    """
    kwargs = {}
    envar = os.environ.get('FLUFL_LOGGING')
    if envar is not None:
        for key_value in envar.split(';'):
            key, equals, value = key_value.partition('=')
            kwargs[key] = value
    logging.basicConfig(**kwargs)


class Detectors(Plugin):
    configSection = 'detectors'

    class DataTest(TestCase):
        def __init__(self, data):
            super().__init__('run_test')
            if len(data) == 3:
                bounce_module, filename, expected = data
                self.is_temporary = False
            else:
                bounce_module, filename, expected, self.is_temporary = data
            self.expected = set(expected)
            self.description = '{}: [{}] detecting {} in {}'.format(
                bounce_module,
                ('T' if self.is_temporary else 'P'),
                self.expected, filename)
            module_name = 'flufl.bounce._detectors.{}'.format(bounce_module)
            module = import_module(module_name)
            with closing(resource_stream(
                    'flufl.bounce.tests.data', filename)) as fp:
                self.message = parse(fp)
            missing = object()
            for name in getattr(module, '__all__', []):
                component_class = getattr(module, name, missing)
                if component_class is missing:
                    raise RuntimeError(
                        'skipping missing __all__ entry: {}'.format(name))
                self.component = component_class()

        def run_test(self):
            # XXX 2011-07-02: We don't currently test temporary failures.
            temporary, permanent = self.component.process(self.message)
            got = (set(temporary) if self.is_temporary else set(permanent))
            self.assertEqual(got, self.expected)

    def loadTestsFromTestCase(self, event):
        if event.testCase.__name__ is not 'TestDetectors':
            return
        for data in DATA:
            event.extraTests.append(Detectors.DataTest(data))

    def describeTest(self, event):
        if event.test.__class__ is Detectors.DataTest:
            event.description = event.test.description
            event.handled = True


DATA = (
    # Postfix bounces
    ('postfix', 'postfix_01.txt', [b'xxxxx@local.ie']),
    ('postfix', 'postfix_02.txt', [b'yyyyy@digicool.com']),
    ('postfix', 'postfix_03.txt', [b'ttttt@ggggg.com']),
    ('postfix', 'postfix_04.txt', [b'userx@mail1.example.com']),
    ('postfix', 'postfix_05.txt', [b'userx@example.net']),
    # Exim bounces
    ('exim', 'exim_01.txt', [b'userx@its.example.nl']),
    # SimpleMatch bounces
    ('simplematch', 'sendmail_01.txt', [b'zzzzz@shaft.coal.nl',
                                        b'zzzzz@nfg.nl']),
    ('simplematch', 'simple_01.txt', [b'bbbsss@example.com']),
    ('simplematch', 'simple_02.txt', [b'userx@example.net']),
    ('simplematch', 'simple_04.txt', [b'userx@example.com']),
    ('simplematch', 'newmailru_01.txt', [b'zzzzz@newmail.ru']),
    ('simplematch', 'hotpop_01.txt', [b'userx@example.com']),
    ('simplematch', 'microsoft_03.txt', [b'userx@example.com']),
    ('simplematch', 'simple_05.txt', [b'userx@example.net']),
    ('simplematch', 'simple_06.txt', [b'userx@example.com']),
    ('simplematch', 'simple_07.txt', [b'userx@example.net']),
    ('simplematch', 'simple_08.txt', [b'userx@example.de']),
    ('simplematch', 'simple_09.txt', [b'userx@example.de']),
    ('simplematch', 'simple_10.txt', [b'userx@example.com']),
    ('simplematch', 'simple_11.txt', [b'userx@example.com']),
    ('simplematch', 'simple_12.txt', [b'userx@example.ac.jp']),
    ('simplematch', 'simple_13.txt', [b'userx@example.fr']),
    ('simplematch', 'simple_14.txt', [b'userx@example.com',
                                      b'usery@example.com']),
    ('simplematch', 'simple_15.txt', [b'userx@example.be']),
    ('simplematch', 'simple_16.txt', [b'userx@example.com']),
    ('simplematch', 'simple_17.txt', [b'userx@example.com']),
    ('simplematch', 'simple_18.txt', [b'userx@example.com']),
    ('simplematch', 'simple_19.txt', [b'userx@example.com.ar']),
    ('simplematch', 'simple_20.txt', [b'userx@example.com']),
    ('simplematch', 'simple_23.txt', [b'userx@example.it']),
    ('simplematch', 'simple_24.txt', [b'userx@example.com']),
    ('simplematch', 'simple_25.txt', [b'userx@example.com']),
    ('simplematch', 'simple_26.txt', [b'userx@example.it']),
    ('simplematch', 'simple_27.txt', [b'userx@example.net.py']),
    ('simplematch', 'simple_29.txt', [b'userx@example.com']),
    ('simplematch', 'simple_30.txt', [b'userx@example.com']),
    ('simplematch', 'simple_31.txt', [b'userx@example.fr']),
    ('simplematch', 'simple_32.txt', [b'userx@example.com']),
    ('simplematch', 'simple_33.txt', [b'userx@example.com']),
    ('simplematch', 'simple_34.txt', [b'roland@example.com']),
    ('simplematch', 'simple_36.txt', [b'userx@example.com']),
    ('simplematch', 'simple_37.txt', [b'user@example.edu']),
    ('simplematch', 'simple_38.txt', [b'userx@example.com']),
    ('simplematch', 'simple_39.txt', [b'userx@example.ru']),
    ('simplematch', 'simple_41.txt', [b'userx@example.com']),
    ('simplematch', 'bounce_02.txt', [b'userx@example.com']),
    ('simplematch', 'bounce_03.txt', [b'userx@example.uk']),
    # SimpleWarning
    ('simplewarning', 'simple_03.txt', [b'userx@example.za'], True),
    ('simplewarning', 'simple_21.txt', [b'userx@example.com'], True),
    ('simplewarning', 'simple_22.txt', [b'User@example.org'], True),
    ('simplewarning', 'simple_28.txt', [b'userx@example.com'], True),
    ('simplewarning', 'simple_35.txt', [b'calvin@example.com'], True),
    ('simplewarning', 'simple_40.txt', [b'user@example.com'], True),
    # GroupWise
    ('groupwise', 'groupwise_01.txt', [b'userx@example.EDU']),
    # This one really sucks 'cause it's text/html.  Just make sure it
    # doesn't throw an exception, but we won't get any meaningful
    # addresses back from it.
    ('groupwise', 'groupwise_02.txt', []),
    # Actually, it's from Exchange, and Exchange does recognize it
    ('exchange', 'groupwise_02.txt', [b'userx@example.com']),
    # Not a bounce but has confused groupwise
    ('groupwise', 'groupwise_03.txt', []),
    # Yale's own
    ('yale', 'yale_01.txt', [b'userx@cs.yale.edu',
                             b'userx@yale.edu']),
    # DSN, i.e. RFC 1894
    ('dsn', 'dsn_01.txt', [b'userx@example.com']),
    ('dsn', 'dsn_02.txt', [b'zzzzz@example.uk']),
    ('dsn', 'dsn_03.txt', [b'userx@example.be']),
    ('dsn', 'dsn_04.txt', [b'userx@example.ch']),
    ('dsn', 'dsn_05.txt', [b'userx@example.cz'], True),
    ('dsn', 'dsn_06.txt', [b'userx@example.com'], True),
    ('dsn', 'dsn_07.txt', [b'userx@example.nz'], True),
    ('dsn', 'dsn_08.txt',
     [b'userx@example.de'], True),
    ('dsn', 'dsn_09.txt', [b'userx@example.com']),
    ('dsn', 'dsn_10.txt', [b'anne.person@dom.ain']),
    ('dsn', 'dsn_11.txt', [b'joem@example.com']),
    ('dsn', 'dsn_12.txt', [b'userx@example.jp']),
    ('dsn', 'dsn_13.txt', [b'userx@example.com']),
    ('dsn', 'dsn_14.txt', [b'userx@example.com.dk']),
    ('dsn', 'dsn_15.txt', [b'userx@example.com']),
    ('dsn', 'dsn_16.txt', [b'userx@example.com']),
    ('dsn', 'dsn_17.txt', [b'userx@example.fi'], True),
    # Microsoft Exchange
    ('exchange', 'microsoft_01.txt', [b'userx@example.COM']),
    ('exchange', 'microsoft_02.txt', [b'userx@example.COM']),
    # SMTP32
    ('smtp32', 'smtp32_01.txt', [b'userx@example.ph']),
    ('smtp32', 'smtp32_02.txt', [b'userx@example.com']),
    ('smtp32', 'smtp32_03.txt', [b'userx@example.com']),
    ('smtp32', 'smtp32_04.txt', [b'after_another@example.net',
                                 b'one_bad_address@example.net']),
    ('smtp32', 'smtp32_05.txt', [b'userx@example.com']),
    ('smtp32', 'smtp32_06.txt', [b'Absolute_garbage_addr@example.net']),
    ('smtp32', 'smtp32_07.txt', [b'userx@example.com']),
    # Qmail
    ('qmail', 'qmail_01.txt', [b'userx@example.de']),
    ('qmail', 'qmail_02.txt', [b'userx@example.com']),
    ('qmail', 'qmail_03.txt', [b'userx@example.jp']),
    ('qmail', 'qmail_04.txt', [b'userx@example.au']),
    ('qmail', 'qmail_05.txt', [b'userx@example.com']),
    ('qmail', 'qmail_06.txt', [b'ntl@xxx.com']),
    ('qmail', 'qmail_07.txt', [b'user@example.net']),
    ('qmail', 'qmail_08.txt', []),
    # LLNL's custom Sendmail
    ('llnl', 'llnl_01.txt', [b'user1@example.gov']),
    # Netscape's server...
    ('netscape', 'netscape_01.txt', [b'aaaaa@corel.com',
                                     b'bbbbb@corel.com']),
    # Yahoo's proprietary format
    ('yahoo', 'yahoo_01.txt', [b'userx@example.com']),
    ('yahoo', 'yahoo_02.txt', [b'userx@example.es']),
    ('yahoo', 'yahoo_03.txt', [b'userx@example.com']),
    ('yahoo', 'yahoo_04.txt', [b'userx@example.es',
                               b'usery@example.uk']),
    ('yahoo', 'yahoo_05.txt', [b'userx@example.com',
                               b'usery@example.com']),
    ('yahoo', 'yahoo_06.txt', [b'userx@example.com',
                               b'usery@example.com',
                               b'userz@example.com',
                               b'usera@example.com']),
    ('yahoo', 'yahoo_07.txt', [b'userw@example.com',
                               b'userx@example.com',
                               b'usery@example.com',
                               b'userz@example.com']),
    ('yahoo', 'yahoo_08.txt', [b'usera@example.com',
                               b'userb@example.com',
                               b'userc@example.com',
                               b'userd@example.com',
                               b'usere@example.com',
                               b'userf@example.com']),
    ('yahoo', 'yahoo_09.txt', [b'userx@example.com',
                               b'usery@example.com']),
    ('yahoo', 'yahoo_10.txt', [b'userx@example.com',
                               b'usery@example.com',
                               b'userz@example.com']),
    ('yahoo', 'yahoo_11.txt', [b'bad_user@aol.com']),
    # sina.com appears to use their own weird SINAEMAIL MTA
    ('sina', 'sina_01.txt', [b'userx@sina.com',
                             b'usery@sina.com']),
    ('aol', 'aol_01.txt', [b'screenname@aol.com']),
    # No address can be detected in these...
    # dumbass_01.txt - We love Microsoft. :(
    # Done
    )
