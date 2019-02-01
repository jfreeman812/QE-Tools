from copy import copy
from itertools import chain
import json
import time

import requests


MAX_CALL_FAILURES = 5

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


def safe_json_from(response, description=''):
    '''
    Accepts a response object and attempts to return the JSON-decoded data.

    Args:
        response (requests.models.Response): a Response object from a requests call
        description (str, optional): details about the response expected.

    Returns:
        The JSON-decoded data from the response

    Raises:
        AssertionError: if the JSON data cannot be decoded properly.
    '''
    # the json module in py2 doesn't contain the specific error,
    # and instead throws a generic ValueError
    try:
        decode_error = json.decoder.JSONDecodeError
    except AttributeError:
        decode_error = ValueError
    try:
        data = response.json()
    except decode_error:
        content = list(filter(None, [description,
                                     'URL: {}'.format(response.url),
                                     'Status Code: {}'.format(response.status_code),
                                     'Response Text -{}-'.format(response.text)]))
        message = format_items_as_string_tree('\nResponse Content NOT a Valid JSON:', content)
        raise AssertionError(message)
    return data


def get_data_from_response(response, dig_layers=None, check_empty=True, first_only=True):
    '''
    Accepts a response object and returns a dict of the data contained within.

    Args:
        response (requests.models.Response): a Response object from a requests call
        dig_layers (list): A list of keys to "dig" down into the response before returning
        check_empty (bool): if True, raises an AssertionError if the payload is empty
        first_only (bool): strip the list wrapping the data and return the first result only

    Returns:
        The data payload.

    Examples:
        >>> response.json() == {"data": [{"key": "value"}, {"key": "value2"}], "other": ""}
        True
        >>>
        >>> get_data_from_response(response, dig_layers=['data'])
        {'key': 'value'}
        >>> get_data_from_response(response, dig_layers=['data'], first_only=False)
        [{'key': 'value'}, {'key': 'value2'}]
        >>> get_data_from_response(response, dig_layers=['other'])
        AssertionError: Payload was empty: ''
        >>> get_data_from_response(response, dig_layers=['other'], check_empty=False)
        ""
    '''
    # most common response is a 'list' of only one element, so first_only=True
    # will fix that by default, but allows a toggle to get full data if desired.
    data = safe_json_from(response)
    if isinstance(data, (int, str, bool)):
        return data
    dig_layers = dig_layers or []
    for layer in dig_layers:
        if layer in data:
            data = data[layer]
    if first_only and isinstance(data, list):
        data = data[0]
    if check_empty:
        assert data, 'Payload was empty: {}'.format(data)
    return data


def get_data_list(response, **kwargs):
    '''
    Get the full list of data from within a response, if the data is a list.

    Helper around get_data_for_response that returns the full list of data
    if the data is in a list format, rather than the default of returning
    the first object inside the list.

    For ``**kwargs`` values and more information, see :py:func:`get_data_from_response`.
    '''
    kwargs.update(first_only=False)
    return get_data_from_response(response, **kwargs)


def _indent_items(*items):
    '''
    Indent all items recursively.

    Adds a tab to every item in ``*items``. If the item is a list, this function
    will be recursively called with the contents of that list, adding an additional
    tab stop.  Each additional nested list will result in an additional tab for every
    item in that additional list.

    Returns:
        list: The items given, with all nested items having an added indent.

    Examples:
        >>>_indent_items('ex1', 'ex2', ['nested1', 'nested2', ['double1'], ['double2']], 'ex3')
        ['\tex1', '\tex2', '\t\tnested1', '\t\tnested2', '\t\t\tdouble1', '\t\t\tdouble2']
    '''
    return ['\t{}'.format(s)
            for x in items for s in chain(_indent_items(*x) if isinstance(x, list) else [x])]


def format_items_as_string_tree(*items):
    '''
    Format the items provided as a string representing a "tree" format.

    Any lists or nested lists will be flattened, with each level of nested lists
    getting its own level of indentation. Each item, once flattened with the
    appropriate level of indentation provided, will be placed on its own line.

    Returns:
        str: An indented "tree" format of the items.

    Example:
        >>> format_items_as_string_tree('ex1', 'ex2', ['nested1', 'nested2',
        >>>                             ['double1'], ['double2']], 'ex3')
            ex1
            ex2
                nested1
                nested2
                    double1
                    double2
            ex3
    '''
    return '\n'.join(_indent_items(*items))


def _status_code_from(status_description):
    if isinstance(status_description, int):
        return status_description
    return requests.codes.get(status_description.replace(' ', '_').upper())


def is_status_code(expected_status_description, actual_status_code):
    '''
    Determine if a given status code matches the expected result.

    Args:
        expected_status_description (str, int): The result to match. Can be:
            - A Python requests libarary status reason ("OK")
            - A phrase matching a ``_status_code_ranges`` key ('a client error')
            - An integer for the response status code (404)
        actual_status_code (int): the status code from the response to be validated

    Returns:
        bool: Whether or not the actual status code matches the expected status description.

    Raises:
        AssertionError: if an invalid ``expected_status_description`` value is provided.
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
    cutting off the response content at the set ``MAX_ERROR_MESSAGE_CONTENT_LENGTH``.
    Additional information can be included in the message by including the
    ``additional_info`` parameter.

    Args:
        summary_line (str): The first line of the message that describes the error.
        request (Request): The python requests library Request.
        response_content (str): The response content to be included in the response.
        additional_info (dict): A dictionary containing additional information to be
            included in the message. The keys and values will be separated by a
            ``":"`` in the message. (optional)

    Returns:
        str: The complete and detailed error message.
    '''
    if additional_info is None:
        additional_info = {}

    headers = {header: value for header, value in request.headers.items()
               if header not in HEADERS_TO_IGNORE_IN_ERROR_MESSAGE}

    response_content = str(response_content)[:MAX_ERROR_MESSAGE_CONTENT_LENGTH]
    request_body = str(request.body)[:MAX_ERROR_MESSAGE_CONTENT_LENGTH]

    return format_items_as_string_tree(
        summary_line,
        ['Request Info:',
            [
                'Url: {}'.format(request.url),
                'HTTP Method: {}'.format(request.method),
                'Headers: {}'.format(headers),
                'Body: {}'.format(request_body)
            ]],
        ['{}: {}'.format(k, v) for k, v in additional_info.items()],
        ['Response Content: {}'.format(response_content)]
    )


