from itertools import chain
import json

import requests


MAX_ERROR_MESSAGE_CONTENT_LENGTH = 500

HEADERS_TO_IGNORE_IN_ERROR_MESSAGE = [
    'Accept-Encoding',
    'Connection',
    'Content-Length',
    'User-Agent',
    'X-Auth-Token',
]

STATUS_CODE_RANGES = {
    'a successful response': (200, 300),
    'a client error': (400, 500),
    'a server error': (500, 600),
    'any error': (400, 600),
}


def _indent_items(*items):
    '''
    Adds a tab to every item in *items, if the item is a list, this function will be recursively
    called with the contents of that list, adding an additional tab stop.  Each additional nested
    list will result in an additional tab for every item in that additional list.
    Ex: *items = 'ex1', 'ex2', ['nested1', 'nested2', ['double1'], ['double2]], 'ex3' ->
    ['\tex1', '\tex2', '\t\tnested1', '\t\tnested2', '\t\t\tdouble1', '\t\t\tdouble2']
    '''
    return ['\t{}'.format(s)
            for x in items for s in chain(_indent_items(*x) if isinstance(x, list) else [x])]


def format_items_as_string_tree(*items):
    '''
    Formats the items provided as a string representing a "tree" format.  Any lists or nested lists
    will be flattened, with each level of nesting of lists, getting its own level of indentation.
    Each item once flattened with the appropriate level of indentation provided will be placed on
    its own line.
    Ex: items = 'ex1', 'ex2', ['nested1', 'nested2', ['double1'], ['double2]], 'ex3' ->
    >---ex1
    >---ex2
    >--->---nested1
    >--->---nested2
    >--->--->---double1
    >--->--->---double2
    >---ex3
    '''
    return '\n'.join(_indent_items(*items))


def _status_code_from(status_description):
    if isinstance(status_description, int):
        return status_description
    return requests.codes.get(status_description.replace(' ', '_').upper())


def is_status_code(expected_status_description, actual_status_code):
    '''
    Verifies that a given status code matches the expected result

    Args:
        expected_status_description (str, int): The result to match. Can be:
            - A Python requests libarary status reason ("OK")
            - A phrase matching a ``_status_code_ranges`` key ('a client error')
            - An integer for the response status code (404)
        actual_status_code (int): the status code from the response to be validated

    Returns:
        bool: True actual matches expected, False otherwise
    '''
    if expected_status_description in STATUS_CODE_RANGES:
        # a range descriptor was provided
        lower, upper = STATUS_CODE_RANGES[expected_status_description]
        return lower <= actual_status_code < upper

    # Convert description to code if not provided as code
    expected_code = _status_code_from(expected_status_description)
    message = 'Coding error, unknown status code check "{}"'.format(expected_status_description)
    assert expected_code, message
    return expected_code == actual_status_code


def create_error_message(summary_line, request, response_content, additional_info=None):
    '''
    Create a detailed error message based on an API call.
    This message will include information about the request and response,
    cutting off the response content at the set MAX_ERROR_MESSAGE_CONTENT_LENGTH.
    Additional information can be included in the message by including the
    ``additional_info`` parameter.

    Args:
        summary_line (str): The first line of the message that describes the error.
        request (Request): The python requests library Request.
        response_content (str): The response content to be included in the response.
        additional_info (dict): A dictionary containing additional information to be included in
            the message. The keys and values will be separated by a ":" in the message. (optional)

    Returns:
        str: The complete and detailed error message.
    '''
    headers = {header: value for header, value in request.headers.items()
               if header not in HEADERS_TO_IGNORE_IN_ERROR_MESSAGE}

    response_content = str(response_content)[:MAX_ERROR_MESSAGE_CONTENT_LENGTH]

    return format_items_as_string_tree(
        summary_line,
        ['Request Info:',
            [
                'Url: {}'.format(request.url),
                'HTTP Method: {}'.format(request.method),
                'Headers: {}'.format(headers),
                'Body: {}'.format(request.body)
            ]],
        ['{}: {}'.format(k, v) for k, v in additional_info.items()],
        ['Response Content: {}'.format(response_content)]
    )


def validate_response_status_code(expected_status_description, response):
    '''
    Assert that a response's status code matches an expected status code.

    Args:
        expected_status_description (str, int): The expected HTTP response status reason or code.
        response (Response): The python requests library response to validate.

    Raises:
        AssertionError: if the response status validation fails
    '''
    if not is_status_code(expected_status_description, response.status_code):
        try:
            response_content = json.dumps(response.json(), indent=4)
        except ValueError:
            response_content = response.content

        status_message = '{} - Actual Response Status: {}'
        err_msg = create_error_message(
            summary_line='The response status does not match the expected status.',
            request=response.request, response_content=response_content,
            additional_info={
                'Expected Status': status_message.format(expected_status_description,
                                                         response.status_code),
                'Reason': response.reason
            }
        )
        raise AssertionError(err_msg)
