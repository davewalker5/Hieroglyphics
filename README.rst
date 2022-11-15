.. image:: https://github.com/davewalker5/Hieroglyphics/workflows/Python%20CI%20Build/badge.svg
    :target: https://github.com/davewalker5/Hieroglyphics/actions
    :alt: Build Status

.. image:: https://codecov.io/gh/davewalker5/Hieroglyphics/branch/main/graph/badge.svg?token=U86UFDVD5S
    :target: https://codecov.io/gh/davewalker5/Hieroglyphics
    :alt: Coverage

.. image:: https://sonarcloud.io/api/project_badges/measure?project=davewalker5_Hieroglyphics&metric=alert_status
    :target: https://sonarcloud.io/summary/new_code?id=davewalker5_Hieroglyphics
    :alt: Quality Gate

.. image:: https://img.shields.io/github/issues/davewalker5/Hieroglyphics
    :target: https://github.com/davewalker5/Hieroglyphics/issues
    :alt: GitHub issues

.. image:: https://img.shields.io/github/v/release/davewalker5/Hieroglyphics.svg?include_prereleases
    :target: https://github.com/davewalker5/Hieroglyphics/releases
    :alt: Releases

.. image:: https://img.shields.io/badge/License-mit-blue.svg
    :target: https://github.com/davewalker5/Hieroglyphics/blob/main/LICENSE
    :alt: License

.. image:: https://img.shields.io/badge/language-python-blue.svg
    :target: https://www.python.org
    :alt: Language

.. image:: https://img.shields.io/github/languages/code-size/davewalker5/Hieroglyphics
    :target: https://github.com/davewalker5/Hieroglyphics/
    :alt: GitHub code size in bytes


English to Hieroglyphics Transliterator
=======================================

The English to hieroglyphics transliterator is an application for performing a simplistic transliteration of words
and phrases entered in English to their hieroglyphic equivalent.

Structure
=========

+-------------------------------+----------------------------------------------------------------------+
| **Package**                   | **Contents**                                                         |
+-------------------------------+----------------------------------------------------------------------+
| hieroglyphics.transliteration | Business logic for the application                                   |
+-------------------------------+----------------------------------------------------------------------+
| hieroglyphics.web             | A simple Flask-based web site providing a user-interface             |
+-------------------------------+----------------------------------------------------------------------+

Running the Application
=======================

Pre-requisites
--------------

To run the application, a virtual environment should be created, the requirements should be installed using pip and the
environment should be activated.

Running the Web Application
---------------------------

To run the web-based application in the Flask development web server, enter the following from the root of the working
copy of the project:

::

    export PYTHONPATH=`pwd`/src
    export FLASK_DEBUG=1
    python -m hieroglyphics

The first four commands will need to be modified based on the current operating system. Once the development server
is running, browse to the following URL in a  web browser:

::

    http://127.0.0.1:5000/


Unit Tests and Coverage
=======================

Unit tests are WIP

Generating Documentation
========================

To generate the documentation, a virtual environment should be created, the requirements should be installed
using pip and the environment should be activated.

HTML documentation can then be created by running the following commands from the "docs" sub-folder:

::

    export PYTHONPATH=`pwd`/../src/
    make html

The resulting documentation is written to the docs/build/html folder and can be viewed by opening "index.html" in a
web browser.


Dependencies
============

The application has dependencies listed in requirements.txt.


Distribution
============

A distribution can be created by running the following from a command prompt at the root of the project:

::

    pip install wheel
    python setup.py bdist_wheel

Note that the project's virtual environment should **not** be activated when creating distributions.


License
=======

This software is licensed under the MIT License:

https://opensource.org/licenses/MIT

Copyright 2022 David Walker

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
