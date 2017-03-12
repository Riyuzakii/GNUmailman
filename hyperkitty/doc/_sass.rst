You will also need to install the `Sass`_ CSS processor using your package
manager or the project's installation documentation. You can either use the
default Ruby implementation or the C/C++ version, called `libsass`_ (the binary
is ``sassc``). The configuration file in ``example_project/settings.py``
defaults to the ``sassc`` version, but you just have to edit the
``COMPRESS_PRECOMPILERS`` mapping to switch to the Ruby implementation, whoose
binary is called ``sass``.

Those tools are usually packaged by your distribution. On Fedora the Ruby
package is named ``rubygem-sass``, so you can install it with::

    sudo yum install rubygem-sass

On Debian and Ubuntu, the Ruby pacakge is available in the ``ruby-sass``
package, which you can install with::

    sudo apt-get install ruby-sass

There is no package of libsass or sassc on either distribution today, but it is
being worked on.

.. _Sass: http://sass-lang.com
.. _libsass: http://sass-lang.com/libsass

