'''
.. inheritance-diagram:: qecommon_tools
   :parts: 1
'''

from __future__ import print_function
import ast
from collections import Iterable
import itertools as _itertools
import logging
import os as _os
import random
import shutil as _shutil
import string as _string
import subprocess as _subprocess
import sys as _sys
import time as _time

import requests as _requests
import wrapt as _wrapt


_debug = logging.getLogger(__name__).debug


class_lookup = {}
'''
This dictionary is to allow code that needs to have very late binding of a class
to look up the class here, and code that needs to control another module's use of a
late bound class to set it in this dictionary.

Code accessing this dictionary should use ``.get()`` with a default value so that
`this` module doesn't have to import lots of things here to set up all the defaults.
Code accessing this dictionary should publish which key(s) it will be using so that
modules wishing to retarget those classes will know which keys to set.

Code setting values in this dictionary so do so `before` importing modules that
will use that value. Setting values in this dictionary is only needed when the
default values need to be changed.

(Motivation: the requests client logging code needs to be able to use a custom
class instead of just ``requests.Session`` when being used by testing code
with the Locust test runner, and it uses this dictionary to accomplish this.)

'''


CHECK_UNTIL_TIMEOUT = 300
CHECK_UNTIL_CYCLE_SECS = 5


def no_op(*args, **kwargs):
    '''A reusable no-op function.'''
    pass


def always_true(*args, **kwargs):
    '''Always return True; ignores any combo of positional and keyword parameters.'''
    return True


def always_false(*args, **kwargs):
    '''Always return False; ignores any combo of positional and keyword parameters.'''
    return False


def identity(x, *args):
    '''
    A single parameter is returned as is, multiple parameters are returned as a tuple.

    From https://stackoverflow.com/questions/8748036/is-there-a-builtin-identity-function-in-python
    Not the top voted answer, but it handles both single and multiple parameters.
    '''
    return (x,) + args if args else x


def display_name(path, package_name=''):
    '''
    Create a human-readable name for a given project.

    Determine the display name for a project given a path and (optional) package name. If a
    display_name.txt file is found, the first line is returned. Otherwise, return a title-cased
    string from either the base directory or package_name (if provided).

    Args:
        path (str): Path for searching
        package_name (str): Sphinx-style, dot-delimited package name (optional)

    Returns:
        str: A display name for the provided path
    '''
    name_path = _os.path.join(path, 'display_name.txt')
    if _os.path.exists(name_path):
        with open(name_path, 'r') as name_fo:
            return name_fo.readline().rstrip('\r\n')
    raw_name = package_name.split('.')[-1] if package_name else _os.path.basename(path)
    return _string.capwords(raw_name.replace('_', ' '))


def format_if(format_str, content):
    '''
    Return a message string with a formatted value if any content value is present.

    Useful for error-checking scenarios where you want a prepared error message
    if failures are present (passed in via content), or no message if no failures.

    Args:
        format_str (str): A message string with a single format brace to be filled
        content (str): A value to be filled into the format_str if present

    Returns:
        str: either the format_str with content included if content present,
        or an empty string if no content.
    '''
    return format_str.format(content) if content else ''


def default_if_none(value, default):
    '''
    Return ``default if value is None else value``

    Use because:
      * no chance of the value stutter being mistyped, speeds up code reading time.
      * easier to read when value or default are complex expressions.
      * can save having to create local variable(s) to shorten the  ``if .. is None ...`` form.
    '''
    return default if value is None else value


def no_nones(iterable):
    '''Return a list of the non-None values in iterable'''
    return [x for x in iterable if x is not None]


def truths_from(iterable):
    '''Return a list of the truthy values in iterable'''
    return list(filter(None, iterable))


