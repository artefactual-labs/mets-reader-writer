# -*- coding: utf-8 -*-
"""Dependency Injection logic for metsrw.

Here a global singleton feature broker is instantiated. By providing features
(i.e., dependencies) to the feature broker one can alter, for example, the
PREMIS dependencies used by metsrw's ``FSEntry`` class when reading and writing
PREMIS XML. Here we provide default classes for handling PREMIS using classes
defined in plugins.premisrw::

    >>> feature_broker = FeatureBroker()
    >>> feature_broker.provide('premis_object_class', premisrw.PREMISObject)
    >>> feature_broker.provide('premis_event_class', premisrw.PREMISEvent)
    >>> feature_broker.provide('premis_agent_class', premisrw.PREMISAgent)

However, the PREMIS dependencies can be altered by providing other features
with the same names, e.g.,::

    >>> feature_broker.provide('premis_object_class', MyOtherPREMISObjectClass)

See http://code.activestate.com/recipes/413268/
"""

from six import with_metaclass

from .plugins import premisrw


class FeatureBroker(object):
    """Feature broker allows for the provisioning of features. These features
    are dependencies that can be injected. Usage::

        >>> feature_broker = FeatureBroker()
        >>> feature_broker.provide('premis_object_class', premisrw.PREMISObject)
    """

    def __init__(self, allow_replace=True):
        self.providers = {}
        self.allow_replace = allow_replace

    def provide(self, feature_name, provider, *args, **kwargs):
        """Provide a feature named ``feature_name`` using the provider object
        ``provider`` and any arguments (``args``, ``kwargs``) needed by the
        provider if it is callable.
        """
        if not self.allow_replace:
            assert feature_name not in self.providers, (
                'Duplicate feature: {!r}'.format(feature_name))
        if callable(provider) and not isinstance(provider, type):
            self.providers[feature_name] = lambda: provider(*args, **kwargs)
        else:
            self.providers[feature_name] = lambda: provider

    def clear(self):
        self.providers.clear()

    def __len__(self):
        return len(self.providers)

    def __getitem__(self, feature_name):
        try:
            provider = self.providers[feature_name]
        except KeyError:
            raise KeyError('Unknown feature named {!r}'.format(feature_name))
        return provider()


def set_feature_broker_to_default_state(fb):
    fb.clear()
    fb.provide('premis_object_class', premisrw.PREMISObject)
    fb.provide('premis_event_class', premisrw.PREMISEvent)
    fb.provide('premis_agent_class', premisrw.PREMISAgent)


feature_broker = FeatureBroker()  # global singleton feature broker
set_feature_broker_to_default_state(feature_broker)


class Dependency(object):
    """Non-overriding descriptor for declaring required dependencies in metsrw
    classes. In the following example usage the ``FSEntry`` class is declaring
    a dependency on a feature named 'premis_object_class' which is a class and
    which has methods ``fromtree`` and ``serialize``::

        >>> from .di import is_class, has_methods, Dependency
        >>> class FSEntry(object):
        ...     premis_object_class = Dependency(
        ...         has_methods('serialize'),
        ...         has_class_methods('fromtree'),
        ...         is_class)

    """

    def __init__(self, *assertions):
        self.dependency_name = None
        self.assertions = assertions

    def __get__(self, instance, owner):
        obj = feature_broker[self.dependency_name]
        for assertion in self.assertions:
            assert assertion(obj), (
                'The value {!r} of {!r} does not match the specified'
                ' criteria'.format(obj, self.dependency_name))
        return obj


class DependencyPossessorMeta(type):
    """Metaclass for ``DependencyPossessor``. Classes that can have
    dependencies---i.e., classes that have class attributes whose values are
    instances of ``Dependency`` above---must inherit from
    ``DependencyPossessor``. This allows us to tell the ``Dependency`` instance
    that its ``dependency_name`` value should be the same as the name of the
    class attribute it was assigned to in the managed class. In short, it
    allows us to write ``premis_object_class = Dependency()`` instead of
    ``premis_object_class = Dependency('premis_object_class')``.
    """
    def __init__(cls, name, bases, attr_dict):
        super(DependencyPossessorMeta, cls).__init__(name, bases, attr_dict)
        for key, attr in attr_dict.items():
            if isinstance(attr, Dependency):
                attr.dependency_name = key


class DependencyPossessor(with_metaclass(DependencyPossessorMeta, object)):
    pass


# ==============================================================================
#   Assertions for declaring dependencies using Dependency
# ==============================================================================

def has_class_methods(*class_method_names):
    """Return a test function that, when given a class, returns ``True`` if that
    class has all of the class methods in ``class_method_names``. If an object
    is passed to the test function, check for the class methods on its
    class.
    """
    def test(cls):
        if not isinstance(cls, type):
            cls = type(cls)
        for class_method_name in class_method_names:
            try:
                class_method = getattr(cls, class_method_name)
                if class_method.__self__ is not cls:
                    return False
            except AttributeError:
                return False
        return True
    return test


def has_methods(*method_names):
    """Return a test function that, when given an object (class or an
    instance), returns ``True`` if that object has all of the (regular) methods
    in ``method_names``. Note: this is testing for regular methods only and the
    test function will correctly return ``False`` if an instance has one of the
    specified methods as a classmethod or a staticmethod. However, it will
    incorrectly return ``True`` (false positives) for classmethods and
    staticmethods on a *class*.
    """
    def test(obj):
        for method_name in method_names:
            try:
                method = getattr(obj, method_name)
            except AttributeError:
                return False
            else:
                if not callable(method):
                    return False
                if not isinstance(obj, type):
                    try:
                        # An instance method is a method type with a __self__
                        # attribute that references the instance.
                        if method.__self__ is not obj:
                            return False
                    except AttributeError:
                        return False
        return True
    return test


def is_class(obj):
    return isinstance(obj, type)
