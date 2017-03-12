import os
import logging

from flufl.bounce.interfaces import IBounceDetector
from importlib import import_module
from pkg_resources import resource_listdir
from public import public


log = logging.getLogger('flufl.bounce')


def _find_detectors(package):
    missing = object()
    for filename in resource_listdir(package, ''):
        basename, extension = os.path.splitext(filename)
        if extension != '.py':
            continue
        module_name = '{}.{}'.format(package, basename)
        module = import_module(module_name)
        for name in getattr(module, '__all__', []):
            component = getattr(module, name, missing)
            if component is missing:
                log.error('skipping missing __all__ entry: {}'.format(name))
            if IBounceDetector.implementedBy(component):
                yield component


@public
def scan_message(msg):
    """Detect the set of all permanently bouncing original recipients.

    :param msg: The bounce message.
    :type msg: `email.message.Message`
    :return: The set of detected original recipients.
    :rtype: set of strings
    """
    permanent_failures = set()
    package = 'flufl.bounce._detectors'
    for detector_class in _find_detectors(package):
        log.info('Running detector: {}'.format(detector_class))
        try:
            temporary, permanent = detector_class().process(msg)
        except Exception:
            log.exception('Exception in detector: {}'.format(detector_class))
            raise
        permanent_failures.update(permanent)
    return permanent_failures


@public
def all_failures(msg):
    """Detect the set of all bouncing original recipients.

    :param msg: The bounce message.
    :type msg: `email.message.Message`
    :return: 2-tuple of the temporary failure set and permanent failure set.
    :rtype: (set of strings, set of string)
    """
    temporary_failures = set()
    permanent_failures = set()
    package = 'flufl.bounce._detectors'
    for detector_class in _find_detectors(package):
        log.info('Running detector: {}'.format(detector_class))
        temporary, permanent = detector_class().process(msg)
        temporary_failures.update(temporary)
        permanent_failures.update(permanent)
    return temporary_failures, permanent_failures
