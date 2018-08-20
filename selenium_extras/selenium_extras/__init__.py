'''
Selenium Extras
===============

.. warning::

    Documentation is for package version: {__version__}

Selenium Extras is provides helpers to simplify web-UI interface interactions.

.. note::

    This package was based-on the open source OpenCAFE Selenium Plug-in and leverages
    that code heavily without having any dependency on OpenCAFE.

    The only dependencies are on selenium and the built-in python libraries.
    Only Python 3 is supported.

Quick overview of the modules in this package:

    * :py:mod:`selenium_extras.browser_config` - Create/configure Selenium Browsers.
    * :py:mod:`selenium_extras.client` - Client (driver) for interacting with Selenium Browsers.
    * :py:mod:`selenium_extras.constants` - Utility values by the other modules in this package.
    * :py:mod:`selenium_extras.exceptions` - Additional exceptions raised in this package.
    * :py:mod:`selenium_extras.locators` - Meat and potatoes for finding things in the browser.
    * :py:mod:`selenium_extras.page` - Base level Page object for Page-Object-Module users.
    * :py:mod:`selenium_extras.popups` - Helpers for dealing with Popups.


Class inheritance diagram for each module, all together here.
Clicking on a class name will take you to its documentation:

.. inheritance-diagram:: browser_config client constants exceptions locators page popups
   :parts: 1
'''

from .__version__ import __version__

__doc__ = __doc__.format(**globals())
