from itertools import product
from random import choice

import json
import pytest
from qecommon_tools import format_if, generate_random_string
from qe_logging.requests_logging import curl_command_from


# This is an arbitrary, but valid url, and is not contacted.
DEFAULT_URL = 'https://www.httpbin.org/'
DEFAULT_METHOD = 'POST'
METHODS_TO_TEST = [DEFAULT_METHOD, 'GET', 'PUT', 'DELETE', 'PATCH']
EXPECTED_FOR_METHODS = {m: 'curl -X {}'.format(m) for m in METHODS_TO_TEST}
EXPECTED_FOR_METHODS['GET'] = 'curl'
URLS_TO_TEST = {method: ''.join([DEFAULT_URL, method]) for method in METHODS_TO_TEST}
DEFAULT_HEADERS = {'Content-Type': 'application/json'}
HEADERS_TO_TEST = [DEFAULT_HEADERS, {'Content-Type': 'application/json', 'HEADER 1': 'Value'}]
PAYLOADS_TO_TEST = [
    {},
    {'json': {}},
    {'json': None},
    {'json': {'a': '11'}},
    {'data': 'THIS IS A LINE OF TEXT\nTHIS IS ANOTHER LINE'},
]
PARAMS_TO_TEST = [
    {},
    {'a': 'b'},
    {'d': 'c'},
]


def _request_curl_with_defaults(**kwargs):
    kwargs['method'] = kwargs.get('method', DEFAULT_METHOD)
    kwargs['url'] = kwargs.get('url', DEFAULT_URL)
    return curl_command_from(**kwargs)


def _fmt_headers(key, value):
    return ' -H "{}: {}"'.format(key, value)


def _fmt_url(url):
    return ' "{}"'.format(url)


def _fmt_data(payload_data):
    json_value = payload_data.get('json')
    value = json.dumps(json_value) if json_value is not None else payload_data.get('data')
    return format_if(" -d '{}'", value)


@pytest.mark.parametrize('method,url_to_test', URLS_TO_TEST.items())
def test_urls_are_correct(method, url_to_test):
    curl = _request_curl_with_defaults(method=method, url=url_to_test)
    assert curl.endswith(_fmt_url(url_to_test))


@pytest.mark.parametrize('headers_to_test,method', product(HEADERS_TO_TEST, METHODS_TO_TEST))
def test_headers_are_correct(headers_to_test, method):
    curl = _request_curl_with_defaults(
        method=method, url=URLS_TO_TEST.get(method), kwargs={'headers': headers_to_test}
    )
    for key, value in headers_to_test.items():
        assert _fmt_headers(key, value) in curl


@pytest.mark.parametrize('headers_to_test', HEADERS_TO_TEST)
def test_override_headers(headers_to_test):
    value_to_find = generate_random_string()
    key_to_override = generate_random_string()
    value_to_not_find = generate_random_string()

    headers_to_test[key_to_override] = value_to_not_find
    curl = _request_curl_with_defaults(
        kwargs={'headers': headers_to_test}, override_headers={key_to_override: value_to_find}
    )

    assert value_to_find in curl
    assert value_to_not_find not in curl


@pytest.mark.parametrize('headers_to_test', HEADERS_TO_TEST)
def test_skip_headers(headers_to_test):
    key_to_skip = generate_random_string()
    headers_to_test[key_to_skip] = generate_random_string()

    curl = _request_curl_with_defaults(
        kwargs={'headers': headers_to_test}, skip_headers=[key_to_skip]
    )

    assert key_to_skip not in curl
    assert headers_to_test[key_to_skip] not in curl


@pytest.mark.parametrize('command_to_test', [generate_random_string(), generate_random_string()])
def test_command_is_used(command_to_test):
    curl = _request_curl_with_defaults(command=command_to_test)

    msg = 'curl {} did not start with {}'.format(curl, command_to_test)
    assert curl.startswith(command_to_test), msg


@pytest.mark.parametrize('test_param', ['command', 'method', 'headers', 'data', 'url'])
def test_exclude_params(test_param):
    # The GET method is not valid for testing the exclusion of a parameter, as it doesn't
    # actually appear in the curl, so there is no way to tell if it was purposefully excluded.
    valid_exclusion_test_methods = [x for x in METHODS_TO_TEST if x != 'GET']
    excluded_value = generate_random_string()
    data_to_test = {
        'headers': {'kwargs': {'headers': {excluded_value: excluded_value}}},
        'data': {'kwargs': {'data': {excluded_value: excluded_value}}},
        'method': {'method': choice(valid_exclusion_test_methods)},
        'url': {'url': '{}{}'.format(DEFAULT_URL, excluded_value)},
        'command': {'command': excluded_value}
    }

    kwargs = {'exclude_params': [test_param]}
    kwargs.update(data_to_test[test_param])
    curl = _request_curl_with_defaults(**kwargs)

    # the param 'method' is its own special snowflake. It can not be set to a truly random value,
    # and must be one of the valid test methods.
    excluded_value = data_to_test['method'].get(test_param, excluded_value)
    assert excluded_value not in curl


@pytest.mark.parametrize('method,params', product(METHODS_TO_TEST, PARAMS_TO_TEST))
def test_params_are_set(method, params):
    url = URLS_TO_TEST.get(method)
    curl = _request_curl_with_defaults(
        method=method, url=url, kwargs={'params': params}
    )
    for key, value in params.items():
        assert '{}={}'.format(key, value) in curl.split(url)[1]


@pytest.mark.parametrize('method,payload', product(METHODS_TO_TEST, PAYLOADS_TO_TEST))
def test_order_is_correct(method, payload):
    url = URLS_TO_TEST.get(method)
    payload['headers'] = DEFAULT_HEADERS
    curl = _request_curl_with_defaults(
        method=method, url=url, kwargs=payload
    )

    expected = EXPECTED_FOR_METHODS.get(method)
    assert curl.startswith(expected), '{} did not start with {}'.format(curl, expected)
    curl = curl.replace(expected, '')

    expected = ''.join([_fmt_headers(k, v) for k, v in DEFAULT_HEADERS.items()])
    assert curl.startswith(expected), '{} did not start with {}'.format(curl, expected)
    curl = curl.replace(expected, '')

    expected = _fmt_data(payload)
    assert curl.startswith(expected), '{} did not start with {}'.format(curl, expected)
    curl = curl.replace(expected, '')

    expected = _fmt_url(url)
    assert curl.startswith(expected), '{} did not start with {}'.format(curl, expected)
