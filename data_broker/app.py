from collections import defaultdict, Counter
from configparser import ConfigParser
import json
import lzma
from os import environ, path, makedirs
import sys
import time
import uuid
try:
    from urllib import parse
except ImportError:
    import urlparse as parse

from flask import Flask, request
from flask_restplus import Api, Resource, reqparse, fields
import requests

from bin.prod_data_dir import PROD_DATA_DIR
from __schema_version__ import SCHEMA_VERSION
import custom_fields
from whitelist import Whitelist


app = Flask(__name__)
app.config.SWAGGER_UI_DOC_EXPANSION = 'full'
app.url_map.strict_slashes = False
api = Api(app, title='QE Data Broker', doc='/coverage/doc/', version='1.1')

ns = api.namespace('coverage', description='Data Broker Endpoint')

whitelist = Whitelist()


SPLUNK_COLLECTOR_HOSTNAME = 'hec.dfw1.splunk.rackspace.com'
SPLUNK_COLLECTOR_URL = 'https://{}:8088/services/collector'.format(SPLUNK_COLLECTOR_HOSTNAME)
SPLUNK_STAGING_INDEX = 'rax_temp_60'
SPLUNK_PRODUCTION_INDEX = 'rax_qe_coverage'
SPLUNK_REPORT_SOURCE = 'rax_qe_coverage'
SPLUNK_UI_BASE_URL = 'sage.rackspace.com:8000'
SPLUNK_UI_SEARCH_PATH = '/en-US/app/search/search'
# The upload limit provided by Jeff Windsor with the SAAC team is 1 MiB,
# so we set our operating limit safely inside at 92% of that.
MAX_UPLOAD_BYTES = (2**20) * .92


TICKET_LIST = fields.List(custom_fields.TicketId(example='JIRA-1234'))

PH_FIELD = custom_fields.ProductHierarchy(example='RBA::ARIC',
                                          description='The ProductHierachy being tested')


coverage_entry = api.model('Coverage Entry', {
    'Categories': fields.List(fields.String, example=['Variable Builder'],
                              min_items=1, required=True),
    'Execution Method': custom_fields.ExecutionMethod(example='automated', required=True),
    'Interface Type': custom_fields.InterfaceType(example='gui', required=True),
    'Polarity': custom_fields.Polarity(example='positive', required=True),
    'Priority': custom_fields.Priority(example='medium', required=True),
    'Product': PH_FIELD,
    'Product Hierarchy': PH_FIELD,
    'Status': custom_fields.Status(example='operational', required=True),
    'Suite': custom_fields.Suite(example='smoke', required=True),
    'Test Name': fields.String(example='Edit and update a created Variable', required=True),
    'test_id': fields.String(example='Variable Builder.Edit and update a created Variable'),
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
    'index': fields.String(default=SPLUNK_STAGING_INDEX),
})


def _token_config():
    parser = ConfigParser()
    file_path = path.join(path.expanduser('~'), 'splunk.config')
    assert parser.read(file_path), 'Error: cannot find {}'.format(file_path)
    return parser


TOKENS = _token_config()


