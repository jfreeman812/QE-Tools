from copy import deepcopy
from itertools import product
import logging
from tempfile import mkdtemp

import pytest
from qecommon_tools import generate_random_string, get_file_contents
from qecommon_tools.assert_ import not_in
import requests
import requests_mock


from qe_logging import setup_logging
from qe_logging.requests_logging import (
    IdentityLogger,
    RequestAndResponseLogger,
    LastOnlyRequestAndResponseLogger,
    NoResponseContentLogger,
    NoRequestDataNoResponseContentLogger,
    SilentLogger,
)


###########################
# Reusable Response Mocks #
###########################


def single_item_random_dict():
    return {generate_random_string(): generate_random_string()}


# For identity logger checking:
SECRET_RESPONSE_VALUE = 'XYZZ'
BAD_SECRET_RESPONSE_DATA = 'Unauthorized: I cannot do that'


session = requests.Session()
adapter = requests_mock.Adapter()
session.mount('mock', adapter)


# NOTE:  This test will use single item dictionaries for headers / json data.  This will make
# verifying that these objects end up in the log file much easier.  It does not seem necessary to
# test more complex headers / json, as the code this is written to test does not mutate these
# objects.
adapter.register_uri(
    'GET',
    'mock://test.com/ok',
    status_code=200,
    headers=single_item_random_dict(),
    json=single_item_random_dict(),
)
adapter.register_uri(
    'POST',
    'mock://test.com/created',
    status_code=201,
    headers=single_item_random_dict(),
    json=single_item_random_dict(),
)
adapter.register_uri(
    'PUT',
    'mock://test.com/accepted',
    status_code=202,
    headers=single_item_random_dict(),
    json=single_item_random_dict(),
)
adapter.register_uri(
    'POST',
    'mock://test.com/secrets',
    status_code=202,
    headers=single_item_random_dict(),
    json={'reponse_data': 'There are SECRETS here: {}, ssshhh!'.format(SECRET_RESPONSE_VALUE)},
)
adapter.register_uri(
    'POST',
    'mock://test.com/bad-secrets',
    status_code=401,
    headers=single_item_random_dict(),
    json={'reponse_data': BAD_SECRET_RESPONSE_DATA},
)
adapter.register_uri(
    'PATCH',
    'mock://test.com/things-that-should-not-be-found',
    status_code=404,
    json=single_item_random_dict(),
)
adapter.register_uri(
    'DELETE',
    'mock://test.com/other-things-that-should-not-be-found',
    status_code=209,
    json=single_item_random_dict(),
)


def requests_to_test():
    return [
        {'url': 'mock://test.com/accepted', 'method': 'PUT'},
        {'url': 'mock://test.com/created', 'method': 'POST'},
    ]


def responses_to_test():
    return [
        session.get('mock://test.com/ok'),
        session.post('mock://test.com/created'),
        session.put('mock://test.com/accepted'),
    ]


def requests_that_should_not_be_logged():
    return [
        {'url': 'mock://test.com/things-that-should-not-be-found', 'method': 'PATCH'},
        {'url': 'mock://test.com/other-things-that-should-not-be-found', 'method': 'DELETE'},
    ]


def responses_that_should_not_be_logged():
    return [
        session.patch('mock://test.com/things-that-should-not-be-found'),
        session.delete('mock://test.com/other-things-that-should-not-be-found'),
    ]


ROOT_MSG = 'Log info:\n\n{}\n\n Did not contain '
ALTERNATE_LOGGER = logging.getLogger('custom_test_logger')


def _setup_logging():
    logging.getLogger().setLevel(logging.DEBUG)
    log_dir = mkdtemp()
    # Only one log file path is needed.  Testing that data is written to both log file paths is
    # covered in another test suite.  Taking the first file is arbitrary.
    return setup_logging('test_request_and_response_logger', base_log_dir=log_dir)[0]


def teardown_function():
    # Handlers must be cleared or they will cause interference with other tests.
    del logging.getLogger('').handlers[:]


def _setup_log_and_get_contents(req, resp, log_class=RequestAndResponseLogger, **init_kwargs):
    log_file = _setup_logging()
    log_class(**init_kwargs).log(req, resp)
    return get_file_contents(log_file)


def _resp_status_logged_as(response):
    # checking simply for the status_code in the log contents could result in false
    # negatives / positives, so checking for the entire string is necessary.
    return 'Response status:  {}'.format(response.status_code)


