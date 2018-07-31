from collections import namedtuple
import logging
from tempfile import mkdtemp
import warnings

try:
    from urllib.parse import urljoin
except ImportError:
    from urlparse import urljoin

import pytest
from requests.exceptions import MissingSchema
import requests_mock

from qecommon_tools import generate_random_string, get_file_contents
from qe_logging import setup_logging
from qe_logging.requests_client_logging import QERequestsLoggingClient  # Legacy Client
from qe_logging.requests_client_logging import (RequestsLoggingClient,
                                                XAuthTokenRequestsLoggingClient,
                                                BasicAuthRequestsLoggingClient)
from qe_logging.requests_logging import RequestAndResponseLogger


# Suppress warnings while we are still testing QERequestsLoggingClient
warnings.filterwarnings('ignore', '.*QERequestsLoggingClient.*')


def teardown_function():
    # Handlers must be cleared or they will cause interference with other tests.
    del logging.getLogger('').handlers[:]


class NoLogging(RequestAndResponseLogger):
    '''Fill the role, but suppress all logging.'''

    def log_request(self, *args, **kwargs):
        pass

    def log_response(self, *args, **kwargs):
        pass


MOCK_SCHEME = 'file'  # Only some schemes work because urljoin is finicky
MOCK_BASE = '{}://test.com/'.format(MOCK_SCHEME)

RequestItem = namedtuple('RequestItem', 'url method status_code text')
REQUESTS_TO_TEST = [
    RequestItem(url='ok', method='GET', status_code=200, text=generate_random_string()),
    RequestItem(url='accepted', method='PUT', status_code=201, text=generate_random_string()),
    RequestItem(url='created', method='POST', status_code=202, text=generate_random_string()),
]

TOKEN = '123abc'
USERNAME = 'qetools'
PASSWORD = 'qetools-password'

CLIENTS_TO_TEST = [
    {
        'client_class': QERequestsLoggingClient,  # Legacy Client
        'kwargs': {}
    },
    {
        'client_class': RequestsLoggingClient,
        'kwargs': {}
    },
    {
        'client_class': XAuthTokenRequestsLoggingClient,
        'kwargs': {'token': TOKEN}
    },
    {
        'client_class': BasicAuthRequestsLoggingClient,
        'kwargs': {'username': USERNAME, 'password': PASSWORD}
    }
]

_clients_and_requests_combinations = []
for client_info in CLIENTS_TO_TEST:
    for request_to_test in REQUESTS_TO_TEST:
        _clients_and_requests_combinations.append(
            (client_info['client_class'], client_info['kwargs'], request_to_test))


def _make_session(client_class, client_class_kwargs, with_logger=RequestAndResponseLogger,
                  base_url=MOCK_BASE):
    '''Create a logging client with the given parameters, and set up it for mocking'''
    session = client_class(curl_logger=with_logger, base_url=base_url, **client_class_kwargs)
    adapter = requests_mock.Adapter()
    session.mount(MOCK_SCHEME, adapter)

    for item in REQUESTS_TO_TEST:
        adapter.register_uri(item.method, urljoin(MOCK_BASE, item.url),
                             status_code=item.status_code, text=item.text)

    return session


def _setup_logging():
    logging.getLogger().setLevel(logging.DEBUG)
    log_dir = mkdtemp()
    # Only one log file path is needed.  Testing that data is written to both log file paths is
    # covered in another test suite.  Taking the first file is arbitrary.
    return setup_logging('test_request_client_logger', base_log_dir=log_dir)[0]


def assert_in(part, whole, prefix):
    assert part in whole, "{} '{}' not in '{}'".format(prefix, part, whole)


def assert_not_in(part, whole, prefix):
    assert part not in whole, "{} '{}' should not have been in '{}'".format(prefix, part, whole)


def _make_request(client_class, client_class_kwargs, request_item, log_message=None,
                  url_prefix=None, **kwargs):
    '''Make a request and return the log file contents and meta-data about the request made'''
    log_file = _setup_logging()
    method = request_item.method.lower()
    url = request_item.url
    if url_prefix:
        url = urljoin(url_prefix, url)
    session = _make_session(client_class, client_class_kwargs, **kwargs)
    if log_message:
        session.log(log_message)
    session_method = getattr(session, method)
    outgoing_text = generate_random_string()
    response = session_method(url, data=outgoing_text)
    log_contents = get_file_contents(log_file)
    return log_contents, {'request URL': url,
                          'outgoing text': outgoing_text,
                          'status_code': str(response.status_code),
                          'response text': request_item.text,
                          }


@pytest.mark.parametrize('client_class, client_class_kwargs, request_item',
                         _clients_and_requests_combinations)
def test_logs_are_written(client_class, client_class_kwargs, request_item):
    '''The request client writes to the logs.

    Checking that the data makes it to the log in some form,
    we have other tests that cover the formatting in detail.
    '''
    log_contents, fields = _make_request(client_class, client_class_kwargs, request_item,
                                         log_message='logs are written')
    for field_name, value in fields.items():
        assert_in(value, log_contents, field_name)


@pytest.mark.parametrize('client_class, client_class_kwargs, request_item',
                         _clients_and_requests_combinations)
def test_logs_can_be_suppressed(client_class, client_class_kwargs, request_item):
    '''The request client logging can be suppressed.

    If both request and response can be suppressed, we believe they can
    be individually suppressed as well.
    This is making sure the basic pathways are covered.
    '''
    log_contents, _ = _make_request(client_class, client_class_kwargs, request_item,
                                    with_logger=NoLogging)
    assert log_contents == '', "Expected empty log, got '{}'".format(log_contents)


@pytest.mark.parametrize('client_class, client_class_kwargs, request_item',
                         _clients_and_requests_combinations)
def test_with_no_base_url(client_class, client_class_kwargs, request_item):
    '''The request will error out with partial URLs and no base to prefix.'''
    with pytest.raises(MissingSchema):
        _make_request(client_class, client_class_kwargs, request_item,
                      base_url=None, log_message='no base url')


@pytest.mark.parametrize('client_class, client_class_kwargs, request_item',
                         _clients_and_requests_combinations)
def test_base_url_override(client_class, client_class_kwargs, request_item):
    '''Individual requests full URLs can override a base_url setting.'''
    log_contents, fields = _make_request(client_class, client_class_kwargs, request_item,
                                         base_url='https://example.org',
                                         url_prefix=MOCK_BASE,
                                         log_message='url override')
    for field_name, value in fields.items():
        assert_in(value, log_contents, field_name)
