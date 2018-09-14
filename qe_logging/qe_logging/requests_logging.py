'''
Logging for API testing with requests.

This module defines objects useful for logging calls made with the python requests library.
'''

try:
    # Python 3
    from inspect import signature as _signature
except ImportError:
    # Python 2
    from funcsigs import signature as _signature
import logging
from types import MethodType

import requests

from qecommon_tools import list_from
from qecommon_tools.http_helpers import is_status_code


DEFAULT_COMMAND = 'curl'


def curl_command_from(method=None, url=None, kwargs={}, exclude_params=[],
                      override_headers=None, skip_headers=None, command=DEFAULT_COMMAND):
    '''
    Creates a curl command string from the request items provided.

    Args:
        method (str): A valid requests method.
        url (str): A valid url.
        kwargs (dict): Keyword arguments for ``requests.models.PreparedRequest.prepare()``.
        exclude_params (list): If supplied will be excluded from the curl.  Note that this may
            make the curl invalid.
        override_headers (dict): Any matching keys in the ``kwargs['headers]`` will have their
            values replaced with the corresponding values in ``override_headers``.
        skip_headers (list): Excludes any matching keys and values in the ``kwargs['headers]`` from
            the curl.
        command (str):  The command to execute.  Defaults to ``default_command``

    Returns:
        str: the curl command
    '''
    return str(
        _RequestCurl(
            method=method,
            url=url,
            kwargs=kwargs,
            exclude_params=exclude_params,
            override_headers=override_headers,
            skip_headers=skip_headers,
            command=command
        )
    )


class _RequestCurl(object):
    default_include_params = ['command', 'method', 'headers', 'data', 'url']

    def __init__(self, method=None, url=None, kwargs=None, exclude_params=None,
                 override_headers=None, skip_headers=None, command=None):
        self.override_headers = override_headers or {}
        self.skip_headers = skip_headers or []
        self.command = command
        self._request = self._prepare_request(method, url, kwargs)
        self.include_params = [x for x in self.default_include_params if x not in exclude_params]

    def __repr__(self):
        '''Will return the full curl string.'''
        return ' '.join(
            filter(None, [getattr(self, '_{}_string'.format(x))() for x in self.include_params])
        )

    def _command_string(self):
        return self.command

    def _method_string(self):
        return {'GET': ''}.get(self._request.method, '-X {}'.format(self._request.method))

    def _single_header(self, key, value):
        if key in self.skip_headers:
            return ''
        value = self.override_headers.get(key, value)
        return '-H "{}: {}"'.format(key, value)

    def _headers_string(self):
        return ' '.join(
            filter(None, [self._single_header(k, v) for k, v in self._request.headers.items()])
        )

    def _data_string(self):
        request = self._request
        if not request.body:
            return ''
        body = request.body.decode('utf-8') if isinstance(request.body, bytes) else request.body
        return "-d '{}'".format(body)

    def _url_string(self):
        return '"{}"'.format(self._request.url)

    def _prepare_request(self, method, url, kwargs):
        '''
        Take the request information and transform it into a prepared_request obj.

        requests.models.PreparedRequest is used to ensure that the url, headers, and body match
        exactly what request is sending to the API.
        '''
        prepared_request = requests.models.PreparedRequest()
        sig = _signature(prepared_request.prepare)
        prepared_kwargs = {x: y for x, y in kwargs.items() if x in sig.parameters}
        prepared_request.prepare(method=method, url=url, **prepared_kwargs)
        return prepared_request


