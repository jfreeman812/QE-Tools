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

import logging


class BaseSeleniumException(Exception):
    _log = logging.getLogger(__name__)

    def __init__(self, message):
        super(BaseSeleniumException, self).__init__(message)
        self.message = message
        self._log.error(self.message)


class UnknownBrowserException(BaseSeleniumException):
    '''Raised when the browser name is not known to modules in this package.'''
    pass


class InvalidSearchByException(BaseSeleniumException):
    '''Raised when a SearchBy value doesn't match a value from the ``constants`` module.'''
    pass


class InvalidSearchForException(BaseSeleniumException):
    '''Raised when a search for value is empty that shouldn't be.'''
    pass


class LocatorNotFoundException(BaseSeleniumException):
    pass


class PageLoadTimeoutException(BaseSeleniumException):
    def __init__(self, message='Page failed to load in the required time'):
        super(PageLoadTimeoutException, self).__init__(message)
