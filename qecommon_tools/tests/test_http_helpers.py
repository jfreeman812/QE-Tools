import json

import pytest
from qecommon_tools import http_helpers
import requests
import requests_mock


###########################
# Reusable Response Mocks #
###########################


session = requests.Session()
adapter = requests_mock.Adapter()
session.mount('mock', adapter)

SAMPLE_DATA = {
    'key': 'value',
    'key2': ['list', 'of', 'values'],
    'data': [{'inside_key': 'inside_value'}, {'inside_key2': 'inside_value2'}]
}

adapter.register_uri('GET', 'mock://test.com/ok', status_code=200)
adapter.register_uri('GET', 'mock://test.com/client', status_code=400)
adapter.register_uri('GET', 'mock://test.com/server', status_code=500)
adapter.register_uri('GET', 'mock://test.com/good_json', status_code=200, json=SAMPLE_DATA)
adapter.register_uri(
    'GET',
    'mock://test.com/bad_json',
    status_code=200,
    text=json.dumps(SAMPLE_DATA).replace('}', ')')
)


@pytest.fixture
def ok_response():
    return session.get('mock://test.com/ok')


@pytest.fixture
def client_err():
    return session.get('mock://test.com/client')


@pytest.fixture
def server_err():
    return session.get('mock://test.com/server')


@pytest.fixture
def good_json():
    return session.get('mock://test.com/good_json')


@pytest.fixture
def bad_json():
    return session.get('mock://test.com/bad_json')


# data from response helpers testing
def test_invalid_json(bad_json):
    with pytest.raises(AssertionError):
        http_helpers.safe_json_from(bad_json)


def test_valid_json(good_json):
    data = http_helpers.safe_json_from(good_json)
    assert data == SAMPLE_DATA


def test_get_data(good_json):
    data = http_helpers.get_data_from_response(good_json, dig_layers=['data'])
    assert data == SAMPLE_DATA['data'][0]


def test_get_data_list(good_json):
    data = http_helpers.get_data_list(good_json, dig_layers=['data'])
    assert data == SAMPLE_DATA['data']


# format_items_as_string_tree testing
@pytest.fixture
def nested_list():
    return ['top', ['middle', ['lower', 'level']]]


@pytest.fixture
def string_tree():
    return '\t\ttop\n\t\t\tmiddle\n\t\t\t\tlower\n\t\t\t\tlevel'


def test_string_tree(string_tree, nested_list):
    assert http_helpers.format_items_as_string_tree(nested_list) == string_tree


# is_status_code testing
OK_DESC = ['OK', 200, 'a successful response']
GENERIC_ERROR_DESC = ['any error']
CLIENT_ERR_DESC = ['BAD_REQUEST', 'BAD', 400, 'a client error']
SERVER_ERR_DESC = ['INTERNAL_SERVER_ERROR', 'SERVER_ERROR', 500, 'a server error']
ALL_ERRORS = CLIENT_ERR_DESC + SERVER_ERR_DESC + GENERIC_ERROR_DESC


def _code_matches_expected(response, description):
    assert http_helpers.is_status_code(description, response.status_code)


def _code_mismatch_expected(response, description):
    assert not http_helpers.is_status_code(description, response.status_code)


@pytest.mark.parametrize('expected_description', OK_DESC)
def test_good_status_code(ok_response, expected_description):
    _code_matches_expected(ok_response, expected_description)


@pytest.mark.parametrize('expected_description', CLIENT_ERR_DESC + GENERIC_ERROR_DESC)
def test_client_err_code(client_err, expected_description):
    _code_matches_expected(client_err, expected_description)


@pytest.mark.parametrize('expected_description', SERVER_ERR_DESC + GENERIC_ERROR_DESC)
def test_server_err_code(server_err, expected_description):
    _code_matches_expected(server_err, expected_description)


@pytest.mark.parametrize('expected_description', ALL_ERRORS)
def test_ok_code_mismatch(ok_response, expected_description):
    _code_mismatch_expected(ok_response, expected_description)


@pytest.mark.parametrize('expected_description', OK_DESC + SERVER_ERR_DESC)
def test_client_err_mismatch(client_err, expected_description):
    _code_mismatch_expected(client_err, expected_description)


@pytest.mark.parametrize('expected_description', OK_DESC + CLIENT_ERR_DESC)
def test_server_client_err_mismatch(server_err, expected_description):
    _code_mismatch_expected(server_err, expected_description)


# create_error_message testing
@pytest.fixture
def expected_error_msg():
    return (
        '\tThe response status does not match the expected status\n'
        '\t\tRequest Info:\n'
        '\t\t\tUrl: mock://test.com/ok\n'
        '\t\t\tHTTP Method: GET\n'
        "\t\t\tHeaders: {'Accept': '*/*'}\n"
        '\t\t\tBody: None\n'
        '\t\tTest Message: this is a test message'
    )


@pytest.fixture
def expected_error_msg_without_additional_info():
    return (
        '\tThe response status does not match the expected status\n'
        '\t\tRequest Info:\n'
        '\t\t\tUrl: mock://test.com/ok\n'
        '\t\t\tHTTP Method: GET\n'
        "\t\t\tHeaders: {'Accept': '*/*'}\n"
        '\t\t\tBody: None'
    )


def test_create_error_msg(expected_error_msg, ok_response):
    created_msg = http_helpers.create_error_message(
        'The response status does not match the expected status',
        ok_response.request,
        ok_response.content,
        additional_info={'Test Message': 'this is a test message'}
    )
    # strip response content line as bytes-vs-str in py2/3 gets messy
    created_msg = '\n'.join(created_msg.split('\n')[:-1])
    assert created_msg == expected_error_msg


def test_create_error_msg_without_additional_info(expected_error_msg_without_additional_info,
                                                  ok_response):
    created_msg = http_helpers.create_error_message(
        'The response status does not match the expected status',
        ok_response.request,
        ok_response.content
    )
    # strip response content line as bytes-vs-str in py2/3 gets messy
    created_msg = '\n'.join(created_msg.split('\n')[:-1])
    assert created_msg == expected_error_msg_without_additional_info


@pytest.mark.parametrize('expected_description', ALL_ERRORS)
def test_validate_response_code(ok_response, expected_description):
    with pytest.raises(AssertionError):
        http_helpers.validate_response_status_code(expected_description, ok_response)


@pytest.mark.parametrize('expected_description', OK_DESC)
def test_validate_response_code_match(ok_response, expected_description):
    http_helpers.validate_response_status_code(expected_description, ok_response)
