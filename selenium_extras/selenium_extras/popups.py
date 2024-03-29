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


from selenium.common.exceptions import NoAlertPresentException


class JavascriptAlert(object):
    '''
    This is the base alert class.  All other popup classes will inherit
    from here.
    '''
    def __init__(self, driver):
        '''
        Every popup will need to use the driver object.

        Args:
            driver (SeleniumClient): The driver to use for the action.
        '''
        self.popup = driver.alert()

    def is_present(self):
        '''Is this popup present?'''
        try:
            if self.text:
                return True
        except NoAlertPresentException:
            return False

    def accept(self):
        '''Accepting the popup'''
        self.popup.accept()

    def dismiss(self):
        '''Dismiss the popup'''
        self.popup.dismiss()

    @property
    def text(self):
        '''Property: the text of the popup'''
        return self.popup.text


class JavascriptPrompt(JavascriptAlert):
    '''
    A prompt is able to accept text
    '''
    def enter(self, data):
        '''Enter text into a javascript prompt.

        Args:
            data (str): The data to enter in the prompt
        '''
        self.popup.send_keys(data)


class JavascriptConfirm(JavascriptAlert):
    '''Syntactic sugar for JavascriptAlter.'''
    pass
