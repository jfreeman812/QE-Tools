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

adapter.register_uri('GET', 'mock://test.com/ok', status_code=200)
adapter.register_uri('GET', 'mock://test.com/client', status_code=400)
adapter.register_uri('GET', 'mock://test.com/server', status_code=500)


@pytest.fixture
def ok_response():
    return session.get('mock://test.com/ok')


@pytest.fixture
def client_err():
    return session.get('mock://test.com/client')


@pytest.fixture
def server_err():
    return session.get('mock://test.com/server')


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
def server_client_err_mismatch(server_err, expected_description):
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


@pytest.mark.parametrize('expected_description', ALL_ERRORS)
def test_validate_response_code(ok_response, expected_description):
    with pytest.raises(AssertionError):
        http_helpers.validate_response_status_code(expected_description, ok_response)


@pytest.mark.parametrize('expected_description', OK_DESC)
def test_validate_response_code_match(ok_response, expected_description):
    http_helpers.validate_response_status_code(expected_description, ok_response)
