'''
Human friendly logging of requests library request/response objects.

``QERequestsLoggingClient`` is a drop-in replacement for the
``requests.Session`` class that provides human-friendly logging,
default URL handling, and a ``.token`` property for the ``X-Auth-Token`` header.

This module uses ``class_lookup`` from ``qecommon_tools`` with the key
``requests.Session`` instead of hardcoding that class name, which is just the default
if no value set.  If you need to change the class used, update ``class_lookup``
`before` importing this module::

    from qecommon_tools import class_lookup

    class_lookup['requests.Session'] = myClassToUseInstead

    import qe_logging.requests_client_logging  # noqa  (comment is for flake8)
'''

import logging
try:
    from urllib.parse import quote, quote_plus, urljoin, urlsplit, urlunsplit
except ImportError:
    from urlparse import urljoin, urlsplit, urlunsplit
    from urllib import quote, quote_plus
import inspect
import sys

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

from qe_logging.requests_logging import RequestAndResponseLogger
from qecommon_tools import class_lookup, dict_strip_value


# Silence the requests urllib3 logger
logging.getLogger('urllib3.connectionpool').setLevel(logging.ERROR)
# Silence requests complaining about insecure connections; needed for our internal certificates
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


def _url_sanitize(url):
    if not url:
        return url

    if '://' not in url:
        return quote(url.encode('utf-8'))

    parts = urlsplit(url)
    return urlunsplit(
        (
            parts.scheme,
            parts.netloc,
            quote(parts.path),
            quote_plus(parts.query),
            quote(parts.fragment)
        )
    )


def _full_url(base_url, url=None):
    if not url:
        return base_url
    if not base_url:
        return url
    if not base_url.endswith('/'):
        base_url += '/'
    return urljoin(base_url, _url_sanitize(url))


class QERequestsLoggingClient(class_lookup.get('requests.Session', requests.Session)):
    _logger = logging.getLogger(__name__)

    base_url = None
    '''
    The base_url from the constructor is a public field, for inspection or update.
    '''

    def __init__(self, base_url=None, token=None, curl_logger=None,
                 content_type='application/json'):
        '''
        A logging client based on ``requests.Session``.


        Args:
            base_url (str, optional): Used as a prefix for all the request methods' URL parameters,
                so that client code does not need to constantly join.
                If a fully qualified URL is passed to a verb method instead, it will be used,
                overriding the join with this value. If this is not set,
                then each method must be passed a full URL.
            token (str, optional): Used as the value for the `X-Auth-Token` key in request headers.
            curl_logger (RequestAndResponseLogger, optional): class (or instance) to log requests
                and responses.
                Defaults to ``RequestAndResponseLogger``.
            content_type (str, optional):  The default content type to include in the headers.
        '''
        self.default_headers = {'Content-Type': content_type}
        self.base_url = base_url
        self.token = token
        self.curl_logger = self._initialized_logger(curl_logger or RequestAndResponseLogger)

        # Although requests.Sessions does not take any parameters, it is possible to register
        # a different parent class that may take parameters as well as not accept *args or **kwargs,
        # we need to dynamically build the call
        if sys.version_info > (3, 2):
            sig = inspect.signature(super(QERequestsLoggingClient, self).__init__)
            kwargs = {x: y for x, y in locals().items() if x in sig.parameters}
        else:
            kwargs = {}
        super(QERequestsLoggingClient, self).__init__(**kwargs)

    @property
    def token(self):
        '''
        Property that gets/sets/deletes the ``X-Auth-Token`` in request headers.
        '''
        return self.default_headers.get('X-Auth-Token')

    @token.setter
    def token(self, token):
        self.default_headers['X-Auth-Token'] = token

    @token.deleter
    def token(self):
        del self.default_headers['X-Auth-Token']

    def _initialized_logger(self, curl_logger):
        return curl_logger(self._logger) if isinstance(curl_logger, type) else curl_logger

    def _get_logger(self, curl_logger):
        if curl_logger:
            return self._initialized_logger(curl_logger)
        return self.curl_logger

    def log(self, data):
        '''
        Logs (DEBUG level) the provided data using our logger.

        Args:
            data: Anything that can be logged, most commonly a string.
        '''
        self._logger.debug(data)

    def request(self, method, url, curl_logger=None, **kwargs):
        '''
        Allow for a one-off custom logger (class or instance).

        All the Session object verb methods (get, put, etc.) come through this method,
        so we have one pinch point at which we can enhance the request processing::

           * log the request and response per the logger, with a one-off override
           * partial URLs are prefixed with the ``base_url`` for simpler use
           * partial URLs are properly sanitized for simpler use

        Args:
            method (str): The request method (see requests.Session)
            url (str):  The url part/extension for the specific request.
                A fully qualified URL will suppress prefixing with the ``base_url`` value.
            curl_logger (RequestAndResponseLogger): A class (or instance) to use to log
                the request and response.
                If not supplied, the curl_logger supplied at the class level (or the default) will
                be used.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            response (requests.Response): The result from the parent request call
            (unless an exception is raised).
        '''
        # If headers are provided by both, headers "wins" over default_headers
        kwargs['headers'] = dict(self.default_headers, **(kwargs.get('headers', {})))
        kwargs['headers'] = dict_strip_value(kwargs['headers'])
        full_url = _full_url(self.base_url, url)
        request_kwargs = {'method': method, 'url': full_url, 'kwargs': kwargs}
        try:
            response = super(QERequestsLoggingClient, self).request(method, full_url,
                                                                    verify=False, **kwargs)
        except:
            # If the request fails for any reason log the request data causing the failure.
            self._get_logger(curl_logger).log_request(request_kwargs)
            raise
        # Because request can be provided iterable, the logging needs to occur after the
        # request library is called to ensure the iterable is not expired before being
        # utilized by the library
        self._get_logger(curl_logger).log(request_kwargs, response)
        return response
