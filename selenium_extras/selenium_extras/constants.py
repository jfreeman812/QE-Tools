import os
from selenium.webdriver.common.by import By

DEFAULT_CONFIG_FILENAME = 'selenium.config'
SEARCH = {
    'class_name': By.CLASS_NAME,
    'class name': By.CLASS_NAME,
    'class': By.CLASS_NAME,
    'css_selector': By.CSS_SELECTOR,
    'css selector': By.CSS_SELECTOR,
    'css': By.CSS_SELECTOR,
    'id': By.ID,
    'link_text': By.LINK_TEXT,
    'link text': By.LINK_TEXT,
    'link_name': By.LINK_TEXT,
    'link name': By.LINK_TEXT,
    'name': By.NAME,
    'partial_link_text': By.PARTIAL_LINK_TEXT,
    'partial link text': By.PARTIAL_LINK_TEXT,
    'tag_name': By.TAG_NAME,
    'tag name': By.TAG_NAME,
    'tag': By.TAG_NAME,
    'xpath': By.XPATH
}
'''
Keys to this dictionary are convenience values used when creating
Locators or passing "by" values into to various helper functions
in this package.
'''

JAVASCRIPT_SCROLL = 'window.scrollTo({x}, {y});'
