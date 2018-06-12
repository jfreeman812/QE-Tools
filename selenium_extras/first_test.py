#! /usr/bin/env python

from selenium_extras.browser_config import (
    preferences_from_config_file, firefox_preferences, get_browser)
from selenium_extras.client import SeleniumClient

config_preferences = preferences_from_config_file('selenium_extras/selenium.config-sample',
                                                  'firefox')

fps = firefox_preferences(preference_settings=config_preferences)

b = get_browser('firefox', 20, preference_settings=fps)

c = SeleniumClient(b, 'https://www.example.org', 120, 60, './screenshots')

c.start()
print(c.title)
print(c.current_url)
print('Screenshot is: {}'.format(c.take_screenshot()))
