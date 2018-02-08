from configparser import ConfigParser
import json
from os import environ, path
import time
try:
    from urllib import parse
except ImportError:
    import urlparse as parse

from flask import Flask
from flask_restplus import Api, Resource, reqparse, fields
import requests


app = Flask(__name__)
app.config.SWAGGER_UI_DOC_EXPANSION = 'full'
app.url_map.strict_slashes = False
api = Api(app, title='QE Data Broker', doc='/coverage/doc/')

ns = api.namespace('coverage', description='Data Broker Endpoint')


SPLUNK_COLLECTOR_HOSTNAME = 'httpc.secops.rackspace.com'
SPLUNK_COLLECTOR_URL = 'https://{}:8088/services/collector'.format(SPLUNK_COLLECTOR_HOSTNAME)
SPLUNK_REPORT_INDEX = 'rax_temp_60'
SPLUNK_REPORT_SOURCE = 'rax_qe_coverage'
SPLUNK_UI_BASE_URL = 'sage.rackspace.com:8000'
SPLUNK_UI_SEARCH_PATH = '/en-US/app/search/search'


base_parser = api.parser()
base_parser.add_argument('host', type=str, required=True,
                         help='A host must be provided', location='json')
base_parser.add_argument('events', type=list, required=True,
                         help='events to be posted must be provided', location='json')
base_parser.add_argument('timestamp', type=float, default=None,
                         help='a unix timestamp for the events. Defaults to current time.',
                         location='json')


raw_parser = base_parser.copy()
raw_parser.add_argument('source', type=str, default=SPLUNK_REPORT_SOURCE,
                        help='the source for the events', location='json')
raw_parser.add_argument('index', type=str, default=SPLUNK_REPORT_INDEX,
                        help='The index to which the data will be posted', location='json')


def _token_config():
    parser = ConfigParser()
    file_path = path.join(path.expanduser('~'), 'splunk.config')
    assert parser.read(file_path), 'Error: cannot find {}'.format(file_path)
    return parser


def coverage_current_time():
    '''
    Returns a unix timestamp for the current time,
    rounded to the nearest hundred seconds,
    to help cluster multiple separate reports sent in sequence with a shared timestamp.
    '''
    return round(time.time(), -2)


TOKENS = _token_config()


class SplunkAPI(Resource):
    parser = None
    fixed_arg_values = {}

    def _get_token(self, index):
        return TOKENS[index]['token']

    @staticmethod
    def _display_url(args):
        search_query = 'index="{}" host="{}"'.format(args['index'], args['host'])
        return parse.urlunparse((
            'https', SPLUNK_UI_BASE_URL, SPLUNK_UI_SEARCH_PATH,
            '', 'q=search%20{}'.format(parse.quote(search_query)), ''
        ))

    def _get_args(self):
        args = self.parser.parse_args()
        for name, value in self.fixed_arg_values.items():
            args[name] = value
        return args

    def post(self):
        args = self._get_args()
        common_data = {
            'time': args['timestamp'] or coverage_current_time(),
            'host': args['host'],
            'index': args['index'],
            'source': args['source'],
            'sourcetype': '_json'
        }
        events = [{'event': x} for x in args['events']]
        for event in events:
            event.update(common_data)
        response = requests.post(SPLUNK_COLLECTOR_URL, data='\n'.join(map(json.dumps, events)),
                                 headers={'Authorization': self._get_token(args['index'])},
                                 verify=False)
        try:
            response.raise_for_status()
            return {'message': 'data posted successfully!',
                    'url': self._display_url(args)}, 201
        except requests.exceptions.HTTPError as e:
            return {'message': 'data failed to post!',
                    'error': str(e),
                    'response_text': str(response.content)}, 500


# leaving fully-extensible API
@ns.route('/', endpoint='RAW-Data')
@api.hide
class RawCoverage(SplunkAPI):
    parser = raw_parser

    @api.response(201, 'Accepted')
    @api.response(500, 'Server Error')
    @api.doc('POST-Raw-Data')
    @api.expect(raw_parser)
    def post(self):
        return super(RawCoverage, self).post()


@ns.route('/staging', endpoint='staging coverage data')
class StagingCoverage(SplunkAPI):
    parser = base_parser
    fixed_arg_values = {'source': SPLUNK_REPORT_SOURCE, 'index': SPLUNK_REPORT_INDEX}

    @api.response(201, 'Accepted')
    @api.response(500, 'Server Error')
    @api.doc('POST-Staging-Data')
    @api.expect(base_parser)
    def post(self):
        return super(StagingCoverage, self).post()


if __name__ == '__main__':
    app.run()
