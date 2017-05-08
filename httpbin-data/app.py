import argparse
import collections
from distutils.util import strtobool
import uuid

import flask
from flask.views import MethodView
from httpbin.core import app, jsonify
from httpbin.helpers import get_dict

KEYS = ('url', 'args', 'form', 'data', 'origin', 'headers', 'files', 'json')

_DEFAULT_VALUE = object()


class DefaultDictHandler(object):
    def __init__(self, default_factory):
        self.__dict__ = collections.defaultdict(default_factory)

    def _dig_layers(self, *layers):
        data = self.__dict__
        for layer in layers:
            data = data[layer]
        return data

    def get(self, *layers):
        return self._dig_layers(*layers)

    def set(self, *layers, value=_DEFAULT_VALUE):
        layers, key = layers[:-1], layers[-1]
        if value is _DEFAULT_VALUE:
            raise ValueError('Key and Value must both be provided')
        data = self._dig_layers(*layers)
        data[key] = value

    def delete(self, *layers):
        layers, key = layers[:-1], layers[-1]
        data = self._dig_layers(*layers)
        data.pop(key)

    def update(self, *layers, update_dict=_DEFAULT_VALUE):
        if update_dict is _DEFAULT_VALUE:
            raise ValueError('no update dict provided')
        data = self._dig_layers(*layers)
        data[key].update(update_dict)

    def keys(self):
        return self.__dict__.keys()


def _get_handler(args, name, default_factory=dict):
    dict_handler = DefaultDictHandler(default_factory)
    return dict_handler


def validate_and_jsonify(f):
    def decorator(*args, **kwargs):
        group_name = kwargs.get('group_name', None)
        data_id = kwargs.get('data_id', None)
        if group_name is not None and group_name not in data.keys():
            flask.abort(404)
        if data_id is not None and data_id not in data.get(group_name):
            flask.abort(404)
        return jsonify(f(*args, **kwargs))
    return decorator


class CounterAPI(MethodView):
    decorators = [validate_and_jsonify]

    def get(self, counter_name):
        return {counter_name: counter.get(counter_name)}

    def put(self, counter_name):
        counter.set(counter_name, value=counter.get(counter_name) + 1)
        count = counter.get(counter_name)
        error_on_first = strtobool(flask.request.values.get('error_on_first', 'False'))
        if error_on_first and count == 1:
            flask.abort(409)
        return {counter_name: count}

    def delete(self, counter_name):
        counter.delete(counter_name)
        return {'message': '{} deleted!'.format(counter_name)}


counter_view = CounterAPI.as_view('counter_view')
app.add_url_rule('/counter/<counter_name>', view_func=counter_view, methods=['GET', 'PUT',
                                                                             'DELETE'])


class GroupAPI(MethodView):
    decorators = [validate_and_jsonify]

    def get(self):
        return list(data.keys())

    def post(self):
        json = flask.request.get_json(force=True, silent=True) or {}
        group_name = json.get('group_name') or flask.request.values.get('group_name', '')
        data.set(group_name, value={})
        return {'group_name': group_name}

    def delete(self, group_name):
        data.delete(group_name)
        return {'message': '{} deleted successfully'.format(group_name)}


group_view = GroupAPI.as_view('group_api')
app.add_url_rule('/data-check/', view_func=group_view, methods=['GET'])
app.add_url_rule('/data-check/', view_func=group_view, methods=['POST'])
app.add_url_rule('/data-check/<group_name>', view_func=group_view, methods=['DELETE'])


class DataAPI(MethodView):
    decorators = [validate_and_jsonify]

    def get(self, group_name, data_id):
        layers = filter(None, (group_name, data_id))
        return data.get(*layers)

    def post(self, group_name):
        data_id = str(uuid.uuid4())
        data.set(group_name, data_id, value=get_dict(*KEYS))
        return {data_id: data.get(group_name, data_id)}

    def put(self, group_name, data_id):
        data.update(group_name, data_id, update_dict=get_dict(*KEYS))
        return data.get(group_name, data_id)

    def delete(self, group_name, data_id):
        data.delete(group_name, data_id)
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
    data = _get_handler(args, 'data')
    counter = _get_handler(args, 'counter', default_factory=int)
    app.run(port=args.port, host=args.host)
