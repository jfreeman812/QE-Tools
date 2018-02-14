from configparser import ConfigParser
import json
from os import environ, path
import time
try:
    from urllib import parse
except ImportError:
    import urlparse as parse

from flask import Flask, request
from flask_restplus import Api, Resource, reqparse, fields
import requests

import custom_fields


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


TICKET_LIST = fields.List(custom_fields.TicketId(example='JIRA-1234'))


coverage_entry = api.model('Coverage Entry', {
    'Categories': fields.List(fields.String, example=['Variable Builder'], required=True),
    'Execution Method': custom_fields.ExecutionMethod(example='automated', required=True),
    'Feature Name': fields.String(example='Variable Builder', required=True),
    'Interface Type': custom_fields.InterfaceType(example='gui', required=True),
    'Polarity': custom_fields.Polarity(example='positive', required=True),
    'Priority': custom_fields.Priority(example='medium', required=True),
    'Product': fields.String(example='ARIC', required=True),
    'Status': custom_fields.Status(example='operational', required=True),
    'Suite': custom_fields.Suite(example='smoke', required=True),
    'Test Name': fields.String(example='Edit and upate a created Variable', required=True),
    'Tickets': TICKET_LIST,
    'quarantined': TICKET_LIST,
    'needs work': TICKET_LIST,
    'not yet implemented': TICKET_LIST,
})


raw_args = api.model('Raw Input', {
    'events': fields.List(fields.Nested(coverage_entry), required=True),
    'host': fields.String(required=True, example='jenkinsqe.rba.rackspace.com'),
    'timestamp': fields.Float(example=1518209250.403),
    'source': fields.String(default=SPLUNK_REPORT_SOURCE),
    'index': fields.String(default=SPLUNK_REPORT_INDEX),
})


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

    def _post(self, args, events=None):
        events = events or args.get('events', [])
        if not events:
            return {'message': 'No events to post!'}, 400
        common_data = {
            'time': args.get('timestamp') or coverage_current_time(),
            'host': args['host'],
            'index': args['index'],
            'source': args['source'],
            'sourcetype': '_json'
        }
        events = [{'event': x} for x in events]
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

    @api.response(201, 'Accepted')
    @api.response(500, 'Server Error')
    @api.doc('POST-Raw-Data')
    @api.expect(raw_args)
    def post(self):
        args = request.json
        return self._post(args)


@ns.route('/staging/<string:host>', endpoint='staging coverage data')
class StagingCoverage(SplunkAPI):
    fixed_arg_values = {'source': SPLUNK_REPORT_SOURCE, 'index': SPLUNK_REPORT_INDEX}

    @api.response(201, 'Accepted')
    @api.response(400, 'Bad Request')
    @api.response(500, 'Server Error')
    @api.doc('POST-Staging-Data')
    @api.expect([coverage_entry], validate=True)
    def post(self, host):
        errors = custom_fields.validate_response_list(request.json, coverage_entry, 'Test Name')
        if errors:
            return {'message': 'payload validation failed!',
                    'errors': errors}, 400
        args = {**self.fixed_arg_values, **{'host': host}}
        timestamp = request.args.get('timestamp')
        if timestamp:
            args.update(timestamp=timestamp)
        return self._post(args, events=request.json)


if __name__ == '__main__':
    app.run()