def _verify_request(test_request, log_contents):
    msg = '{}Request value '.format(ROOT_MSG.format(log_contents))

    for value in test_request.values():
        assert value in log_contents, '{}{}'.format(msg, value)


def _verify_response(test_resp, log_contents, resp_text=''):
    msg = '{}Response value '.format(ROOT_MSG.format(log_contents))

    for value in [_resp_status_logged_as(test_resp), str(test_resp.headers), resp_text]:
        assert value in log_contents, '{}{}'.format(msg, value)


@pytest.mark.parametrize('test_request,test_resp', product(requests_to_test(), responses_to_test()))
def test_request_and_response_are_logged(test_request, test_resp, **kwargs):
    log_contents = _setup_log_and_get_contents(test_request, test_resp, **kwargs)

    _verify_request(test_request, log_contents)
    _verify_response(test_resp, log_contents, resp_text=test_resp.text)

    return log_contents


@pytest.mark.parametrize(
    'logger_name,test_request,test_resp',
    product(
        [generate_random_string(), generate_random_string()],
        requests_to_test(),
        responses_to_test()
    )
)
def test_log_can_be_passed(logger_name, test_request, test_resp):
    log_contents = test_request_and_response_are_logged(
        test_request, test_resp, logger=logging.getLogger(logger_name)
    )
    msg = 'Log info:\n\n{}\n\n Did not contain logger name: {}'.format(log_contents, logger_name)
    assert logger_name in log_contents, msg


@pytest.mark.parametrize(
    'test_param,test_request,test_resp',
    product(['url', 'method'], requests_to_test(), responses_to_test())
)
def test_request_params_are_excluded(test_param, test_request, test_resp):
    log_contents = _setup_log_and_get_contents(
        test_request, test_resp, exclude_request_params=test_param
    )

    # make sure we don't mutate the original test data.
    test_request = deepcopy(test_request)
    # The request value is removed so we can verify the other request data is present in the log.
    excluded_value = test_request.pop(test_param)

    _verify_response(test_resp, log_contents, resp_text=test_resp.text)
    _verify_request(test_request, log_contents)

    msg = 'Log info:\n\n{}\n\n Contained an excluded parameter: {} with a value of: {}'.format(
        log_contents, test_param, excluded_value
    )
    assert excluded_value not in log_contents, msg


ALTERNATE_MSG = generate_random_string()


class AlternateRequestLogger(RequestAndResponseLogger):

    def __init__(self, **kwargs):
        super(AlternateRequestLogger, self).__init__(**kwargs)
        self.request_message = ALTERNATE_MSG

    def log_request(self, *args):
        ALTERNATE_LOGGER.debug(self.request_message)


class AlternateResponseLogger(RequestAndResponseLogger):

    def __init__(self, **kwargs):
        super(AlternateResponseLogger, self).__init__(**kwargs)
        self.response_message = ALTERNATE_MSG

    def log_response(self, *args):
        ALTERNATE_LOGGER.debug(self.response_message)


@pytest.mark.parametrize('test_request,test_resp', product(requests_to_test(), responses_to_test()))
def test_custom_request_logger(test_request, test_resp):
    log_contents = _setup_log_and_get_contents(
        test_request, test_resp, log_class=AlternateRequestLogger
    )

    _verify_response(test_resp, log_contents, resp_text=test_resp.text)

    # Verify request data isn't present.
    msg = 'Log info:\n\n{}\n\n Should not have contained Request data: '.format(log_contents)
    for value in test_request.values():
        assert value not in log_contents, '{}{}'.format(msg, value)

    # Verify our custom message is in the log data.
    msg = '{}custom request message {}'.format(ROOT_MSG.format(log_contents), ALTERNATE_MSG)
    assert ALTERNATE_MSG in log_contents, msg


@pytest.mark.parametrize('test_request,test_resp', product(requests_to_test(), responses_to_test()))
def test_custom_response_logger(test_request, test_resp):
    log_contents = _setup_log_and_get_contents(
        test_request, test_resp, log_class=AlternateResponseLogger
    )

    _verify_request(test_request, log_contents)

    # Verify response data isn't present.
    msg = 'Log info:\n\n{}\n\n Should not have contained Request data: '.format(log_contents)
    for value in [_resp_status_logged_as(test_resp), str(test_resp.headers), test_resp.text]:
        assert value not in log_contents, '{}{}'.format(msg, value)

    # Verify our custom message is in the log data.
    msg = '{}custom request message {}'.format(ROOT_MSG.format(log_contents), ALTERNATE_MSG)
    assert ALTERNATE_MSG in log_contents, msg


