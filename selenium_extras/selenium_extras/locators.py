# Copyright 2016 Rackspace
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

'''
Locators are the bread and butter of this package's value add.

Locators exist for two reasons:

    #. To help with the problem of stale Selenium objects/elements
    #. To provide useful helper functions.


A Locator defines how to find an element/elements on a web page.
Only when the Locator is used (such as to click, clear text, etc) does
it get the underlying Selenium object to work with. This leaves a very
small chance that the Selenium object could be stale or out of date.
(If the web page is still be loaded or unloaded, then all bets are off
whether you use Locators or not.)
'''


import logging

from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC  # noqa N812
from selenium.webdriver.support.ui import Select as NativeSelectWrapper

from .constants import SEARCH
from .exceptions import (InvalidSearchByException,
                         InvalidSearchForException,
                         LocatorNotFoundException)


class Locator(object):
    _log = logging.getLogger(__name__)
    '''
    Base Locator class for this package.

    Every other 'locator' should inherit this.
    '''

    def __init__(self, driver, search_by, search_for):
        '''
        Every locator has a ``by``, and ``for`` to locate an item on a page.

        Args:
            search_by (str): How to find the item. See the SEARCH dictionary
                keys in the constants module for valid values.
            search_for (str): What to search for. Values depend on ``search_by``.
        '''
        if search_by not in SEARCH:
            raise InvalidSearchByException(('"{search_by}" is not a '
                                            'valid search_by method')
                                           .format(**locals()))

        if not search_for:
            raise InvalidSearchForException(('The search_for field cannot be '
                                             'empty'))
        self.driver = driver
        self.search_by = SEARCH[search_by]
        self.search_for = search_for
        self.locator_type = self.__class__.__name__
        super(Locator, self).__init__()

    def __str__(self):
        '''A human readable version of this locator.'''
        return ('<{self.locator_type}(search_by="{self.search_by}", '
                'search_for="{self.search_for}")>').format(**locals())

    def get_tuple(self):
        '''a tuple representation for this locator.'''
        return (self.search_by, self.search_for)

    def get_dict(self):
        '''a dictionary representing this locator.'''
        return {'search_by': self.search_by, 'search_for': self.search_for}

    def get_object(self):
        '''The webelement object found by this locator.

        Raises:
            LocatorNotFoundException: When the locator is not found.
        '''
        ret = self.find_one()
        if not ret:
            raise LocatorNotFoundException(("Couldn't find {}").format(self))
        return ret

    def scroll_to(self):
        '''Use Javascript to scroll to this locator.'''
        self.driver.javascript('window.scrollTo({x}, {y});'.format(**self.get_object().location))

    def wait_for_present(self, timeout=None):
        '''Wait for this locator to be present on the page.

        Args:
            timeout (int, optional): How long to wait for the locator to be present, in seconds.
                If None, the driver's page element timeout value is used.
        '''
        timeout = timeout or self.driver.page_element_timeout
        self._log.debug(('Waiting {timeout} for {self} '
                         'to be present').format(**locals()))
        WebDriverWait(self.driver.browser, timeout).until(
            EC.presence_of_element_located(self.get_tuple()))

    def wait_for_visible(self, timeout=None):
        '''Wait for this locator to be visible on the page.

        Args:
            timeout (int, optional): How long to wait for the locator to be visible, in seconds.
                If None, the driver's page element timeout value is used.
        '''
        timeout = timeout or self.driver.page_element_timeout
        self._log.debug(('Waiting {timeout} for {self} '
                         'to be visible').format(**locals()))
        return WebDriverWait(self.driver.browser, timeout).until(
            EC.visibility_of_element_located(self.get_tuple()))

    def wait_for_invisible(self, timeout=None):
        '''Wait for this locator to be invisible on the page.

        Args:
            timeout (int, optional): How long to wait for the locator to be invisible, in seconds.
                If None, the driver's page element timeout value is used.
        '''
        timeout = timeout or self.driver.page_element_timeout
        self._log.debug(('Waiting {timeout} for {self} '
                         'to be invisible').format(**locals()))
        WebDriverWait(self.driver.browser, timeout).until(
            EC.invisibility_of_element_located(self.get_tuple()))

    def wait_for_clickable(self, timeout=None):
        '''Wait for this locator to be clickable.

        Args:
            timeout (int, optional): How long to wait for the locator to be clickable, in seconds.
                If None, the driver's page element timeout value is used.
        '''
        timeout = timeout or self.driver.page_element_timeout
        self._log.debug(('Waiting {timeout} for {self} '
                         'to be clickable').format(**locals()))
        WebDriverWait(self.driver.browser, timeout).until(
            EC.element_to_be_clickable(self.get_tuple()))

    def is_present(self):
        '''Is this locator present?

        Returns:
            bool: True if present, False otherwise.
        '''
        self._log.debug('Checking if {self} is present'.format(**locals()))
        try:
            self.get_object()
            return True
        except LocatorNotFoundException:
            return False

    def assert_is_present(self, msg_prefix=''):
        '''assert, with a helpful message, that this locator is present.'''
        assert self.is_present(), '{} locator should have been present: {}'.format(
            msg_prefix, self)

    def assert_not_present(self, msg_prefix=''):
        '''assert, with a helpful message, that this locator isn't present.'''
        assert not self.is_present(), '{} locator should not have been present: {}'.format(
            msg_prefix, self)

    def is_visible(self):
        '''Is this locator visible?

        Returns:
            bool: True if visible, False otherwise.
        '''
        self._log.debug('Checking if {self} is visible'.format(**locals()))
        try:
            return self.get_object().is_displayed()
        except LocatorNotFoundException:
            return False

    def assert_is_visible(self, msg_prefix=''):
        '''assert, with a helpful message, that this locator is visible.'''
        assert self.is_visible(), '{} locator should have been visible: {}'.format(
            msg_prefix, self)

    def assert_not_visible(self, msg_prefix=''):
        '''assert, with a helpful message, that this locator isn't visible.'''
        assert not self.is_visible(), '{} locator should not have been visible: {}'.format(
            msg_prefix, self)

    def is_enabled(self):
        '''Is this locator enabled?

        Returns:
            bool: True if enabled, False otherwise.
        '''
        self._log.debug('Checking if {self} is enabled'.format(**locals()))
        try:
            return self.get_object().is_enabled()
        except LocatorNotFoundException:
            return False

    def assert_is_enabled(self, msg_prefix=''):
        '''assert, with a helpful message, that this locator is enabled.'''
        assert self.is_enabled(), '{} locator should have been enabled: {}'.format(
            msg_prefix, self)

    def assert_not_enabled(self, msg_prefix=''):
        '''assert, with a helpful message, that this locator is not enabled.'''
        assert not self.is_enabled(), '{} locator should not have been enabled: {}'.format(
            msg_prefix, self)

    def get_children(self, child_locator):
        '''All the children of the locator.

        Args:
            child_locator (Locator): Used to find the children of this locator.

        Yields:
            webdriver object: Each webobject of this locator matching ``child_locator``
        '''
        self._log.debug(('Returning children ("{child_locator}")'
                         'from {self}').format(**locals()))
        obj = self.get_object()
        for child in obj.find_elements(*child_locator.get_tuple()):
            yield child

    def get_attribute(self, attribute):
        '''The value of the given attribute of this locator's object.

        Args:
            attribute (str): The attribute name.

        Returns:
            str: The value of the attribute given.
        '''
        self._log.debug(('Getting attribute ({attribute}) from '
                         '{self}').format(**locals()))
        return self.get_object().get_attribute(attribute)

    def click(self):
        '''Click on the locator's object.'''
        self._log.debug('Clicking element: {self}'.format(**locals()))
        self.scroll_to()
        self.get_object().click()
        self.driver.optional_take_screenshot()

    def get_text(self):
        '''Return the text of the locator's object.'''
        self._log.debug(('Getting the text from: '
                         '{self}').format(**locals()))
        return self.get_object().text

    @property
    def text(self):
        '''Property convenience for getting locator's object's text.'''
        return self.get_text()

    def find_one(self):
        '''Find one Selenium element based on our own search by/for values.

        Returns:
            selenium web-element object: If found, if not found, False is returned.
        '''
        self._log.debug(('Searching for {self} - '
                         'on page "{self.driver.current_url}"').format(**locals()))
        try:
            return self.driver.browser.find_element(
                by=SEARCH[self.search_by], value=self.search_for)
        except NoSuchElementException:
            self._log.warn('Unable to locate element {} on page {}'.format(
                self, self.driver.current_url))
            return False

    def find_all(self):
        '''Find all the Selenium elements based on our own search buy/for values.

        Yields:
            selenium web-element object: each object found by the find_elements method.
        '''
        self._log.debug(('Searching for all {self} - '
                         'on page: "{self.driver.current_url}"').format(**locals()))
        try:
            for element in self.driver.browser.find_elements(by=SEARCH[self.search_by],
                                                             value=self.search_for):
                yield element
        except NoSuchElementException:
            self._log.warn('Unable to locate element {} on page {}'.format(
                self, self.driver.current_url))