class RequestAndResponseLogger(object):
    '''
    A class that can be used to log request and response data from API calls.

    By default the entire request curl, response stats, response headers, and response content are
    logged.

    Args:
        logger (logging.getLogger): A logger to use to record data.  If not provided defaults to
            ``default_logger_name``.
        exclude_request_params (str, or list[str]): If supplied will be excluded from the logging
            in the curl for the request.
            Note that this may make the curl invalid.
        skip_headers (optional, list): These headers will be excluded from the logging
            in the curl for the request. Defaults to ``skip_headers``.
        override_headers (optional, dict): If supplied, headers present as keys in the dictionary
            will have their values replaced by the value in the dictionary
            in the curl for the request.

    Note: The individual logging methods are exposed for the convenience of subclassing.
    '''
    default_logger_name = 'QE_requests'
    skip_headers = ['Connection', 'Accept-Encoding', 'Accept', 'User-Agent', 'Content-Length']
    '''Common headers we find annoying in the logs.'''

    def __init__(self, logger=None, exclude_request_params=None, skip_headers=None,
                 override_headers=None):
        self.logger = logger or logging.getLogger(self.default_logger_name)
        self.exclude_request_params = list_from(exclude_request_params)
        self.skip_headers = self.skip_headers if skip_headers is None else skip_headers
        self.override_headers = {} if override_headers is None else override_headers

    def log_request(self, request_kwargs):
        '''
        The log a request using ``curl_command_from``; excludes parameters per the constructor.

        Args:
            request_kwargs (dict): A dictionary of keyword arguments for the API call to log.
        '''
        kwargs = {'exclude_params': self.exclude_request_params,
                  'skip_headers': self.skip_headers,
                  'override_headers': self.override_headers,
                  }
        kwargs.update(request_kwargs)
        self.logger.debug(curl_command_from(**kwargs))

    def log_response_status(self, response):
        '''Log the response's status code field.'''
        self.logger.debug('-->Response status:  {}'.format(response.status_code))

    def log_response_headers(self, response):
        '''Log the response's header field.'''
        self.logger.debug('-->Response headers: {}'.format(response.headers))

    def log_response_content(self, response):
        '''Log the the response content field'''
        self.logger.debug('-->Response content: {}'.format(response.content.decode('utf-8')))

    def log_response(self, response):
        '''
        Log the full response, status, header, contents.

        Args:
            response (requests.models.Response): A Response object for the API call to log.

        Uses the response log methods so that simple overrides of those don't require
        this method to be overridden as well.
        '''
        self.log_response_status(response)
        self.log_response_headers(response)
        self.log_response_content(response)

    def log(self, request_kwargs, response):
        '''
        Convenience function to log a request and response together.

        Args:
            request_kwargs (dict): Passed to ``log_request``, see that doc for info.
            response (requests.models.Repsonse): Passed to ``log_response``, see that doc for info.
        '''
        self.log_request(request_kwargs)
        self.log_response(response)


class IdentityLogger(RequestAndResponseLogger):
    '''
    For use with the Identity client.

    This will suppress the logging of the data header in the request
    and will only log the response data if there is an error.
    '''

    def __init__(self, logger=None):
        super(IdentityLogger, self).__init__(logger=logger, exclude_request_params='data')

    def log_response_content(self, response):
        '''Don't log anything unless there is an error; keep Identity secrets safe!'''
        if is_status_code('any error', response.status_code):
            super(IdentityLogger, self).log_response_content(response)
        else:
            self.logger.debug('-->Response content: <SUPPRESSED FOR SECURITY>')


class NoResponseContentLogger(RequestAndResponseLogger):
    '''
    For use when logging the response content is undesirable.
    '''

    def log_response_content(self, *args, **kwargs):
        '''Do not log any Response Content'''
        pass


class NoRequestDataNoResponseContentLogger(NoResponseContentLogger):
    '''
    For use when logging the request data and the response content is undesirable.
    '''

    def __init__(self, logger=None):
        super(NoRequestDataNoResponseContentLogger, self).__init__(
            logger=logger, exclude_request_params='data'
        )


class SilentLogger(RequestAndResponseLogger):
    '''
    For use when logging anything is undesirable.
    '''

    def __init__(self, *_, **__):
        # Accept, but ignore any parameters that are passed in.
        logger = logging.getLogger('No-op')
        # Silence the actual logger itself, this is done so that even any calls to the logger
        # attribute on an instance of this class would not log any data.
        logger.setLevel('CRITICAL')
        logger.critical = lambda *args, **kwargs: None
        super(SilentLogger, self).__init__(logger=logger)


class LastOnlyRequestAndResponseLogger(RequestAndResponseLogger):
    '''
    For use when logging only the last of a series of requests is desired.
    '''
    def __init__(self, *args, **kwargs):
        super(LastOnlyRequestAndResponseLogger, self).__init__(*args, **kwargs)
        self._last_log = None

    def log(self, request_kwargs, response):
        '''
        Holds the request_kwargs and response data provided.

        Keep track of the latest request/response to be logged, but don't actually log them until
        'done' is called.  In this way, this logger can be passed to any client and intermediate
        request/response '.log' calls will work, but the master puppet master can then call 'done'
        to log just the last request/response pair handled.

        Args:
            request_kwargs (dict): Eventually passed to ``RequestAndResponseLogger.log_request``,
                see that doc for info.
            response (requests.models.Response): Eventually passed to
                ``RequestAndResponseLogger.log_response``, see that doc for info.
        '''
        self._last_log = (request_kwargs, response)

    def done(self):
        '''
        Logs the last request / response data received by the ``log`` method.
        '''
        super(LastOnlyRequestAndResponseLogger, self).log(*self._last_log)