@pytest.mark.parametrize('log_class', [RequestAndResponseLogger, IdentityLogger])
def test_identity_secrets_are_safe_with_identity_logger(log_class):
    # We have other tests that check nitty gritty logging details,
    # so this test is simpler, do secrets show up in the log files (regular logger),
    # or not (IdentityLogger).
    request_secret = 'MY_SECRET_HERE'
    request = {'url': 'mock://test.com/secrets', 'method': 'POST',
               'kwargs': {'data': {'username': 'UserName', 'password': request_secret}}}
    response = session.post('mock://test.com/secrets')

    log_contents = _setup_log_and_get_contents(request, response, log_class=log_class)
    if log_class == IdentityLogger:
        assert request_secret not in log_contents
        assert SECRET_RESPONSE_VALUE not in log_contents
    else:
        assert request_secret in log_contents
        assert SECRET_RESPONSE_VALUE in log_contents


def test_identity_logger_log_response_when_response_has_errors():
    request = {'url': 'mock://test.com/bad-secrets', 'method': 'POST'}
    response = session.post('mock://test.com/bad-secrets')

    log_contents = _setup_log_and_get_contents(request, response, log_class=IdentityLogger)
    assert BAD_SECRET_RESPONSE_DATA in log_contents


@pytest.mark.parametrize('test_request,test_resp', product(requests_to_test(), responses_to_test()))
def test_no_response_content_logger(test_request, test_resp):
    log_contents = _setup_log_and_get_contents(
        test_request, test_resp, log_class=NoResponseContentLogger
    )

    _verify_request(test_request, log_contents)
    _verify_response(test_resp, log_contents)

    not_in(test_resp.text, log_contents, msg='Value should not have been logged. ')


@pytest.mark.parametrize('test_request,test_resp', product(requests_to_test(), responses_to_test()))
def test_no_request_data_no_response_content_logger(test_request, test_resp):
    # make sure we don't mutate the original test data.
    test_request = deepcopy(test_request)

    test_request['kwargs'] = {'data': single_item_random_dict()}
    log_contents = _setup_log_and_get_contents(
        test_request, test_resp, log_class=NoRequestDataNoResponseContentLogger
    )

    request_data = test_request.pop('kwargs')['data']
    _verify_request(test_request, log_contents)
    _verify_response(test_resp, log_contents)

    for value in [test_resp.text, str(request_data)]:
        not_in(value, log_contents, msg='Value should not have been logged. ')


@pytest.mark.parametrize('test_request,test_resp', product(requests_to_test(), responses_to_test()))
def test_silent_logger_does_not_log_requests_or_responses(test_request, test_resp):
    log_contents = _setup_log_and_get_contents(
        test_request, test_resp, log_class=SilentLogger
    )

    assert not log_contents, 'Log info found when None was expected:\n\n{}'.format(log_contents)


@pytest.mark.parametrize(
    'found_before,found_after,not_found',
    [[generate_random_string() for _ in range(3)] for _ in range(2)]
)
def test_silent_logger_does_not_log_external_calls(found_before, found_after, not_found):
    log_file = _setup_logging()
    test_logger = logging.getLogger('test logger')
    test_logger.debug(found_before)

    SilentLogger(logger=test_logger).logger.debug(not_found)
    test_logger.debug(found_after)

    with open(log_file, 'r') as f:
        log_contents = f.read()

    not_in(not_found, log_contents, msg='Value should not have been logged. ')

    msg = '{}Logged value '.format(ROOT_MSG.format(log_contents))
    for value in [found_before, found_after]:
        assert value in log_contents, '{}{}'.format(msg, value)


@pytest.mark.parametrize('test_request,test_resp', product(requests_to_test(), responses_to_test()))
def test_last_only_logger(test_request, test_resp):
    log_file = _setup_logging()
    last_only_logger = LastOnlyRequestAndResponseLogger()
    requests_and_responses_that_should_not_be_logged = list(product(
        requests_that_should_not_be_logged(), responses_that_should_not_be_logged()
    ))

    for request_data, response in requests_and_responses_that_should_not_be_logged:
        last_only_logger.log(request_data, response)
    last_only_logger.log(test_request, test_resp)
    last_only_logger.done()

    log_contents = get_file_contents(log_file)
    _verify_request(test_request, log_contents)
    _verify_response(test_resp, log_contents)

    for request_data, response in requests_and_responses_that_should_not_be_logged:
        for value in [response.text, request_data['url'], request_data['method']]:
            not_in(value, log_contents, msg='Value should not have been logged. ')