def padded_list(iterable, size, padding=None):
    '''
    Generate a fixed-length list from an iterable, padding as needed.

    Args:
        iterable (iterable): Any iterable that needs padding
        size (int): The length for the returned list
        padding: Any value that should be used to pad an iterable that is too short

    Returns:
        list: The iterable parameter converted to a list, up to size, padded as needed.
    '''
    return list(_itertools.islice(_itertools.chain(iterable, _itertools.repeat(padding)), size))


def _python_2_or_3_base_str_type():
    try:
        return basestring
    except NameError:
        return str


def list_from(item):
    '''
    Generate a list from a single item or an iterable.

    Any item that is "false-y", will result in an empty list. Strings and dictionaries will be
    treated as single items, and not iterable.

    Args:
        item: A single item or an iterable.

    Returns:
        list: A list from the item.

    Examples:
        >>> list_from(None)
        []
        >>> list_from('abcd')
        ['abcd']
        >>> list_from(1234)
        [1234]
        >>> list_from({'abcd': 1234})
        [{'abcd': 1234}]
        >>> list_from(['abcd', 1234])
        ['abcd', 1234]
        >>> list_from({'abcd', 1234})
        ['abcd', 1234]
    '''
    if not item:
        return []
    if isinstance(item, (_python_2_or_3_base_str_type(), dict)) or not isinstance(item, Iterable):
        return [item]
    return list(item)


def string_to_list(source, sep=',', maxsplit=-1, chars=None):
    '''``.split()`` a string into a list and ``.strip()`` each piece.

    For handling lists of things, from config files, etc.

    Args:
        source (str): the source string to process
        sep (str, optional): The ``.split`` ``sep`` (separator) to use.
        maxsplit (int, optional): The ``.split`` ``maxsplit`` parameter to use.
        chars (str, optional): The ``.strip`` ``chars`` parameter to use.
    '''
    return [item.strip(chars) for item in source.split(sep, maxsplit)]


def cleanup_and_exit(dir_name=None, status=0, message=None):
    '''
    Cleanup a directory tree that was created and exit.

    Args:
        dir_name (string): Full path to a directory to remove (optional)
        status (int): Exit code to use for exit (optional)
        message (string): Message to print to standard error (optional)
    '''
    if dir_name:
        _shutil.rmtree(dir_name)
    exit(status=status, message=message)


def safe_run(commands, cwd=None):
    '''
    Run the given list of commands, only return if no error.

    If there is an error in attempting or actually running the commands,
    error messages are printed to stdout and ``sys.exit()`` will be called.
    '''

    try:
        status = _subprocess.call(commands, cwd=cwd)
    except OSError as e:
        print('')
        print('Error when trying to execute: "{}"'.format(' '.join(commands)))
        print('')
        print(e)
        _sys.exit(-1)

    if status:
        print('')
        print('Error {} from running: "{}"'.format(status, ' '.join(commands)))
        print('')
        _sys.exit(status)


def exit(status=0, message=None):
    '''
    Exit the program and optionally print a message to standard error.

    Args:
        status (int): Exit code to use for exit (optional)
        message (string): Message to print to standard error (optional)
    '''
    if message:
        print(message, file=_sys.stderr)
    _sys.exit(status)


def error_if(check, status=None, message=''):
    '''
    Exit the program if a provided check is true.

    Exit the program if the check is true. If a status is provided, that code is used for the
    exit code; otherwise the value from the check is used. An optional message for standard
    error can also be provided.

    Args:
        check: Anything with truthiness that can determine if the program should exit or not
        status (int): Exit code to use for exit (optional)
        message (string): Message to print to standard error if check is True (optional)
    '''
    if check:
        exit(status=status or check, message=message.format(check))


def filter_dict(a_dict, keep_key=always_true, keep_value=always_true):
    '''
    Return a new dict based on keeping only those keys _and_ values whose function returns True.

    Args:
        a_dict (dict): A dictionary to filter values from.
        keep_key (function): Return True if the key is to be kept.
        keep_value (function): Return True if the value is to be kept.

    Returns:
        dict: A new dictionary with only the desired key, value pairs.
    '''
    return {k: v for k, v in a_dict.items() if keep_key(k) and keep_value(v)}


