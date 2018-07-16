'''
Browser creation and configuration convenience functions.

This module provides several convenience functions related to creating Selenium broswers:

    * :py:func:`preferences_from_config_file` - Read preferences from a browser
      section of config file.
    * :py:func:`firefox_preferences` - Overlay preferences on a default set for Firefox.
    * :py:func:`firefox_profile_with_preferences` - Create a Firefox profile and
      customize it with the given preferences.
    * :py:func:`get_browser` for creating and configuring a Selenium browser.

These functions are designed to work together, but don't depend on each other so you can
use just the parts that are helpful.
'''

from configparser import ConfigParser
import logging
import os

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver import FirefoxProfile

from .exceptions import UnknownBrowserException


debug = logging.getLogger(__name__).debug

DEFAULT_DOWNLOAD_DIRECTORY = 'downloads'
DEFAULT_HOME_PAGE_URL = 'about:about'


DEFAULT_BROWSER_CAPABILITIES = {
    'native_events_enabled': 'False',
    'handleAlerts': 'False',
    'unexpectedAlertBehaviour': 'ignore',
}
'''Default capabilties to apply on top of a webdriver DesiredCapabilities dictionary.'''


DEFAULT_FIREFOX_PREFERENCES = {
    'browser.startup.page': 1,
    'browser.download.folderList': 2,
    'browser.download.manager.showWhenStarting': False,
    'plugin.disable_full_page_plugin_for_types': 'application/pdf',
    'pdfjs.disabled': True,
    'browser.helperApps.neverAsk.saveToDisk': 'application/pdf',
}
'''Default browser preferences for Firefox.'''


def firefox_preferences(download_directory=DEFAULT_DOWNLOAD_DIRECTORY,
                        home_page_url=DEFAULT_HOME_PAGE_URL,
                        preference_settings={}):
    '''Create a dictionary of Firefox preferences.

    Args:
        download_directory (str, optional): where files will be downloaded.
            Set to None to suppress setting this value in the returned dictionary.
        home_page_url (str, optional): url for the home page
            Set to None to suppress setting this value in the returned dictionary.
        preference_settings (dict): Additional preferences to set/override on top
            of a copy of :py:data:`DEFAULT_FIREFOX_PREFERENCES`.
            All values in this dictionary that can be converted to ``int``
            will be and will be put in to the result dictionary as such,
            otherwise they will be left as is.

    Returns:
        dict: preferences as per the parameters
    '''
    browser_settings = DEFAULT_FIREFOX_PREFERENCES.copy()
    if download_directory is not None:
        browser_settings['browser.download.dir'] = download_directory
    if home_page_url is not None:
        browser_settings['browser.startup.homepage'] = home_page_url

    for k, v in preference_settings.items():
        try:
            browser_settings[k] = int(v)
        except ValueError:
            browser_settings[k] = v

    return browser_settings


def firefox_profile_with_preferences(preferences_dict, native_events_enabled=False):
    '''
    Create a Firefox Profile with the given preferences.

    Any preferences_dict can be used; :py:func:`firefox_preferences` might
    be a handy way to get one.

    Args:
        preferences_dict (dict): Keys and values used to set preferences
            on the new profile.
        native_events_enabled (bool, optional): Used to set the corresponding value
            on the new profile. Use the default unless you know what you are doing.

    Returns:
        FirefoxProfile: A new profile, as customized.
    '''

    profile = FirefoxProfile()
    profile.native_events_enabled = native_events_enabled
    for k, v in preferences_dict.items():
        profile.set_preference(k, v)
    return profile


def preferences_from_config_file(config_file, browser_name):
    '''Build a preferences dictionary from a config (INI) file.

    Args:
        config_file (str, or ConfigParser): The config file to read.
            This can be the name of a `.INI` file, or an instance of a
            ``ConfigParser`` object from a config file already loaded.
        browser_name (str): Which browser preferences section to read.

    Returns:
        dict: preferences read from the config file.
            The browser_name is concatenated with ``_preferences`` to find
            the section of the config file to read. Each entry/value in that
            section becomes a key/value pair in the returned dictionary.
    '''
    if isinstance(config_file, ConfigParser):
        config_parser = config_file
    else:
        config_parser = ConfigParser()
        config_parser.read(config_file)

    section_name = browser_name.lower() + '_preferences'
    error = 'Cannot find "{}" in your config file: {}'.format(section_name, config_file)
    assert section_name in config_parser, error
    return dict(config_parser[section_name].items())


def get_browser(browser_name,
                page_load_timeout,
                window_size=None,
                firefox_profile=None,
                capabilities_dict=DEFAULT_BROWSER_CAPABILITIES,
                grid_url=None,
                **kwargs):
    '''Get a browser with some helpful pre-configuration.

    Args:

        browser_name (str): The name of the browser you want to run.
        page_load_timeout (int): passed on the browser setting of the same name
        window_size (2-tuple, None): a 2-tuple for the window size; use None to maximize the window.
            NOTE: This is ignored when grid_url is supplied.
        firefox_profile (FirefoxProfile): The profile to use for Firefox.
            Any profile can be used; :py:func:`firefox_profile_with_preferences` might be a handy
            way to get one. This only optional if the browser isn't Firefox.
        capabilities_dict (dict, optional): Capabilities to set on top of the webdriver defaults
            for the given browser.
        grid_url (str, optional): if not None means you want to run on the grid instead of locally.
        kwargs (dict): additional parameters for the Webdriver browser creation.

    Returns:
        webdriver: A webdriver browser instance configured as per the parameters.
    '''

    capabilities = getattr(webdriver.DesiredCapabilities, browser_name.upper()).copy()
    capabilities.update(capabilities_dict)

    if grid_url:
        browser = webdriver.Remote(command_executor=grid_url,
                                   desired_capabilities=capabilities)
    else:
        if browser_name.lower() == 'firefox':
            browser = webdriver.Firefox(
                capabilities=capabilities,
                firefox_profile=firefox_profile,
                log_path=os.devnull,
                **kwargs)
        elif browser_name.lower() == 'chrome':
            browser = webdriver.Chrome(desired_capabilities=capabilities, **kwargs)
        else:
            raise UnknownBrowserException(browser_name)

    browser.set_page_load_timeout(page_load_timeout)

    if window_size is not None:
        browser.set_window_size(*window_size)
        debug('Set window size: {}'.format(window_size))
    else:
        # Some versions of some browsers, when run on the grid, cannot maximize.
        # Since maximize is the default, protect against it failing and keep going.
        try:
            browser.maximize_window()
            debug('Maximized window')
        except WebDriverException as e:
            debug('Maximize browser attempt failed: {}'.format(e))

    return browser
