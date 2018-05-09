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

import requests


class RequestCurl(object):
    '''
    Creates a curl command from the request items provided.

    As __repr__ will return the curl string, the object can be logged to record the curl.  The
    requests PreparedRequest model is used to be sure the values are formatted exactly as they would
    be sent to the API.

    Args:
        method (str): A valid requests method.
        url (str): A valid url.
        kwargs (dict): Keyword arguments for ``requests.models.PreparedRequest.prepare()``.
        exclude_params (list): If supplied will be excluded from the curl.  Note that this may
            make the curl invalid.
        override_headers (dict): Any matching keys in the ``kwargs['headers]`` will have their
            values replaced with the corresponding values in ``override_headers``. Defaults to
            ``RequestCurl.default_override_headers``.
        skip_headers (list): Excludes any matching keys and values in the ``kwargs['headers]`` from
            the curl. Defaults to ``RequestCurl.default_skip_headers``.
        command (str):  The command to execute.  Defaults to ``default_command``

    '''
    default_override_headers = {'X-Auth-Token': '$TOKEN'}
    default_skip_headers = [
        'Connection', 'Accept-Encoding', 'Accept', 'User-Agent', 'Content-Length'
    ]
    default_include_params = ['command', 'method', 'headers', 'data', 'url']
    default_command = 'curl'

    def __init__(self, method=None, url=None, kwargs={}, exclude_params=[],
                 override_headers=default_override_headers, skip_headers=default_skip_headers,
                 command=default_command):
        self.override_headers = override_headers
        self.skip_headers = skip_headers
        self.command=command
        self._request = self._prepare_request(method, url, kwargs)
        self.include_params = [x for x in self.default_include_params if x not in exclude_params]

    def __repr__(self):
        '''Will return the full curl string.'''
        return ' '.join(
            filter(None, [getattr(self, '_{}_string'.format(x))() for x in self.include_params])
        )

    def _command_string(self):
        '''Return the command part of the curl.'''
        return self.command

    def _method_string(self):
        '''Returns the method part of the curl.'''
        return {'GET': ''}.get(self._request.method, '-X {}'.format(self._request.method))

    def _single_header(self, key, value):
        '''Returns a single formatted pair of headers.'''
        if key in self.skip_headers:
            return ''
        value = self.override_headers.get(key, value)
        return '-H "{}: {}"'.format(key, value)

    def _headers_string(self):
        '''Returns the headers part of the curl.'''
        return ' '.join(
            filter(None, [self._single_header(k, v) for k, v in self._request.headers.items()])
        )

    def _data_string(self):
        '''Returns the data part of the curl.'''
        request = self._request
        if not request.body:
            return ''
        body = request.body.decode('utf-8') if isinstance(request.body, bytes) else request.body
        return "-d '{}'".format(body)

    def _url_string(self):
        '''Returns the url part of the curl.'''
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