def dict_strip_value(a_dict, value=None):
    '''
    Return a new dict based on stripping out any key with the given value.

    Note:
        The default value ``None`` is chosen because it is a common case.
        Unlike other functions, value ``None`` is literally the value ``None``.

    Args:
        a_dict (dict): A dictionary to strip values from.
        value: Any value that should be stripped from the dictionary.

    Returns:
        dict: A new dictionary without key/value pairs for the given value.
    '''
    return filter_dict(a_dict, keep_value=lambda v: v != value)


def dict_transform(a_dict, key_transform=identity, value_transform=identity):
    '''
    Return a new dict based on transforming the keys and/or values of ``a_dict``.

    Args:
        a_dict (dict): the source dictionary to process
        key_transform (function): Takes an existing key and returns a new key to use.
        value_transform (function): Take an existing value and returns a new value to use.

    Returns:
        dict: A new dictionary with keys and values as transformed.
    '''
    return {key_transform(k): value_transform(v) for k, v in a_dict.items()}


def generate_random_string(prefix='', suffix='', size=8, choose_from=None):
    '''
    Generate a random string of the specified size.

    Args:
        prefix (str): The string to prepend to the beginning of the random string. (optional)
        suffix (str): The string to append to the end of the random string. (optional)
        size (int): The number of characters the random string should have. (defaults to 8)
        choose_from (str): A string containing the characters from which the randomness
            will be chosen. If not provided, it will choose from lowercase letters and digits.

    Returns:
        str: A randomly generated string.

    Raises:
        AssertionError: if the specified length is incompatible with prefix/suffix length

    Examples:
        >>> generate_random_string()
        'vng345jn'
        >>> generate_random_string(prefix='Lbs-', suffix='-test', size=15)
        'Lbs-js7eh9-test'
        >>> generate_random_string(prefix='Lbs-', size=15)
        'Lbs-js7eh98sfnk'
        >>> generate_random_string(suffix='-test', size=15)
        '8sdfjs7eh9-test'
        >>> generate_random_string(choose_from="aeiou")
        'uiiaueea'
    '''
    choose_from = default_if_none(choose_from, _string.ascii_lowercase + _string.digits)
    rand_string_length = size - len(prefix) - len(suffix)
    message = '"size" of {} too short with prefix {} and suffix {}!'
    assert rand_string_length > 0, message.format(size, prefix, suffix)
    rand_string = ''.join(random.choice(choose_from) for _ in range(rand_string_length))
    return '{}{}{}'.format(prefix, rand_string, suffix)


def index_or_default(a_list, value, default=-1):
    '''
    Return the index of a value from a list, or a default if not found.

    Args:
        a_list (list): A list from which to find the index
        value (any): the list item whose index is sought
        default (any): the value to return if the value is not in the list

    Returns:
        int,any: an index value (int) for the list item, or default value (any)
    '''
    return a_list.index(value) if value in a_list else default


def must_be_in_virtual_environment(
        exit_code=1,
        message='Must be running in a Python virtual environment, aborting!'):
    '''Exit with the given code and message if not running in a Python virtual environment'''
    if 'VIRTUAL_ENV' not in _os.environ:
        exit(exit_code, message)


def must_get_key(a_dict, key):
    '''
    Either return the value for the key, or raise an exception.

    The exception will indicate what the valid keys are.
    Inspired by Gherkin steps so that a typo in the Gherkin
    will result in a more helpful error message than the stock KeyError.

    Args:
        a_dict (dict): Dictionary with the values
        key (str): The key whose value is desired

    Returns:
        The value found on the key

    Raises:
        KeyError: if the given key is not present in the dictionary.
    '''
    if key not in a_dict:
        raise KeyError(
            '{} is not one of: {}'.format(key, ', '.join(sorted(map(str, a_dict))))
        )
    return a_dict[key]


