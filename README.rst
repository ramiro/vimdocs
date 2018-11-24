=======
vimdocs
=======

Let's try bringing VIM documentation to the 21st century.

Requirements
============

* Python 3.6
* Pipenv

Setup
=====

Install our Python dependencies (we assume you already have `Pipenv installed`_)::

    $ pipenv install

Install *Asciidoctor* (using Ruby's ``bundle``)::

    $ bundle install --path vendor/bundle

Checkout a copy of the Vim source code to a ``vim/`` directory sibling to this one::

    $ ( cd .. ; git clone https://github.com/vim/vim ; cd - )

(this is because our scripts expect to find the Vim documentation at ``../vim/runtime/doc/``.)

.. _Pipenv installed: https://pipenv.readthedocs.io/en/latest/install/#installing-pipenv

Running the conversion process
==============================

Perform a full conversion::

    $ pipenv run ./build.sh

If everything goes well the resulting final output should be in ``output/html/``.

Working on the project itself
=============================

Additionally to the steps described in `Setup`_ install the *development-time*
dependencies::

    $ pipenv install --dev

You can also run our checks and tests by using *tox*. Install it per `its
documentation`_ (it needs to be available as a script runnable by your OS user)
and then run::

    $ tox

.. _its documentation: https://tox.readthedocs.io/en/stable/install.html

Project dir contents
====================

============================= ======================================================================
``adoc/``                     Dir for output AsciiDoctor files
``build.sh``                  Uses ``itervimdocs.py`` and ``vimdoc2adoc.py`` to create *Asciidoctor*
                              files and then asciidoctor to create HTML files from them
``itervimdocs.py``            Process Vim docs .txt files with a provided command
``files.py``                  Describe Vim docs .txt files encodings, etc. Used by ``itervimdocs.py``
``Gemfile``                   Ruby packaging admin files
``Gemfile.lock``              Ruby packaging admin files
``output/``                   Output dir
``vimdoc2adoc.py``            Script that does the heavylifting
``README.rst``                This file
``vendor/``                   Ruby packaging admin files
============================= ======================================================================
