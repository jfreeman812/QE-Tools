from configparser import ConfigParser
import json
from os import environ, path
import time
try:
    from urllib import parse
except ImportError:
    import urlparse as parse

from flask import Flask
from flask_restplus import Api, Resource, reqparse
import requests


app = Flask(__name__)
api = Api(app, title='Splunk Data Forwarder', doc='/splunk/doc/')

ns = api.namespace('splunk', description='Splunk Forwarding Endpoint')


SPLUNK_COLLECTOR_HOSTNAME = 'httpc.secops.rackspace.com'
SPLUNK_COLLECTOR_URL = 'https://{}:8088/services/collector'.format(SPLUNK_COLLECTOR_HOSTNAME)
SPLUNK_REPORT_INDEX = 'rax_temp_60'
SPLUNK_REPORT_SOURCE = 'rax_qe_coverage'
SPLUNK_UI_BASE_URL = 'sage.rackspace.com:8000'
SPLUNK_UI_SEARCH_PATH = '/en-US/app/search/search'


parser = api.parser()
parser.add_argument('host', type=str, required=True,
                    help='A host must be provided', location='json')
parser.add_argument('events', action='append', required=True,
                    help='events to be posted must be provided', location='json')
parser.add_argument('source', type=str, default=SPLUNK_REPORT_SOURCE,
                    help='the source for the events must be provided', location='json')
parser.add_argument('index', type=str, default=SPLUNK_REPORT_INDEX,
                    help='The index for the data was missing', location='json')
parser.add_argument('timestamp', type=str, default=round(time.time(), 2),
                    help='a unix timestamp for the events', location='json')


def _token_config():
    parser = ConfigParser()
    file_path = path.join(path.expanduser('~'), 'splunk.config')
    assert parser.read(file_path), 'Error: cannot find {}'.format(file_path)
    return parser


TOKENS = _token_config()


@ns.route('/splunk', endpoint='splunk')
class SplunkAPI(Resource):
    def _get_token(self, index):
        return TOKENS[index]['token']

    @staticmethod
    def _splunk_search_url(args):
        search_query = 'index="{}" host="{}"'.format(args['index'], args['host'])
        return parse.urlunparse((
            'https', SPLUNK_UI_BASE_URL, SPLUNK_UI_SEARCH_PATH,
            '', 'q=search%20{}'.format(parse.quote(search_query)), ''
        ))

    @api.response(201, 'Accepted')
    @api.response(500, 'Server Error')
    @api.doc('POST-Splunk-Data')
    @api.expect(parser)
    def post(self):
        args = parser.parse_args()
        common_data = {
            'time': args['timestamp'],
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
                    'url': self._splunk_search_url(args)}, 201
        except requests.exceptions.HTTPError as e:
            return {'message': 'data failed to post!',
                    'error': str(e),
                    'response_text': str(response.content)}, 500


if __name__ == '__main__':
    app.run()