class Button(Locator):
    '''Locator that can check if it is selected.'''

    def is_selected(self):
        '''
        Returns:
            bool: True if selected, False otherwise.
        '''
        self._log.debug(('Checking if {self} is '
                         'selected').format(**locals()))
        return self.get_object().is_selected()

    def assert_is_selected(self, msg_prefix=''):
        '''assert, with a helpful message, that this locator is selected.'''
        assert self.is_selected(), '{} locator should have been selected: {}'.format(
            msg_prefix, self)

    def assert_not_selected(self, msg_prefix=''):
        '''assert, with a helpful message, that this locator is not selected.'''
        assert not self.is_selected(), '{} locator should not have been selected: {}'.format(
            msg_prefix, self)


class TextField(Locator):
    '''Locator for manipulating text fields.'''

    def clear(self):
        '''Clear the text field.'''
        self._log.debug(('Clearing the {self} Text'
                         'Field').format(**locals()))
        self.get_object().clear()

    def send_keys(self, text):
        '''Enter the given text to the text box.

        Args:
            text (str): text to enter.
        '''
        self.scroll_to()
        self.clear()
        self.get_object().send_keys(text)
        self.driver.optional_take_screenshot()

    def enter(self, text):
        '''Alias for send_keys - backward compatibility.'''
        self.send_keys(text)


