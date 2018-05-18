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


DEFAULT_OVERRIDE_HEADERS = {'X-Auth-Token': '$TOKEN'}
DEFAULT_SKIP_HEADERS = ['Connection', 'Accept-Encoding', 'Accept', 'User-Agent', 'Content-Length']
DEFAULT_COMMAND = 'curl'


def curl_command_from(method=None, url=None, kwargs={}, exclude_params=[],
                      override_headers=DEFAULT_OVERRIDE_HEADERS, skip_headers=DEFAULT_SKIP_HEADERS,
                      command=DEFAULT_COMMAND):
    '''
    Creates a curl command string from the request items provided.

    Args:
        method (str): A valid requests method.
        url (str): A valid url.
        kwargs (dict): Keyword arguments for ``requests.models.PreparedRequest.prepare()``.
        exclude_params (list): If supplied will be excluded from the curl.  Note that this may
            make the curl invalid.
        override_headers (dict): Any matching keys in the ``kwargs['headers]`` will have their
            values replaced with the corresponding values in ``override_headers``. Defaults to
            ``DEFAULT_OVERRIDE_HEADERS``.
        skip_headers (list): Excludes any matching keys and values in the ``kwargs['headers]`` from
            the curl. Defaults to ``DEFAULT_SKIP_HEADERS``.
        command (str):  The command to execute.  Defaults to ``default_command``

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
        self.override_headers = override_headers
        self.skip_headers = skip_headers
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
        request_logger (func): A function for logging request information, if provided it must
            take the following arguments:  ``self``, ``request_kwargs``.  Defaults to
            ``self._request_logger`` if not provided.
        response_logger (func): A function for logging response information, if provided it must
            take the following arguments:  ``self``, ``response``.  Defaults to
            ``self._response_logger`` if not provided.
        exclude_request_params (list): If supplied will be excluded from the request logging curl.
            Note that this may make the curl invalid.
    '''
    default_logger_name = 'QE_requests_logger'

    def __init__(self, logger=None, request_logger=None, response_logger=None,
                 exclude_request_params=None):
        self.logger = logger or logging.getLogger(self.default_logger_name)
        self.exclude_request_params = list_from(exclude_request_params)
        self.response_logger = self._methodtype_or_builtin(response_logger, self._response_logger)
        self.request_logger = self._methodtype_or_builtin(request_logger, self._request_logger)

    def _methodtype_or_builtin(self, input_param, builtin):
        return MethodType(input_param, self) if input_param else builtin

    def _request_logger(self, request_kwargs):
        kwargs = {'exclude_params': self.exclude_request_params}
        kwargs.update(request_kwargs)
        self.logger.debug(curl_command_from(**kwargs))

    def _log_response_status(self, response):
        self.logger.debug('-->Response status:  {}'.format(response.status_code))

    def _log_response_headers(self, response):
        self.logger.debug('-->Response headers: {}'.format(response.headers))

    def _log_response_content(self, response):
        self.logger.debug('-->Response content: {}'.format(response.content.decode('utf-8')))

    def _response_logger(self, response):
        self._log_response_status(response)
        self._log_response_headers(response)
        self._log_response_content(response)

    def log(self, request_kwargs, response):
        '''
        Logs the request / response data.

        Args:
            request_kwargs (dict): A dictionary of keyword arguments for the API call to log.
            response (requests.models.Response): A Response object for the API call to log.
        '''
        self.request_logger(request_kwargs)
        self.response_logger(response)
