from copy import deepcopy
from itertools import product
import logging
from tempfile import mkdtemp

try:
    from urllib.parse import urljoin
except ImportError:
    from urlparse import urljoin

import pytest
from qecommon_tools import generate_random_string, get_file_contents
from requests.exceptions import MissingSchema
import requests_mock


from qe_logging import setup_logging
from qe_logging.requests_client_logging import QERequestsLoggingClient
from qe_logging.requests_logging import RequestAndResponseLogger


class NoLogging(RequestAndResponseLogger):

    def log_request(self, *args, **kwargs):
        pass

    def log_response(self, *args, **kwargs):
        pass


MOCK_SCHEME = 'file'  # Only some schemes work because urljoin is finicky
MOCK_BASE = '{}://test.com/'.format(MOCK_SCHEME)

REQUESTS_TO_TEST = [
    {'url': 'ok',
     'method': 'GET',
     'status_code': 200,
     'text': generate_random_string()},
    {'url': 'accepted',
     'method': 'PUT',
     'status_code': 201,
     'text': generate_random_string()},
    {'url': 'created',
     'method': 'POST',
     'status_code': 202,
     'text': generate_random_string()},
]


def make_session(with_logger=RequestAndResponseLogger, base_url=MOCK_BASE):
    session = QERequestsLoggingClient(curl_logger=with_logger, base_url=base_url)
    adapter = requests_mock.Adapter()
    session.mount(MOCK_SCHEME, adapter)

    for item in REQUESTS_TO_TEST:
        adapter.register_uri(
            item['method'],
            urljoin(MOCK_BASE, item['url']),
            status_code=item['status_code'],
            text=item['text'])

    return session


def _setup_logging():
    logging.getLogger().setLevel(logging.DEBUG)
    log_dir = mkdtemp()
    # Only one log file path is needed.  Testing that data is written to both log file paths is
    # covered in another test suite.  Taking the first file is arbitrary.
    return setup_logging('test_request_client_logger', base_log_dir=log_dir)[0]


def teardown_function():
    # Handlers must be cleared or they will cause interference with other tests.
    del logging.getLogger('').handlers[:]


def assert_in(part, whole, message):
    assert part in whole, message.format(part, whole)


def assert_not_in(part, whole, message):
    assert part not in whole, message.format(part, whole)


@pytest.mark.parametrize('request_item', REQUESTS_TO_TEST)
def test_logs_written(request_item):
    log_file = _setup_logging()
    method = request_item['method'].lower()
    url = request_item['url']
    session = make_session()
    session_method = getattr(session, method)
    outgoing_text = generate_random_string()
    response = session_method(url, data=outgoing_text)
    log_contents = get_file_contents(log_file)
    assert_in(url, log_contents, "request URL '{}' not in '{}'")
    assert_in(outgoing_text, log_contents, "outgoing text '{}' not in '{}'")
    assert_in(str(response.status_code), log_contents, "status_code '{}' not in '{}'")
    assert_in(request_item['text'], log_contents, "reponse text '{}' not in '{}'")


@pytest.mark.parametrize('request_item', REQUESTS_TO_TEST)
def test_logs_no_response(request_item):
    log_file = _setup_logging()
    method = request_item['method'].lower()
    url = request_item['url']
    session = make_session(with_logger=NoLogging)
    session_method = getattr(session, method)
    outgoing_text = generate_random_string()
    response = session_method(url, data=outgoing_text)
    log_contents = get_file_contents(log_file)
    assert_not_in(url, log_contents, "request URL '{}' in '{}")
    assert_not_in(outgoing_text, log_contents, "outgoing text '{}' in '{}'")
    assert_not_in(str(response.status_code), log_contents, "status_code '{}' in '{}'")
    assert_not_in(request_item['text'], log_contents, "reponse text '{}' in '{}'")


@pytest.mark.parametrize('request_item', REQUESTS_TO_TEST)
def test_no_base_url(request_item):
    _setup_logging()
    method = request_item['method'].lower()
    url = request_item['url']
    session = make_session(base_url=None)
    session_method = getattr(session, method)
    outgoing_text = generate_random_string()
    with pytest.raises(MissingSchema):
        session_method(url, data=outgoing_text)


@pytest.mark.parametrize('request_item', REQUESTS_TO_TEST)
def test_override_base_url(request_item):
    log_file = _setup_logging()
    method = request_item['method'].lower()
    url = request_item['url']
    session = make_session(base_url=None)
    session_method = getattr(session, method)
    outgoing_text = generate_random_string()
    response = session_method(urljoin(MOCK_BASE, url), data=outgoing_text)
    log_contents = get_file_contents(log_file)
    assert_in(url, log_contents, "request URL '{}' not in '{}'")
    assert_in(outgoing_text, log_contents, "outgoing text '{}' not in '{}'")
    assert_in(str(response.status_code), log_contents, "status_code '{}' not in '{}'")
    assert_in(request_item['text'], log_contents, "reponse text '{}' not in '{}'")
