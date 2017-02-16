import argparse
import collections
import uuid

import flask
from flask.views import MethodView
from httpbin.core import app, jsonify
from httpbin.helpers import get_dict

DATA = collections.defaultdict(dict)
KEYS = ('url', 'args', 'form', 'data', 'origin', 'headers', 'files', 'json')


def validate_and_jsonify(f):
    def decorator(*args, **kwargs):
        group_name = kwargs.get('group_name', None)
        data_id = kwargs.get('data_id', None)
        if group_name is not None and group_name not in DATA:
            flask.abort(404)
        if data_id is not None and data_id not in DATA[group_name]:
            flask.abort(404)
        return jsonify(f(*args, **kwargs))
    return decorator


class GroupAPI(MethodView):
    decorators = [validate_and_jsonify]

    def get(self):
        return list(DATA.keys())

    def post(self):
        json = flask.request.get_json(force=True, silent=True) or {}
        group_name = json.get('group_name') or flask.request.values.get('group_name', '')
        DATA[group_name] = {}
        return {'group_name': group_name}

    def delete(self, group_name):
        del DATA[group_name]
        return {'message': '{} deleted successfully'}


group_view = GroupAPI.as_view('group_api')
app.add_url_rule('/data-check/', view_func=group_view, methods=['GET'])
app.add_url_rule('/data-check/', view_func=group_view, methods=['POST'])
app.add_url_rule('/data-check/<group_name>', view_func=group_view, methods=['GET', 'DELETE'])


class DataAPI(MethodView):
    decorators = [validate_and_jsonify]

    def get(self, group_name, data_id):
        return DATA[group_name] if data_id is None else DATA[group_name][data_id]

    def post(self, group_name):
        data_id = str(uuid.uuid4())
        DATA[group_name][data_id] = get_dict(*KEYS)
        return {data_id: DATA[group_name][data_id]}

    def put(self, group_name, data_id):
        DATA[group_name][data_id].update(get_dict(*KEYS))
        return DATA[group_name][data_id]

    def delete(self, group_name, data_id):
        del DATA[group_name][data_id]
        return {'message': '{} deleted successfully'.format(data_id)}


data_view = DataAPI.as_view('data_api')
app.add_url_rule('/data-check/<group_name>/', defaults={'data_id': None}, view_func=data_view,
                 methods=['GET'])
app.add_url_rule('/data-check/<group_name>/', view_func=data_view, methods=['POST'])
app.add_url_rule('/data-check/<group_name>/<data_id>', view_func=data_view,
                 methods=['GET', 'PUT', 'DELETE'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()
    app.run(port=args.port, host=args.host)
