..
   Created : 2018-01-02

   @author: Eric Lapouyade

   django-best-templatetags documentation master file,

========================
django-best-templatetags
========================

Best tags and filters for Django templates

Installation
------------

Install with pip::

    pip install best_templatetags

Then declare the app in your settings.py ::

    INSTALLED_APPS = [
    ...
        'best_templatetags',
    ]

To use the filters, add in your template::

    {% load best_filters %}


To use the tags, add in your template::

    {% load best_tags %}



Filters
-------

.. currentmodule:: best_filters
.. autosummary::
     :toctree: stubs
     :nosignatures:

     age
     basename
     dirname
     divide
     get_key
     listsort
     listsortreversed
     multiply
     replace
     resub
     sanitizetags
     truncat

Tags
----

.. currentmodule:: best_tags
.. autosummary::
     :toctree: stubs
     :nosignatures:

     render_template
     update_url

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

