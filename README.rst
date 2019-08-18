======
pypuck
======

.. image:: https://img.shields.io/pypi/v/pypuck.svg
    :target: https://pypi.python.org/pypi/pypuck

.. image:: https://travis-ci.org/starofrainnight/pypuck.svg?branch=master
    :target: https://travis-ci.org/starofrainnight/pypuck

.. image:: https://ci.appveyor.com/api/projects/status/github/starofrainnight/pypuck?svg=true
    :target: https://ci.appveyor.com/project/starofrainnight/pypuck

A script for compile python program to portable executable (for windows only currently)

Just like cxfreeze, pyinstaller or py2exe.

This program have much different from those packager applications above. We package the python application with the full functional python environment without analyse your python application dependences, so you have to ensure your application's dependences in `setup.py` .

Certainly, we have our rules, only those python application that wrote  in standard python package layout will be packaged successed.

If a python application could be installed by standard command:

    python setup.py install

and the `entry_points` has been correct defined in `setup.py`, this python application could be packaged.

* License: Apache-2.0
* Documentation: https://pypuck.readthedocs.io.

Features
--------

* Package with winpython core, a full python environment
* Always use latest stable python
* No special codes needs to changed just like you works with other packager applications (just like the `__main__` problems that works with cxfreeze)

Usage
-------

TBD.

Known Issues
-------------

* Only works with windows

Credits
---------

This package was created with Cookiecutter_ and the `PyPackageTemplate`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`PyPackageTemplate`: https://github.com/starofrainnight/rtpl-pypackage

