from itertools import product
from random import choice

import json
import pytest
from qecommon_tools import format_if, generate_random_string
from qe_logging.requests_logging import curl_command_from


# This is an arbitrary, but valid url, and is not contacted.
DEFAULT_URL = 'https://www.httpbin.org/'
DEFAULT_METHOD = 'POST'


def _methods_to_test(exclude=''):
    return [x for x in [DEFAULT_METHOD, 'GET', 'PUT', 'DELETE', 'PATCH'] if x != exclude]


def _urls_to_test():
    # Joining the url with a random string to provide unique urls.  The number of urls to test
    # is simply an arbitrary number.
    return [DEFAULT_URL] + [''.join([DEFAULT_URL, generate_random_string()]) for _ in range(2)]


def _default_headers():
    return {'Content-Type': 'application/json'}


def _headers_to_test():
    return [
        _default_headers(),
        {'Content-Type': 'application/json', 'HEADER 1': 'Value'}
    ]


def _payloads_to_test():
    return [
        {},
        {'json': {}},
        {'json': None},
        {'json': {'a': '11'}},
        {'data': 'THIS IS A LINE OF TEXT\nTHIS IS ANOTHER LINE'},
    ]


def _params_to_test():
    return [
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


@pytest.mark.parametrize('url_to_test', _urls_to_test())
def test_urls_are_correct(url_to_test):
    curl = _request_curl_with_defaults(url=url_to_test)
    assert curl.endswith(_fmt_url(url_to_test))


@pytest.mark.parametrize('headers_to_test,method', product(_headers_to_test(), _methods_to_test()))
def test_headers_are_correct(headers_to_test, method):
    curl = _request_curl_with_defaults(method=method, kwargs={'headers': headers_to_test})
    for key, value in headers_to_test.items():
        assert _fmt_headers(key, value) in curl


@pytest.mark.parametrize('headers_to_test', _headers_to_test())
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


@pytest.mark.parametrize('headers_to_test', _headers_to_test())
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
    valid_exclusion_test_methods = _methods_to_test(exclude='GET')
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


@pytest.mark.parametrize('url,params', product(_urls_to_test(), _params_to_test()))
def test_params_are_set(url, params):
    curl = _request_curl_with_defaults(url=url, kwargs={'params': params})
    for key, value in params.items():
        assert '{}={}'.format(key, value) in curl.split(url)[1]


@pytest.mark.parametrize(
    'url,method,payload', product(_urls_to_test(), _methods_to_test(), _payloads_to_test())
)
def test_order_is_correct(url, method, payload):
    payload['headers'] = _default_headers()
    curl = _request_curl_with_defaults(
        method=method, url=url, kwargs=payload
    )

    expected = 'curl -X {}'.format(method) if method != 'GET' else 'curl'
    assert curl.startswith(expected), '{} did not start with {}'.format(curl, expected)
    curl = curl.replace(expected, '')

    expected = ''.join([_fmt_headers(k, v) for k, v in _default_headers().items()])
    assert curl.startswith(expected), '{} did not start with {}'.format(curl, expected)
    curl = curl.replace(expected, '')

    expected = _fmt_data(payload)
    assert curl.startswith(expected), '{} did not start with {}'.format(curl, expected)
    curl = curl.replace(expected, '')

    expected = _fmt_url(url)
    assert curl.startswith(expected), '{} did not start with {}'.format(curl, expected)
