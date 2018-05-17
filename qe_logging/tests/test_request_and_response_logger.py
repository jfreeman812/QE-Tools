from copy import deepcopy
from itertools import product
import logging
import os
from tempfile import mkdtemp

import pytest
from qecommon_tools import generate_random_string
import requests
import requests_mock


from qe_logging import setup_logging
from qe_logging.requests_logging import RequestAndResponseLogger


###########################
# Reusable Response Mocks #
###########################


def single_item_random_dict():
    return {generate_random_string(): generate_random_string()}


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


def _setup_log_and_get_contents(req, resp, **init_kwargs):
    log_file = _setup_logging()
    RequestAndResponseLogger(**init_kwargs).log_call(req, resp)
    with open(log_file, 'r') as f:
        return f.read()


def _resp_status_logged_as(response):
    # checking simply for the status_code in the log contents could result in false
    # negatives / positives, so checking for the entire string is necessary.
    return 'Response status:  {}'.format(response.status_code)


def _verify_request(test_request, log_contents):
    msg = '{}Request value '.format(ROOT_MSG.format(log_contents))

    for value in test_request.values():
        assert value in log_contents, '{}{}'.format(msg, value)


def _verify_response(test_resp, log_contents):
    msg = '{}Response value '.format(ROOT_MSG.format(log_contents))

    for value in [_resp_status_logged_as(test_resp), str(test_resp.headers), test_resp.text]:
        assert value in log_contents, '{}{}'.format(msg, value)


@pytest.mark.parametrize('test_request,test_resp', product(requests_to_test(), responses_to_test()))
def test_request_and_response_are_logged(test_request, test_resp, **kwargs):
    log_contents = _setup_log_and_get_contents(test_request, test_resp, **kwargs)

    _verify_request(test_request, log_contents)
    _verify_response(test_resp, log_contents)

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
        test_request, test_resp, log=logging.getLogger(logger_name)
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

    _verify_response(test_resp, log_contents)
    _verify_request(test_request, log_contents)

    msg = 'Log info:\n\n{}\n\n Contained an excluded parameter: {} with a value of: {}'.format(
        log_contents, test_param, excluded_value
    )
    assert excluded_value not in log_contents, msg


@pytest.mark.parametrize('test_request,test_resp', product(requests_to_test(), responses_to_test()))
def test_custom_request_logger(test_request, test_resp):
    alternate_msg = generate_random_string()
    log_contents = _setup_log_and_get_contents(
        test_request, test_resp, request_logger=lambda *_: ALTERNATE_LOGGER.debug(alternate_msg)
    )

    _verify_response(test_resp, log_contents)

    # Verify request data isn't present.
    msg = 'Log info:\n\n{}\n\n Should not have contained Request data: '.format(log_contents)
    for value in test_request.values():
        assert value not in log_contents, '{}{}'.format(msg, value)

    # Verify our custom message is in the log data.
    msg = '{}custom request message {}'.format(ROOT_MSG.format(log_contents), alternate_msg)
    assert alternate_msg in log_contents, msg


@pytest.mark.parametrize('test_request,test_resp', product(requests_to_test(), responses_to_test()))
def test_custom_response_logger(test_request, test_resp):
    alternate_msg = generate_random_string()
    log_contents = _setup_log_and_get_contents(
        test_request, test_resp, response_logger=lambda *_: ALTERNATE_LOGGER.debug(alternate_msg)
    )

    _verify_request(test_request, log_contents)

    # Verify response data isn't present.
    msg = 'Log info:\n\n{}\n\n Should not have contained Request data: '.format(log_contents)
    for value in [_resp_status_logged_as(test_resp), str(test_resp.headers), test_resp.text]:
        assert value not in log_contents, '{}{}'.format(msg, value)

    # Verify our custom message is in the log data.
    msg = '{}custom request message {}'.format(ROOT_MSG.format(log_contents), alternate_msg)
    assert alternate_msg in log_contents, msg
