from collections import namedtuple
import logging
import os
import shutil
from tempfile import mkdtemp
from uuid import uuid4
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


LOG_DIRS_TO_TEST = [mkdtemp(), mkdtemp(dir=os.getcwd()), str(uuid4())]

# Suppress warnings while we are still testing QERequestsLoggingClient

# Note that we can't say:
# "ignore:Warning: The QERequestsLoggingClient"
# because pytest will think "Warning" is a module name.
pytestmark = pytest.mark.filterwarnings('ignore:.*The QERequestsLoggingClient')


@pytest.fixture(scope='function', params=LOG_DIRS_TO_TEST)
def log_dir(request):
    yield request.param
    if os.path.exists(request.param):
        shutil.rmtree(request.param)


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

TOKEN = generate_random_string(prefix='token-', size=25)
USERNAME = generate_random_string(prefix='username-', size=25)
PASSWORD = generate_random_string(prefix='password', size=25)

OVERRIDE_TOKEN = generate_random_string(prefix='other-token-', size=25)
OVERRIDE_USERNAME = generate_random_string(prefix='other-username-', size=25)
OVERRIDE_PASSWORD = generate_random_string(prefix='other-password-', size=25)

X_AUTH_CLIENT_KWARGS = {'token': TOKEN}
BASIC_AUTH_CLIENT_KWARGS = {'username': USERNAME, 'password': PASSWORD}

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
        'kwargs': X_AUTH_CLIENT_KWARGS
    },
    {
        'client_class': BasicAuthRequestsLoggingClient,
        'kwargs': BASIC_AUTH_CLIENT_KWARGS
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


def _setup_logging(log_dir):
    root_log = logging.getLogger('')
    root_log.setLevel(logging.DEBUG)

    # If this function has already been called before in the current test,
    # just return the original first log file path.
    current_log_file_paths = [x.baseFilename for x in root_log.handlers
                              if isinstance(x, logging.FileHandler)]
    if current_log_file_paths:
        return current_log_file_paths[0]

    # Otherwise create one for the current test.
    # Only one log file path is needed.  Testing that data is written to both log file paths is
    # covered in another test suite.  Taking the first file is arbitrary.
    return setup_logging('test_request_client_logger', base_log_dir=log_dir)[0]


def assert_in(part, whole, prefix):
    assert part in whole, "{} '{}' not in '{}'".format(prefix, part, whole)


def assert_not_in(part, whole, prefix):
    assert part not in whole, "{} '{}' should not have been in '{}'".format(prefix, part, whole)


def _make_request(log_dir, session, request_item, log_message=None, url_prefix=None):
    '''Make a request and return the log contents, info about the request, and the response.'''
    log_file = _setup_logging(log_dir)
    method = request_item.method.lower()
    url = request_item.url

    if url_prefix:
        url = urljoin(url_prefix, url)

    if log_message:
        session.log(log_message)

    session_method = getattr(session, method)
    outgoing_text = generate_random_string()
    response = session_method(url, data=outgoing_text)

    log_contents = get_file_contents(log_file)
    fields = {
        'request URL': url,
        'outgoing text': outgoing_text,
        'status_code': str(response.status_code),
        'response text': request_item.text,
    }

    return log_contents, fields, response


def _get_x_auth_token_header(response):
    return response.request.headers['X-Auth-Token']


def _get_basic_auth_header(response):
    return response.request.headers['Authorization']


@pytest.mark.parametrize('client_class, client_class_kwargs, request_item',
                         _clients_and_requests_combinations)
def test_logs_are_written(log_dir, client_class, client_class_kwargs, request_item):
    '''The request client writes to the logs.

    Checking that the data makes it to the log in some form,
    we have other tests that cover the formatting in detail.
    '''
    session = _make_session(client_class, client_class_kwargs)
    log_contents, fields, _ = _make_request(log_dir, session, request_item,
                                            log_message='logs are written')
    for field_name, value in fields.items():
        assert_in(value, log_contents, field_name)


@pytest.mark.parametrize('client_class, client_class_kwargs, request_item',
                         _clients_and_requests_combinations)
def test_logs_can_be_suppressed(log_dir, client_class, client_class_kwargs, request_item):
    '''The request client logging can be suppressed.

    If both request and response can be suppressed, we believe they can
    be individually suppressed as well.
    This is making sure the basic pathways are covered.
    '''
    session = _make_session(client_class, client_class_kwargs, with_logger=NoLogging)
    log_contents, _, _ = _make_request(log_dir, session, request_item)
    assert log_contents == '', "Expected empty log, got '{}'".format(log_contents)


@pytest.mark.parametrize('client_class, client_class_kwargs, request_item',
                         _clients_and_requests_combinations)
def test_with_no_base_url(log_dir, client_class, client_class_kwargs, request_item):
    '''The request will error out with partial URLs and no base to prefix.'''
    session = _make_session(client_class, client_class_kwargs, base_url=None)
    with pytest.raises(MissingSchema):
        _make_request(log_dir, session, request_item, log_message='no base url')


@pytest.mark.parametrize('client_class, client_class_kwargs, request_item',
                         _clients_and_requests_combinations)
def test_base_url_override(log_dir, client_class, client_class_kwargs, request_item):
    '''Individual requests full URLs can override a base_url setting.'''
    session = _make_session(client_class, client_class_kwargs, base_url='https://example.org')
    log_contents, fields, _ = _make_request(log_dir, session, request_item,
                                            url_prefix=MOCK_BASE,
                                            log_message='url override')
    for field_name, value in fields.items():
        assert_in(value, log_contents, field_name)


@pytest.mark.parametrize('request_item', REQUESTS_TO_TEST)
def test_x_auth_token_client_includes_x_auth_token_in_request(log_dir, request_item):
    session = _make_session(XAuthTokenRequestsLoggingClient, X_AUTH_CLIENT_KWARGS)
    log_contents, _, response = _make_request(log_dir, session, request_item)
    assert 'X-Auth-Token' in response.request.headers
    assert _get_x_auth_token_header(response) == TOKEN
    assert 'X-Auth-Token' in log_contents
    assert TOKEN not in log_contents


@pytest.mark.parametrize('request_item', REQUESTS_TO_TEST)
def test_x_auth_token_client_with_no_auth_does_not_include_x_auth_token_in_request(log_dir,
                                                                                   request_item):
    session = _make_session(XAuthTokenRequestsLoggingClient, X_AUTH_CLIENT_KWARGS)
    with session.no_auth:
        log_contents, _, response = _make_request(log_dir, session, request_item)
    assert 'X-Auth-Token' not in response.request.headers
    assert 'X-Auth-Token' not in log_contents


@pytest.mark.parametrize('request_item', REQUESTS_TO_TEST)
def test_x_auth_token_client_can_use_overridden_authentication(log_dir, request_item):
    session = _make_session(XAuthTokenRequestsLoggingClient, X_AUTH_CLIENT_KWARGS)
    with session.this_auth(OVERRIDE_TOKEN):
        _, _, response = _make_request(log_dir, session, request_item)
    assert _get_x_auth_token_header(response) == OVERRIDE_TOKEN


@pytest.mark.parametrize('request_item', REQUESTS_TO_TEST)
def test_basic_auth_client_includes_basic_auth_in_request(log_dir, request_item):
    session = _make_session(BasicAuthRequestsLoggingClient, BASIC_AUTH_CLIENT_KWARGS)
    _, _, response = _make_request(log_dir, session, request_item)
    assert 'Authorization' in response.request.headers
    assert _get_basic_auth_header(response).startswith('Basic')


@pytest.mark.parametrize('request_item', REQUESTS_TO_TEST)
def test_basic_auth_client_with_no_auth_does_not_include_basic_auth_in_request(log_dir,
                                                                               request_item):
    session = _make_session(BasicAuthRequestsLoggingClient, BASIC_AUTH_CLIENT_KWARGS)
    with session.no_auth:
        _, _, response = _make_request(log_dir, session, request_item)
    assert 'Authorization' not in response.request.headers


@pytest.mark.parametrize('request_item', REQUESTS_TO_TEST)
def test_basic_auth_client_can_use_overridden_authentication(log_dir, request_item):
    session = _make_session(BasicAuthRequestsLoggingClient, BASIC_AUTH_CLIENT_KWARGS)

    with session.this_auth(OVERRIDE_USERNAME, OVERRIDE_PASSWORD):
        # First make sure that the _auth property is what is expected
        # since that is what gets passed into the request as the auth param.
        assert session._auth == (OVERRIDE_USERNAME, OVERRIDE_PASSWORD)
        _, _, override_response = _make_request(log_dir, session, request_item)

    # Then make a call with the original credentials
    # and make sure the auth values are different.
    _, _, response = _make_request(log_dir, session, request_item)
    assert _get_basic_auth_header(response) != _get_basic_auth_header(override_response)