def must_get_keys(a_dict, *keys):
    '''
    Either return the value found for the keys provided, or raise an exception.

    Args:
        a_dict (dict): Dictionary with the values
        keys (str): The key or keys whose value is desired

    Returns:
        The value found on the final key

    Raises:
        KeyError: if any of the given keys are not present in the dictionary.
    '''
    for key in keys:
        a_dict = must_get_key(a_dict, key)
    return a_dict


def var_from_env(var_name):
    '''
    Get an environment variable and raise an error if it is not set or has an empty value.

    Returns:
        str: The value of the environment variable.

    Raises:
        ValueError: if the variable name is not set or has an empty value.
    '''
    envvar = _os.environ.get(var_name)
    if not envvar:
        raise ValueError('"{}" variable not found!'.format(var_name))
    return envvar


def get_file_contents(*paths):
    '''
    Get the contents of a file as a Python string.

    Args:
        *paths: The path or paths that lead to the file whose contents are to be retrieved.

    Returns:
        str: The contents of the file.
    '''
    with open(_os.path.join(_os.path.join(*paths)), 'r') as f:
        return f.read()


def get_file_docstring(file_path):
    '''
    Get the full docstring of a given python file.

    Args:
        file_path (str): The path to the file whose docstring should
            be gathered and returned.

    Returns:
        str: The python file's docstring.
    '''
    tree = ast.parse(get_file_contents(file_path))
    return ast.get_docstring(tree)


def filter_lines(line_filter, lines, return_type=None):
    '''
    Filter the given lines based on the given filter function.

    This function by default will return the same type that it is given.
    If you'd like, you may return a different type by providing the
    ``return_type`` parameter.

    The expected values for the the ``lines`` parameter type and the
    ``return_type`` value are ``str`` and ``list``. Any other types/values
    may cause unexpected behavior.

    Args:
        line_filter (Callable): The callable function to be used to filter each line.
            It should take a single string parameter and return a boolean.
        lines (Union[str, List[str]]): Either a string with newline characters splitting
            the lines, or a list of lines as strings.
        return_type (type): The desired return type. If not provided, the type of the
            ``lines`` parameter will be used.

    Returns:
        Union[str, List[str]]: The filtered lines.
    '''
    if return_type is None:
        return_type = type(lines)

    if isinstance(lines, _python_2_or_3_base_str_type()):
        lines = lines.split('\n')

    filtered_lines = list(filter(line_filter, lines))
    return filtered_lines if return_type is list else '\n'.join(filtered_lines)


def fib_or_max(fib_number_index, max_number=None):
    '''The nth Fibonacci number or max_number, which ever is smaller.

    This can be used for retrying failed operations with progressively longer
    gaps between retries, cap'd at the max_number paraemter if given.
    '''
    current, next_ = 0, 1
    for _ in range(fib_number_index):
        current, next_ = next_, current + next_
        if max_number and current > max_number:
            return max_number
    return current


DEFAULT_MAX_RETRY_SLEEP = 30


def retry_on_exceptions(max_retry_count, exceptions, max_retry_sleep=DEFAULT_MAX_RETRY_SLEEP):
    '''
    A wrapper to retry a function max_retry_count times if any of the given exceptions are raised.

    In the event the exception/exceptions are raised, this code will sleep for ever increasing
    amounts of time (using the fibonacci sequence) but capping at max_retry_sleep seconds.

    Args:
        max_retry_count (int): The maximum number of retries, must be > 0..
        exceptions (exception or tuple of exceptions): The exceptions to catch and retry on.
        max_retry_sleep (int, float): The maximum amount of time to sleep between retries.
    '''
    assert exceptions, 'No exception(s) given'
    assert max_retry_count > 0, 'max_retry_count must be greater than 0'

    @_wrapt.decorator
    def wrapper(wrapped, instance, args, kwargs):
        error_count = 0
        while error_count <= max_retry_count:
            try:
                return wrapped(*args, **kwargs)
            except exceptions as e:
                error = e
                _debug('Retry on exception: "{}" encountered during call'.format(error))
                error_count += 1
                retry_sleep = fib_or_max(error_count, max_number=max_retry_sleep)
                _debug('...trying again after a sleep of {}'.format(retry_sleep))
                _time.sleep(retry_sleep)
        _debug('Retry on exception: Max Retry Count of {} Exceeded'.format(max_retry_count))
        raise error

    return wrapper


