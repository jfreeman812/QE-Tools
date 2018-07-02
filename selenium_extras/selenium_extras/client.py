# Copyright 2016, 2018 Rackspace
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import os
import logging
from glob import glob

from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import (NoAlertPresentException,
                                        NoSuchElementException,
                                        TimeoutException,
                                        UnexpectedAlertPresentException)
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.support import expected_conditions as EC  # noqa N812
from selenium.webdriver.remote.remote_connection import LOGGER

from .constants import SEARCH
from .exceptions import PageLoadTimeoutException, JQueryTimeoutException

from time import sleep

# Turn off the spamminess of the Selenium Logger
LOGGER.setLevel(logging.WARNING)

_screenshot_errormessage = "'{}' should have exactly 1 pair of curly brackets"


class SeleniumClient(object):
    '''
    This is the top-level client for the browser extensions.

    The underlying Browser instance will be available as the `.browser` field.

        driver = SeleniumClient(browser_instance)
        driver.start('http://www.google.com')
        driver.browser.find_element_by_name('blah')
    '''
    _log = logging.getLogger(__name__)

    def __init__(self, browser, default_url, page_load_timeout,
                 page_element_timeout,
                 screenshot_path,
                 base_screenshot_filename='selenium_screenshot_{}.png',
                 optional_screen_shots=True):
        '''
        The base initialization for the selenium client

        Args:
            browser (webdriver browser): The browser instance to use for underlying actions.
            default_url (str): Where to go when no URL is passed to 'start'.
            page_load_timeout (int): How long, in seconds, for ``wait_for_document_ready`` to wait.
            page_element_timeout (int): How long, in seconds, to wait for elements (visible, etc.)
            screenshot_path (str): Where on the filesystem to put the the screenshots.
            base_screenshot_filename (str, optional): This is the default file
                name the system will use for screenshots. It should contain exactly one pair
                of curly brackets that will be replaced by a unique-ifying number.
            optional_screen_shots (bool): If True, take screen shots when clicking, selecting, etc.
        '''
        self.browser = browser
        self.default_url = default_url
        self.page_load_timeout = page_load_timeout
        self.page_element_timeout = page_element_timeout
        self.screenshot_path = screenshot_path
        self.optional_screen_shots = optional_screen_shots

        assert base_screenshot_filename.count('{}') == 1, \
            _screenshot_errormessage.format(base_screenshot_filename)

        self.base_screenshot_filename = base_screenshot_filename

    def start(self, url=None):
        '''
        Go to the given url.

        Args:
            url(str): The URL the browser should visit.
                If None, the default_url will be used.
        '''
        if not url:
            url = self.default_url
        self.go_to(url)

    @property
    def title(self):
        '''
        The title for the current page

        Returns:
            str: the page title
        '''
        return self.browser.title

    @property
    def current_url(self):
        '''
        The browser's current url

        Returns:
            str: the current URL
        '''
        return self.browser.current_url

    def take_screenshot(self, screenshot_filename=False):
        '''
        Take a screenshot of the current page

        Args:
            screenshot_filename (str): [Optional] This is the filename to be
                used for the screenshot. If not given, a numbered screen shot
                file name will be automatically created.

        Returns:
            str: The name of the screen shot file used.

        The screenshot file will be put into the screenshot_path directory
        passed in to the constructor.
        '''
        if not screenshot_filename:
            search = glob(
                os.path.join(self.screenshot_path,
                             self.base_screenshot_filename.format('*')))
            screenshot_filename = self.base_screenshot_filename.format(
                len(search))
        filename = os.path.join(self.screenshot_path, screenshot_filename)
        if not os.path.isdir(os.path.dirname(filename)):
            os.makedirs(os.path.dirname(filename))
        try:
            self.browser.save_screenshot(filename)
        except UnexpectedAlertPresentException:
            pass
        return filename

    def optional_take_screenshot(self, *args, **kwargs):
        '''Take a screen shot if ``optional_screen_shots`` was True in the constructor.

        Intended for use where code may want to take screenshots for tracing or logging purposes,
        but not when a screenshot must be taken (say on an error). This is called from
        various Locators automatically.

        Parameters are passed to ``take_screenshot``.

        Returns:
            str or None: If a screen shot was taken return the file name, otherwise return None.
        '''
        if self.optional_screen_shots:
            return self.take_screenshot(*args, **kwargs)
        return None

    def javascript(self, script):
        '''
        Execute javascript in the current page.

        Args:
            script (str): the javascript to execute

        Returns:
            any: the result of the execute_script method of the browser.
        '''
        return self.browser.execute_script(script)

    def refresh(self):
        '''
        Refresh the browser page
        '''
        self.browser.refresh()
        self.wait_for_document_ready()

    def wait_for_document_ready(self, timeout=None):
        '''
        Wait timeout seconds for ``is_document_ready`` to return True.

        Args:
            timeout (int): How long to wait in seconds. If None, then
                the page_load_timeout from the constructor will be used.

        Raises:
            PageLoadTimeoutException: If ``is_document_ready`` doesn't return
                True in the given time.
        '''
        if timeout is None:
            timeout = self.page_load_timeout
        try:
            WebDriverWait(self, timeout).until(lambda d: d.is_document_ready())
        except TimeoutException:
            message = 'Page failed to become document ready within {} seconds'.format(timeout)
            raise PageLoadTimeoutException(message)

    def wait_for_jquery_done(self, timeout=None):
        '''
        Wait timeout seconds for ``is_jquery_active`` to return False.

        Args:
            timeout (int): How long to wait in seconds. If None, then
                the page_load_timeout from the constructor will be used.

        Raises:
            JQueryTimeoutException: If ``is_jquery_active`` doesn't return
                False in the given time.
        '''
        if timeout is None:
            timeout = self.page_load_timeout
        try:
            WebDriverWait(self, timeout).until(lambda d: not d.is_jquery_active())
        except TimeoutException:
            message = 'JQuery was still active after {} seconds.'.format(timeout)
            raise JQueryTimeoutException(message)

    def is_document_ready(self):
        '''
        Javascript check to see if the readyState is complete.

        NOTE: This does not necessarily mean the page has finished loading,
        as AJAX and other scripts could still be running.
        '''
        return self.javascript("return document.readyState == 'complete';")

    def is_jquery_active(self):
        '''Is jQuery active?

        Returns:
            bool: True if jQuery is active, False otherwise.
        '''
        return not self.javascript('return jQuery.active == 0;')

    def wait_for_url_to_contain(self, url_part, timeout=None):
        '''
        Wait for the URL to contain url_part

        Args:
            url_part (str): The substring of the url to look for.
            timeout (int): How long in seconds to wait. If None, the page_load_timeout
                from the constructor will be used.

        Raises:
            PageLoadTimeoutException - if the the URL does not contain the url_part
                within timeout seconds.
        '''
        if timeout is None:
            timeout = self.page_load_timeout
        try:
            WebDriverWait(self, timeout).until(EC.url_contains(url_part))
        except TimeoutException:
            message = 'Url {} failed to contain {} within {} seconds'.format(self.current_url,
                                                                             url_part, timeout)
            raise PageLoadTimeoutException(message)

    def close(self):
        '''Close the browser session'''
        self._log.info('Closing the browser.')
        try:
            if hasattr(self, 'browser'):
                self.browser.quit()
        except UnexpectedAlertPresentException:
            self.alert().dismiss()
            self.close()

    def go_to(self, url):
        '''
        Go to a specific URL

        Args:
            url (str): This is the URL to which the driver should browse
        '''
        try:
            self._log.debug('Browsing to: ({url})'.format(**locals()))
            self.browser.get(url)
            self.wait_for_document_ready()
            self.optional_take_screenshot()
        except UnexpectedAlertPresentException:
            self.alert().dismiss()
            self.go_to(url)

    def get_cookies(self):
        '''All available cookies from the browser'''
        return self.browser.get_cookies()

    def add_cookie(self, domain=None, name=None, value=None,
                   expiry=None, path=None, secure=False):
        '''Add a cookie with the given attributes.'''

        cookie_dict = {'domain': domain or '',
                       'name': name or '',
                       'value': value or '',
                       'expiry': expiry or '',
                       'path': path or '',
                       'secure': secure}
        self._log.debug('Adding cookie: {cookie_dict}'.format(**locals()))
        self.browser.add_cookie(cookie_dict)

    def delete_cookie(self, name):
        '''Delete the cookie with the given name.'''
        self._log.debug('Removing cookie named: {name}'.format(**locals()))
        self.browser.delete_cookie(name)

    def alert_present(self):
        '''Is an alert/prompt/confirmation box present?

        Returns:
            bool: True if present, False otherwise.
        '''
        try:
            alert = self.browser.switch_to.alert
            alert.text
            return True
        except NoAlertPresentException:
            return False

    def alert(self):
        '''Create an Alert for the browser.

        Returns:
            Alert: the created Alert.
        '''
        return Alert(self.browser)
