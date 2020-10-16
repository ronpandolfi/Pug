=====
Usage
=====

You can use pug without specifying an operation. Pug shows you a selection of available packages matching that name.
From this menu you can select to install/uninstall packages::

    pug numpy

.. image:: _static/example1.png
  :width: 400
  :alt: pug numpy

Some packages can be installed from multiple providers, and/or installed by different mechanisms. If pug finds these
options, you'll have some choices.

You can also list installed packages with::

    pug

There are also some special commands Pug provides.

Refresh
-------

The `refresh` command is useful when working with editable installations which include entry points. Each time a package's entry points change, it must be reinstalled for that change to take effect, even when using editable installations. A quick and lazy way to 'resfresh' those packages is simply::

    pug refresh
    
This effectively reinstalls all editable packages, updating their entry points. 