def check_response_status_code(expected_status_description, response, call_description=None,
                               additional_info=None):
    '''
    Checks that a response's status code matches an expected status description.

    Args:
        expected_status_description (str, int): The expected HTTP response status reason or code.
        response (Response): The python requests library response to validate.
        call_description (str): additional details about the call placed (optional)
        additional_info (dict): Additional Info to be passed to create_error_message

    Returns:
        str: Empty string if response status code matches, or a detailed error message otherwise
    '''
    if is_status_code(expected_status_description, response.status_code):
        return ''
    try:
        response_content = json.dumps(safe_json_from(response), indent=4)
    except AssertionError:
        response_content = response.content

    status_message = '{} - Actual Response Status: {}'
    info = {
        'Expected Status': status_message.format(
            expected_status_description, response.status_code
        ),
        'Reason': response.reason
    }
    info.update(additional_info or {})
    if call_description:
        info.update({'Call Description': call_description})
    err_msg = create_error_message(
        summary_line='The response status does not match the expected status.',
        request=response.request, response_content=response_content,
        additional_info=info
    )
    return err_msg


def validate_response_status_code(expected_status_description, response, err_prefix='', **kwargs):
    '''
    Assert that a response's status code matches an expected status code.

    Args:
        expected_status_description (str, int): The expected HTTP response status reason or code.
        response (Response): The python requests library response to validate.
        err_prefix (str): Prefix, if any, to the error message, when an assertion is raised.
        kwargs: additional keyword args to be passed on to check_response_status_code.

    Raises:
        AssertionError: if the response status validation fails
    '''
    err_msg = check_response_status_code(expected_status_description, response, **kwargs)
    if err_msg:
        raise AssertionError(err_prefix + err_msg)


def response_if_status_check(call_description, response, target_status='a successful response'):
    '''
    Validates a response matches the expected status code before returning.

    Args:
        call_description (str): Text description of the call placed (e.g. "get schedule list")
        response (requests.Response): the response object to validate.
        target_status (str, int): The expected HTTP response status reason or code.

    Returns:
        requests.Response: if the response status validation succeeds

    Raises:
        AssertionError: if the response status validation fails
    '''
    validate_response_status_code(
        target_status, response, call_description='Call to "{}" failed'.format(call_description)
    )
    return response


def check_until(
    client_call,
    data,
    keep_checking_validator,
    timeout,
    cycle_secs,
    curl_logger=None,
    retry=True,
    max_failures=MAX_CALL_FAILURES,
    **client_call_kwargs
):
    '''
    Helper to repeatedly try a REST client call until a validation condition is met.


    Args:
        client_call (function): a function call that will return a requests.Response object
        data (dict): a key-value pair(s) to be passed into the ``client_call`` as the main args,
            kept separate from client_call_kwargs to support easy comprehensions and loops
            with shared kwargs but multiple data entries.
        keep_checking_validator (function): a call that will accept a requests.Response
            and return True if the call should continue repeating (still pending),
            or False if the checked response is complete and may be returned.
        timeout (int): maximum number of seconds to "check until"
        cycle_secs (int): number of seconds per cycle (check every n seconds)
        curl_logger (cls,optional): if your client is
            an instance of ``qe_logging.RequestsLoggingClient``,
            you can pass in a member of ``qe_logging.RequestAndResponseLogger``
            that will be used to log the calls as well as entries from check_until,
            ``LastOnlyRequestAndResponseLogger`` is recommended.
        max_failures (int): the maximum number of allowed for failed retries
        client_call_kwargs: all other kwargs will be passed directly to the client call

    Returns:
        requests.Response: the eventual result of your client_call
            once the pending_validator condition has been met, or failure retries are exhausted.

    '''

    def _noop(*args, **kwargs):
        # No-op debug if no curl_logger passed in
        pass

    debug = _noop
    if curl_logger:
        # instantiate if not already
        curl_logger = curl_logger() if isinstance(curl_logger, type) else curl_logger
        debug = curl_logger.logger.debug

    check_start = time.time()
    debug('***logging response content of final call of loop only***')
    call_kwargs = copy(data)
    call_kwargs.update(client_call_kwargs)
    if curl_logger:
        call_kwargs.update(curl_logger=curl_logger)
    response = client_call(**call_kwargs)
    end_time = time.time() + timeout
    while keep_checking_validator(response) and time.time() < end_time:
        time.sleep(cycle_secs)
        response = client_call(**call_kwargs)
    time_elapsed = round(time.time() - check_start, 2)
    if keep_checking_validator(response):
        debug('Response was still pending at timeout.')
    debug('Final response achieved in {} seconds'.format(time_elapsed))
    if hasattr(curl_logger, 'done'):
        # This is a temporary workaround pending QET-129.
        curl_logger.done()
    return response