class Link(Locator):
    '''Link - Semantic name for a Locator.'''
    pass


class CheckBox(Button):
    '''CheckBox - Semantic name for a Locator.'''
    pass


class RadioButton(Button):
    '''RadioButton - Semantic name for a Locator.'''
    pass


class Row(Locator):
    '''Row - Semantic name for a Locator.'''


class Label(Locator):
    '''Label - Semantic name for a Locator,'''


class Select(Locator):
    '''Conveniece object for interacting with HTML selects.'''

    def choose(self, selection):
        '''
        Select one or many options from a select.

        Args:
            selection (str or list[str] or tuple[str]): The visible text or list/tuple of visible
                          texts of the select to be chosen. When list or tuple
                          then each value will be selected in turn (no delay) with
                          ``select_by_visible_text``, otherwise plain old ``select`` will be used.
        '''
        if isinstance(selection, (list, tuple)):
            select_obj = NativeSelectWrapper(self.get_object())
            for value in selection:
                select_obj.select_by_visible_text(value)
        else:
            NativeSelectWrapper(self.get_object()).select_by_visible_text(selection)
        self.driver.optional_take_screenshot()

    def get_options(self):
        '''Generator for options of this locator's object.

        Yields:
            The 'otions' elements for the given locator's object.
        '''
        obj = self.get_object()
        for option in obj.find_elements_by_tag_name('option'):
            yield option

    def choose_by_indexes(self, indexes):
        '''Choose one or many options from a select using indexes

        Args:
            indexes (list[int]): Index or list/tuple of indexes of options to be
                selected.  Note: option indexes start with 0
        '''
        select_obj = NativeSelectWrapper(self.get_object())
        if isinstance(indexes, (list, tuple)):
            for index_i in indexes:
                select_obj.select_by_index(index_i)
        else:
            select_obj.select_by_index(indexes)
        self.driver.optional_take_screenshot()

    def clear_all_selections(self):
        '''Clear all selections from a select.'''
        select_obj = NativeSelectWrapper(self.get_object())
        select_obj.deselect_all()
        self.driver.optional_take_screenshot()


class Table(Locator):
    '''Simple Table interactions.'''

    def get_rows(self, row_locator, search_text=None):
        '''Yield rows that are identified by the 'row_locator', and contain 'search_text' if given.

        Args:
            row_locator (Locator): The locator object for finding rows.
            search_text (str or None): the text to be searched for within each row.
                If None, then all rows found are returned.

        Yields:
            object: Selenium object/element for the rows found.
        '''
        for row in self.get_children(row_locator):
            if (search_text is None) or (search_text in row.text):
                yield row

    def get_row_count(self, row_locator=None, search_text=False):
        '''the number of rows found by ``get_rows`` with the same parameters.

        Args:
            row_locator (Locator): The locator object for finding rows.
            search_text (str, optional): text to be searched for within each row.
                Ir None, then all rows found are counted.

        Returns:
            int: the number of rows matching the criteria given.
        '''
        return len(list(self.get_rows(row_locator, search_text=search_text)))


class Form(object):
    '''Simple Form interactions.'''

    def __init__(self, fields, submit, field_order=None):
        '''
        Args:
            fields (dict): A dictionary of values defining the form elements.  The
                       key name is important, as it will become the reference
                       for submission.
            submit (Locator): the form submit locator.  It is separate from
                       the 'fields' parameter to force the developer to
                       consciously choose how the form will be sumitted.
            field_order (list[str], optional): The order in which the fields will be handled.
            If not supplied, the `.keys()` of 'fields' will be used.
        '''
        super(Form, self).__init__()
        self.form = fields
        self.form_submit = submit
        self.field_order = field_order or self.form.keys()

    def fill_and_submit(self, values):
        '''Fill out and then submit this form.

        Args:
            values (dict): values to be used to fill out the form.
                The keys of 'values' must match the keys from the init 'fields' param.
        '''
        self.fill(values)
        self.submit()

    def fill(self, values):
        '''Fill in the form with 'values'.

        Args:
            values (dict): Values to be used to fill out this form.
                The keys of 'values' must match the keys from the init 'fields' param.
        '''
        for key in self.field_order:
            field = self.form[key]
            if isinstance(field, TextField):
                field.enter(values[key])
            elif isinstance(field, Select):
                field.choose(values[key])
            elif isinstance(field, (Button, RadioButton, CheckBox)):
                field.click()

    def submit(self):
        '''Click the 'submit' locator provided in the '__init__' method.'''
        self.form_submit.click()
