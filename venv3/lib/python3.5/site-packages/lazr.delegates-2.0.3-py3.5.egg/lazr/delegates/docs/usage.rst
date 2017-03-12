==============
lazr.delegates
==============

The ``lazr.delegates`` package makes it easy to write objects that delegate
behavior to another object. The new object adds some property or behavior on
to the other object, while still providing the underlying interface, and
delegating behavior.


Usage
=====

The ``@delegate_to`` class decorator makes a class implement zero or more
interfaces by delegating the implementation to another object.  In the case of
a class providing an adapter, that object will be the *context*, but it can
really be any object stored in an attribute.  So while the interfaces use an
inheritance mechanism, the classes use a composition mechanism.

For example, we can define two interfaces ``IFoo0`` and ``IFoo1`` where the
latter inherits from the former.  The first interface defines an attribute.

    >>> from zope.interface import Interface, Attribute
    >>> class IFoo0(Interface):
    ...     one = Attribute('attribute in IFoo0')

The second (i.e. derived) interface defines a method and an attribute.

    >>> class IFoo1(IFoo0):
    ...     def bar():
    ...         """A method in IFoo1"""
    ...     baz = Attribute('attribute in IFoo1')

We also define two classes that mirror the interfaces, and do something
interesting.
::

    >>> class Foo0:
    ...     one = 'one'

    >>> class Foo1(Foo0):
    ...     def bar(self):
    ...         return 'bar'
    ...     baz = 'I am baz'

Finally, to tie everything together, we can define a class that delegates the
implementation of ``IFoo1`` to an attribute on the instance.  By default,
``self.context`` is used as the delegate attribute.

    >>> from lazr.delegates import delegate_to
    >>> @delegate_to(IFoo1)
    ... class SomeClass:
    ...     def __init__(self, context):
    ...         self.context = context

When the class doing the delegation is instantiated, an instance of the class
implementing the interface is passed in.

    >>> delegate = Foo1()
    >>> s = SomeClass(delegate)

Now, the ``bar()`` method comes from ``Foo1``.

    >>> print(s.bar())
    bar

The ``baz`` attribute also comes from ``Foo1``.

    >>> print(s.baz)
    I am baz

The ``one`` attribute comes from ``Foo0``.

    >>> print(s.one)
    one

Even though the interface of ``SomeClass`` is defined through the delegate,
the interface is still provided by the instance.

    >>> IFoo1.providedBy(s)
    True


Custom context
--------------

The ``@delegate_to`` decorator takes an optional keyword argument to customize
the attribute containing the object to delegate to.

    >>> @delegate_to(IFoo1, context='myfoo')
    ... class SomeOtherClass:
    ...     def __init__(self, foo):
    ...         self.myfoo = foo

The attributes and methods are still delegated correctly.

    >>> s = SomeOtherClass(delegate)
    >>> print(s.bar())
    bar
    >>> print(s.baz)
    I am baz


Multiple interfaces
===================

The ``@delegate_to`` decorator accepts more than one interface.  Note however,
that the context attribute must implement all of the named interfaces.

    >>> class IFoo2(Interface):
    ...     another = Attribute('another attribute')

Here is a class that implements the interface.  It inherits from the
implementation class that provides the ``IFoo0`` interface.  Thus does this
class implement both interfaces.

    >>> class Foo2(Foo0):
    ...     another = 'I am another foo'

Again, we tie it all together.

    >>> @delegate_to(IFoo0, IFoo2)
    ... class SomeOtherClass:
    ...     def __init__(self, context):
    ...         self.context = context

Now, the instance of this class has all the expected attributes, and provides
the expected interfaces.

    >>> s = SomeOtherClass(Foo2())
    >>> print(s.another)
    I am another foo
    >>> IFoo0.providedBy(s)
    True
    >>> IFoo2.providedBy(s)
    True