def check_until(
    function_call,
    keep_checking_validator,
    timeout=CHECK_UNTIL_TIMEOUT,
    cycle_secs=CHECK_UNTIL_CYCLE_SECS,
    fn_args=None,
    **fn_kwargs
):
    '''
    Args:
        function_call (function): The function to be called
        keep_checking_validator (function): a fn that will accept the output from function_call
            and return True if the call should continue repeating (still pending result),
            or False if the checked result is complete and may be returned.
        timeout (int): maximum number of seconds to "check until" before returning last result
        cycle_secs (int): frequency (in seconds) of checks (call every n seconds until...)
        fn_args (tuple, optional): tuple of positional args to be provided to function_call
        fn_kwargs (any): keyword args to be provided to function_call

    Returns:
        any: the eventual result of your function_call
            once the keep_checking_validator condition has been met
            or the timeout limit is exhausted.

    '''
    fn_args = fn_args or ()
    log = logging.getLogger('check_until')

    check_start = _time.time()
    log.debug('***logging response content of final call of loop only***')

    result = function_call(*fn_args, **fn_kwargs)
    end_time = _time.time() + timeout
    while keep_checking_validator(result) and _time.time() < end_time:
        _time.sleep(cycle_secs)
        result = function_call(*fn_args, **fn_kwargs)
    time_elapsed = round(_time.time() - check_start, 2)
    if keep_checking_validator(result):
        log.debug('Response was still pending at timeout.')
    log.debug('Final response achieved in {} seconds'.format(time_elapsed))
    return result


def only_item_of(item_sequence, label=''):
    '''Assert item_sequence has only one item, and return that item.'''
    label = label or item_sequence.__class__.__name__
    assert len(item_sequence) == 1, '{} was not of length 1: "{}"'.format(label, item_sequence)
    return item_sequence[0]


class NotEmptyList(list):
    '''
    A list that fails to iterate if it is empty.

    Iterating on this list will fail if the list is empty.
    This simplifies code from having to check for empty lists everywhere.
    Empty lists are a problem because ``for`` loop bodies don't execute on empyt lists.
    thus any checks/tests/etc in a loop body would not run.
    In a testing context, the loop would "succeed" by not doing anything
    (it would fail to have checked anything) and that would be a false-positive.
    '''

    @staticmethod
    def error_on_empty():
        '''Is called to return the error message when the NotEmptyList is empty.'''
        return 'list is empty!'

    def __iter__(self):
        '''
        Iterate only if not empty.

        Any loops that check items in the list could fail to fail for empty
        lists becuase the loop body would never execute.
        Help our clients by asserting if the list is empty so they don't have to.
        '''
        assert self, self.error_on_empty()
        return super(NotEmptyList, self).__iter__()


class CommonAttributeList(list):
    '''
    A list for similar objects that can be operated on as a group.

    Accessing an attribute on this list instead
    returns a list of that attribute's value from each member.
    (unless the attribute is defined here or in the base class)
    If any member of this list does not have that attribute, ``AttributeError`` is raised.

    Setting an attribute on this list instead sets the attribute on each member.
    '''

    def __getattr__(self, name):
        try:
            return [getattr(x, name) for x in self]
        except AttributeError:
            message = 'Attribute "{}" not present on all list items.'
            raise AttributeError(message.format(name))

    def __setattr__(self, name, value):
        '''On each item, set the give attribute to the given value'''
        for item in self:
            setattr(item, name, value)

    def update_all(self, **kwargs):
        '''On each item, set each key as an attribute to the corresponding value from kwargs.'''
        for key, value in kwargs.items():
            setattr(self, key, value)


