from configparser import ConfigParser
import json
from os import environ, path
import time
import uuid
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
SCHEMA_VERSION = 'qe_coverage_metrics_schema_v20180301'


TICKET_LIST = fields.List(custom_fields.TicketId(example='JIRA-1234'))

PH_FIELD = custom_fields.ProductHierarchy(example='RBA::ARIC',
                                          description='The ProductHierachy being tested')


coverage_entry = api.model('Coverage Entry', {
    'Categories': fields.List(fields.String, example=['Variable Builder'], required=True),
    'Execution Method': custom_fields.ExecutionMethod(example='automated', required=True),
    'Feature Name': fields.String(example='Variable Builder', required=True),
    'Interface Type': custom_fields.InterfaceType(example='gui', required=True),
    'Polarity': custom_fields.Polarity(example='positive', required=True),
    'Priority': custom_fields.Priority(example='medium', required=True),
    'Product': PH_FIELD,
    'Product Hierarchy': PH_FIELD,
    'Status': custom_fields.Status(example='operational', required=True),
    'Suite': custom_fields.Suite(example='smoke', required=True),
    'Test Name': fields.String(example='Edit and upate a created Variable', required=True),
    'Tickets': TICKET_LIST,
    'quarantined': TICKET_LIST,
    'needs work': TICKET_LIST,
    'not yet implemented': TICKET_LIST,
    'pending': TICKET_LIST,
})


raw_args = api.model('Raw Input', {
    'events': fields.List(fields.Nested(coverage_entry), required=True),
    'timestamp': fields.Float(example=1518209250.403),
    'source': fields.String(default=SPLUNK_REPORT_SOURCE),
    'index': fields.String(default=SPLUNK_REPORT_INDEX),
})


def _token_config():
    parser = ConfigParser()
    file_path = path.join(path.expanduser('~'), 'splunk.config')
    assert parser.read(file_path), 'Error: cannot find {}'.format(file_path)
    return parser


TOKENS = _token_config()


class SplunkAPI(Resource):
    fixed_arg_values = {}

    def _get_token(self, index):
        return TOKENS[index]['token']

    @staticmethod
    def _display_url(**kwargs):
        search_query = ' '.join(['{}="{}"'.format(k, v) for k, v in kwargs.items()])
        return parse.urlunparse((
            'https', SPLUNK_UI_BASE_URL, SPLUNK_UI_SEARCH_PATH,
            '', 'q=search%20{}'.format(parse.quote(search_query)), ''
        ))

    def _prep_event(self, upload_id, common_data, event):
        event.update(upload_id=upload_id)
        event = {'event': event}
        event.update(common_data)
        return event

    def _post(self, args, events=None):
        events = events or args.get('events', [])
        if not events:
            return {'message': 'No events to post!'}, 400
        common_data = {
            'time': args.get('timestamp') or time.time(),
            'host': SCHEMA_VERSION,
            'index': args['index'],
            'source': args['source'],
            'sourcetype': '_json'
        }
        upload_id = str(uuid.uuid4())
        events = [self._prep_event(upload_id, common_data, x) for x in events]
        response = requests.post(SPLUNK_COLLECTOR_URL, data='\n'.join(map(json.dumps, events)),
                                 headers={'Authorization': self._get_token(args['index'])},
                                 verify=False)
        try:
            response.raise_for_status()
            return {'message': 'data posted successfully!',
                    'url': self._display_url(index=args['index'], upload_id=upload_id)}, 201
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


def _enrich_data(entry):
    product_hierarchy = entry.pop('Product Hierarchy')
    team, product = product_hierarchy.split(custom_fields.ProductHierarchy.hierarchy_separator)
    entry.update({'Team': team, 'Product': product})
    return entry


@ns.route('/staging', endpoint='staging data')
class StagingCoverage(SplunkAPI):
    fixed_arg_values = {'source': SPLUNK_REPORT_SOURCE, 'index': SPLUNK_REPORT_INDEX}

    @api.response(201, 'Accepted')
    @api.response(400, 'Bad Request')
    @api.response(500, 'Server Error')
    @api.doc('POST-Staging-Data')
    @api.expect([coverage_entry], validate=True)
    def post(self):
        field_name_alternates = {'Product Hierarchy': 'Product'}
        errors = custom_fields.validate_response_list(request.json, coverage_entry, 'Test Name',
                                                      field_name_alternates=field_name_alternates)
        if errors:
            return {'message': 'payload validation failed!',
                    'errors': errors}, 400
        args = {**self.fixed_arg_values}
        timestamp = request.args.get('timestamp')
        if timestamp:
            args.update(timestamp=timestamp)
        return self._post(args, events=[_enrich_data(x) for x in request.json])


if __name__ == '__main__':
    app.run()
