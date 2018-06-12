from contextlib import contextmanager

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.expected_conditions import staleness_of


class Page(object):
    '''Generic Selenium Page Object Model Base Class.

    Defines some useful behavior, to be overridden in a subclass as needed.
    '''

    def __init__(self, driver, url=None):
        '''
        set up the driver and optional URL.

        url is optional so that it can be set later.
        '''
        self.driver = driver
        self.url = url

    def go_to_and_wait(self):
        '''Go to the page and ``wait_until_loaded``.'''
        assert self.url, 'go_to called but no URL is defined!'
        self.driver.go_to(self.url)
        self.wait_until_loaded()

    def wait_until_loaded(self, timeout=None):
        '''Wait until this page has loaded. (Please override this method!)

        This is meant for clients to use instead of driver functions directly,
        so that subclasses can override it with page-specific logic as needed.
        The default implementation just calls the driver's ``wait_for_document_ready``
        which might work for simple pages, but really we expect this method to be
        overridden based on the specifics of specific pages (jQuery, etc).
        '''
        self.driver.wait_for_document_ready(timeout=timeout)

    # Adapted from Tommy Beadle's code from:
    # http://www.obeythetestinggoat.com/how-to-get-selenium-to-wait-for-page-load-after-a-click.html
    @contextmanager
    def wait_for_page_load_after_action(self, timeout=None, locator_to_go_stale=None):
        '''Wait for this page to load after contained actions are done. (Context Manager)

        ``locator_to_go_stale`` is a locator on the `current` page for an element that will go stale
        when the page is reloaded. When None, it will use the 'html' element (whole page).
        In the case where the action(s) only cause partial page loading, this parameter
        can be used.

        This is a four step process:

        #. find an object that will go stale indicating the `current` page is no longer valid.
        #. take actions in the body of the 'with'.
        #. wait for found object to go stale.
        #. wait for the page to load.

        The third step is used to make sure that the fourth step doesn't see the current page
        before the actions in step two cause the browser to change.

        NOTE: The object to go stale does `not` have to be on the same page as the one that
        this method is being called on.

        Simple Use::

            with some_page.wait_for_page_load_after_action():
                my_locator.click()

            # This will wait for the page to go stale after the button has been clicked.
            # and will then call ``some_page``'s ``wait_until_loaded`` method.
            # This is so that ``wait_until_loaded`` is not fooled by the old version of the page.

        '''
        if locator_to_go_stale:
            old_item = locator_to_go_stale.get_object()
        else:
            old_item = self.driver.browser.find_element_by_tag_name('html')
        yield
        timeout = timeout if timeout is not None else self.driver.page_element_timeout
        WebDriverWait(self.driver.browser, timeout).until(staleness_of(old_item))
        self.wait_until_loaded(timeout=timeout)