class ResponseInfo(object):

    def __init__(self, response=None, description=None, response_callback=None,
                 response_data_extract=None, **kwargs):
        '''
        Keep track of needed info about test operation responses (or any info really).

        Originally created to augment/track info about ``requests'`` responses, it's not limited
        or bounded by that use case.
        Please read ``response`` more generally as any kind of object
        useful for catpuring some kind of response from the system under test.
        In addition, arbitrary other attributes can be set on this object.
        To make that easier, ``kwargs`` is processed as attribute / value pairs to be set on the
        object, for whatever attributes make sense for your application.

        Sometimes this object is keeping track of a response that is needed,
        but isn't available yet.
        In these cases, ``response_callback`` can be set to a parameter-less function that
        can be called to obtain the response when the ``response_data`` property is used.

        For ease of use, when the data is buried in the response or otherwise needs to be decoded,
        ``response_data_extract`` can be used. It should take one parameter (the response) and
        return the desired data from it. This function should not have any side-effects.
        ``response_data_extract`` is also used by the ``response_data`` property,
        see that property documentation for details.

        Args:
            response (any, optional): Whatever kind of response object you need to track.
            description (str, optional): Description (if any) of this particular response.
            response_callback (function w/no parameters, optional):
                A callback to use in place of the ``response`` field.
            response_data_extract (function w/1 parameter, optional):
                A callback used to extract wanted data from the response.
            kwargs (dict, optional): any additional attributes to set on this object,
                                     based on the name/value pairs in kwargs.
        '''

        super(ResponseInfo, self).__init__()

        self.response = response
        self.description = description
        self.response_callback = response_callback
        self.response_data_extract = response_data_extract
        for key, value in kwargs.items():
            setattr(self, key, value)

    def run_response_callback(self):
        '''Run the ``response_callback``, if any, and set ``response`` to the result.

        Set ``response_callback`` to None so iit isn't run more than once.
        '''
        if self.response_callback:
            self.response = self.response_callback()
            self.response_callback = None

    @property
    def response_data(self):
        '''Property that returns the data from a response:

        1. If ``response_callback`` is set, that is used to obtain the response,
           otherwise the ``response`` attribute is used.
           If the ``response_callback`` is called,
           it's result is assigned to the ``.response`` attribute and
           the ``response_callback`` attribute is set to None.
           This is to prevent the callback from being invoked more than once.
        2. If ``response_data_extract`` is set, it is called on the response
           from step 1, and it's return value is the value of this property.
           Otherwise the result of step 1 is returned as is.
           Note that in this step the ``.response`` attribute is not changed,
           the ``response_data_extract`` callback is expected to have no side-effects.
        '''
        self.run_response_callback()
        if self.response_data_extract:
            return self.response_data_extract(self.response)
        return self.response


class ResponseList(NotEmptyList, CommonAttributeList):
    '''A list specialized for testing, w/ResponseInfo object items.'''

    def set(self, resp):
        '''
        Clear and set the contents of this list to single object or an iterator of objects.

        Generators will be converted into a list to allow access more than once.

        This method can be handy/useful when transforming this list's contents
        from one form to another, such as:

        >>> x = CommonAttributeList()
        >>> ...
        >>> x.set(transform(thing, doo_dad) for thing in x)
        '''
        self[:] = list_from(resp)

    @property
    def single_item(self):
        '''Property - Assert this list has one item, and return that item.'''
        return only_item_of(self)

    def build_and_set(self, *args, **kwargs):
        '''Create ResponseInfo object with args & kwargs, then ``.set`` it on this ResponseList.'''
        self.set(ResponseInfo(*args, **kwargs))

    def run_response_callbacks(self):
        '''Call ``run_response_callback`` on each item of this ReponseList.'''
        for resp_info in self:
            resp_info.run_response_callback()