def _enrich_data(entry):
    product_hierarchy = entry.pop('Product Hierarchy')
    team, product = product_hierarchy.split(custom_fields.ProductHierarchy.hierarchy_separator)
    entry.update({'Team': team, 'Product': product})
    return entry


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

    def _check_for_duplicates(self, events):
        test_ids = [self._test_id_from(x) for x in events]
        duplicates = {name: count for name, count in Counter(test_ids).items() if count > 1}
        valids = {self._test_id_from(x): x for x in events}.values()
        return valids, duplicates

    def _validate_payload(self):
        field_name_alternates = {'Product Hierarchy': 'Product'}
        return custom_fields.validate_response_list(
            request.json, coverage_entry, 'Test Name', field_name_alternates=field_name_alternates
        )

    @staticmethod
    def _test_id_from(event):
        return event.get('test_id', '{}.{}'.format(event['Categories'][-1], event['Test Name']))

    def _prep_event(self, upload_id, common_data, event):
        event.update(upload_id=upload_id)
        event['test_id'] = self._test_id_from(event)
        event = {'event': event}
        event.update(common_data)
        return event

    def _chunk_events(self, events):
        data = []
        for event in events:
            if sys.getsizeof(data) + sys.getsizeof(event) < MAX_UPLOAD_BYTES:
                data.append(event)
            else:
                yield data
                data = [event]
        yield data

    def _prep_args(self):
        args = {**self.fixed_arg_values}  # noqa: E999
        timestamp = request.args.get('timestamp')
        if timestamp:
            args.update(timestamp=timestamp)
        return args

    def _check_whitelist(self):
        return list(whitelist.get_disallowed({x['Product Hierarchy'] for x in request.json}))

    def _write_data_file(self):
        data_by_product = defaultdict(list)
        for entry in request.json:
            product = entry['Product Hierarchy'].split('::')[-1]
            product_slug = ''.join(filter(
                lambda x: x.isalnum() or x in ('.', '_'), product.replace(' ', '_')
            ))
            data_by_product[product_slug].append(entry)
        for product_slug in data_by_product:
            product_path = path.join(PROD_DATA_DIR, product_slug)
            if not path.exists(product_path):
                makedirs(product_path)
            file_path = path.join(
                product_path, '{}.xz'.format(time.strftime('%Y%m%d_%H%M%S')))
            with lzma.open(file_path, 'wt') as f:
                f.write(json.dumps(data_by_product[product_slug]))

    def _post(self, require_perfection=False, check_whitelist=False, write_file=False):
        initial_count = len(request.json)
        if not initial_count:
            return {'message': 'No events to post!'}, 400
        valids, errors = self._validate_payload()

        if check_whitelist:
            disallowed = self._check_whitelist()
            if disallowed:
                message = 'This payload contains hierarchies not on the whitelist!'
                return self._return_message(
                    initial_count=initial_count, message=message, errors=disallowed, status_code=401
                )

        valids, duplicates = self._check_for_duplicates(valids)
        if duplicates:
            errors.append({'duplicate entries': duplicates})

        valids_count = len(valids)

        if require_perfection and errors:
            message = 'Some entries did not meet requirements, no data sent.'
            return self._return_message(
                allowed_count=valids_count, initial_count=initial_count,
                message=message, errors=errors, status_code=400
            )
        if not valids:
            message = 'All entries contained errors, no data sent.'
            return self._return_message(
                allowed_count=valids_count, initial_count=initial_count,
                message=message, errors=errors, status_code=400
            )

        valids = [_enrich_data(x) for x in valids]
        if write_file:
            # wrap writing in a broad try/except so that write failures will not impede uploads
            try:
                self._write_data_file()
            except BaseException:
                pass
        args = self._prep_args()
        common_data = {
            'time': args.get('timestamp') or time.time(),
            'host': SCHEMA_VERSION,
            'index': args['index'],
            'source': args['source'],
            'sourcetype': '_json'
        }
        upload_id = str(uuid.uuid4())
        events = [self._prep_event(upload_id, common_data, x) for x in valids]

        total_posted = 0
        url = self._display_url(index=args['index'], upload_id=upload_id)
        for subset in self._chunk_events(events):
            response = requests.post(
                SPLUNK_COLLECTOR_URL, data='\n'.join(map(json.dumps, subset)),
                headers={'Authorization': self._get_token(args['index'])}, verify=False
            )
            try:
                response.raise_for_status()
                total_posted += len(subset)
            except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError) as e:
                message = 'Some data failed to post due to remote host error!'
                return self._return_message(
                    allowed_count=valids_count, posted_count=total_posted,
                    initial_count=initial_count, message=message, status_code=500,
                    url=url, errors={'local_error': str(e), 'remote_error': str(response.content)}
                )

        message = 'data posted successfully!'
        status_code = 201
        if errors:
            message = 'Some data posted, some filtered for errors.'
            status_code = 451
        return self._return_message(
            allowed_count=valids_count, posted_count=total_posted, initial_count=initial_count,
            message=message, url=url, errors=errors, status_code=status_code
        )

    def _return_message(self, allowed_count=0, posted_count=0, initial_count=0, message='',
                        status_code=201, url=None, errors=None):
        body = {
            'initial_event_count': initial_count,
            'validated_event_count': allowed_count,
            'posted_event_count': posted_count,
            'message': message,
            'errors': errors,
            'url': url
        }
        return {k: v for k, v in body.items() if v not in (None, [], {})}, status_code


@ns.route('/staging', endpoint='staging data')
class StagingCoverage(SplunkAPI):
    fixed_arg_values = {'source': SPLUNK_REPORT_SOURCE, 'index': SPLUNK_STAGING_INDEX}

    @api.response(201, 'Accepted')
    @api.response(400, 'Bad Request')
    @api.response(500, 'Server Error')
    @api.doc('POST-Staging-Data')
    @api.expect([coverage_entry], validate=True)
    def post(self):
        return self._post()


@ns.route('/production', endpoint='production data')
class ProductionCoverage(SplunkAPI):
    fixed_arg_values = {'source': SPLUNK_REPORT_SOURCE, 'index': SPLUNK_PRODUCTION_INDEX}

    @api.response(201, 'Accepted')
    @api.response(400, 'Bad Request')
    @api.response(401, 'Unauthorized')
    @api.response(500, 'Server Error')
    @api.doc('POST-Staging-Data')
    @api.expect([coverage_entry], validate=True)
    def post(self):
        # on a "rewind" call, do not write a second copy of the data
        write_file = not request.args.get('is_rewind', False)
        return self._post(check_whitelist=True, require_perfection=True, write_file=write_file)


if __name__ == '__main__':
    app.run()
