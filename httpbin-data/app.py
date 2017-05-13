import argparse
import collections
import os
from types import SimpleNamespace
from distutils.util import strtobool
import sys
import uuid

import etcd

import flask
from flask.views import MethodView
from httpbin.core import app, jsonify
from httpbin.helpers import get_dict

KEYS = ('url', 'args', 'form', 'data', 'origin', 'headers', 'files', 'json')

_DEFAULT_VALUE = object()

ETCD_TTL = 24 * 60 * 60


class ETCDHandler(object):
    def __init__(self, default_factory, client, name, etcd_ttl):
        self.default_factory = default_factory
        self.client = client
        self.name = name
        self.etcd_ttl = etcd_ttl

    def _defined_or_default(self, key, default):
        return key if key is not _DEFAULT_VALUE else default

    def _get_subname(self, *layers):
        return '/'.join([self.name, *layers])

    def _keyname_from_child(self, child):
        return child['key'].split('/')[-1]

    def _value_handler(self, value):
        if not isinstance(self.default_factory(), int):
            return value
        if value.isdigit():
            return int(value)
        return value

    def _write_default(self, *layers):
        # in etcd, a dict is treated as a set of slash-path "layers", so an empty dict
        # is equivalent to an empty directory, whereas an int (or str) is defined with key/value
        if isinstance(self.default_factory(), dict):
            self.client.write(self._get_subname(*layers), None, dir=True, ttl=self.etcd_ttl)
            return
        self.client.write(self._get_subname(*layers), self.default_factory())

    def _recursive_read(self, *layers):
        response = self.client.read(self._get_subname(*layers))
        if not response.dir:
            return self._value_handler(response.value)
        keys = self.keys(*layers)
        return {k: self._recursive_read(*layers, k) for k in keys}

    def _recursive_write(self, *layers, value, ttl):
        if not isinstance(value, dict):
            self.client.write(self._get_subname(*layers), value, ttl=ttl)
            return
        # the etcd client does have advanced support for all potential write/overwrite situations
        # so allow the EtcdNotFile error (indicating dir already exists) to pass silently
        try:
            self.client.write(self._get_subname(*layers), None, dir=True, ttl=ttl)
        except etcd.EtcdNotFile:
            pass
        for k, v in value.items():
            self._recursive_write(*layers, k, value=v, ttl=ttl)

    def get(self, *layers):
        try:
            return self._recursive_read(*layers)
        except etcd.EtcdKeyNotFound:
            self._write_default(*layers)
            return self._recursive_read(*layers)

    def set(self, *layers, value=_DEFAULT_VALUE, ttl=_DEFAULT_VALUE):
        ttl = self._defined_or_default(ttl, self.etcd_ttl)
        return self._recursive_write(*layers, value=value, ttl=ttl)

    def delete(self, *layers):
        return self.client.delete(self._get_subname(*layers), recursive=True)

    def update(self, *layers, update_dict=_DEFAULT_VALUE, ttl=_DEFAULT_VALUE):
        ttl = self._defined_or_default(ttl, self.etcd_ttl)
        if update_dict is _DEFAULT_VALUE:
            raise ValueError('no update dict provided')
        self._recursive_write(*layers, value=update_dict, ttl=ttl)

    def keys(self, *layers):
        hierarchy = self._get_subname(*layers)
        try:
            namespace_data = self.client.read(hierarchy)
        except etcd.EtcdKeyNotFound:
            self.client.write(hierarchy, None, dir=True)
            namespace_data = self.client.read(self.name)
        return [self._keyname_from_child(child, *layers) for child in namespace_data._children]


class DefaultDictHandler(object):
    def __init__(self, default_factory):
        self._dict = collections.defaultdict(default_factory)

    def _dig_layers(self, *layers):
        data = self._dict
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
        layers, key = layers[:-1], layers[-1]
        if update_dict is _DEFAULT_VALUE:
            raise ValueError('no update dict provided')
        data = self._dig_layers(*layers)
        data[key].update(update_dict)

    def keys(self):
        return self._dict.keys()


def _get_handler(args, name, default_factory=dict):
    dict_handler = DefaultDictHandler(default_factory)
    if not args.etcd_hostnames:
        return dict_handler
    host_tuple = tuple((x, args.etcd_port) for x in args.etcd_hostnames)
    etcd_client = etcd.Client(host=host_tuple, protocol=args.etcd_protocol, allow_reconnect=True,
                              ca_cert=args.etcd_ca_cert_path)
    try:
        etcd_client.machines
    except etcd.EtcdException:
        print('ERROR CONNECTING TO HOST: Falling back to local datastore.')
        return dict_handler
    return ETCDHandler(default_factory, etcd_client, name, etcd_ttl=args.etcd_ttl)


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
        count = counter.get(counter_name) + 1
        counter.set(counter_name, value=count)
        error_on_first = strtobool(flask.request.values.get('error_on_first', 'False'))
        # error_on_first allows support to test RBAN-6974, which requires the
        # server calling in a callback to get a 409 response on first attempt
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
        return data.get(*filter(None, (group_name, data_id)))

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


def _env_args():
    env_args = SimpleNamespace()
    env_args.etcd_hostnames = os.environ.get('ETCD_HOSTNAMES').split(',')
    env_args.etcd_port = os.environ.get('ETCD_PORT', 443)
    env_args.etcd_protocol = os.environ.get('ETCD_PROTOCOL', 'https')
    env_args.etcd_ca_cert_path = os.environ.get('ETCD_CA_CERT_PATH', 'httbin-data/rs_ca_level1.crt')
    env_args.etcd_ttl = os.environ.get('ETCD_TTL', ETCD_TTL)
    return env_args


def _cli_args(env_args):
    etcd_parser = argparse.ArgumentParser()
    etcd_parser.add_argument("--port", type=int, default=5000)
    etcd_parser.add_argument("--host", default="127.0.0.1")
    etcd_parser.add_argument("--etcd-hostnames", nargs="+", default=env_args.etcd_hostnames,
                             help="FQDNs of etcd cluster nodes. Falls back to local datastore.")
    etcd_parser.add_argument("--etcd-port", default=env_args.etcd_port,
                             help="port to use for etcd cluster hosts")
    etcd_parser.add_argument("--etcd-protocol", default=env_args.etcd_protocol,
                             help="protocol for etcd connection")
    etcd_parser.add_argument("--etcd-ca-cert-path", default=env_args.etcd_cert_path,
                             help="path to ca cert")
    etcd_parser.add_argument("--etcd-ttl", default=env_args.etcd_ttl,
                             help="ttl (in seconds) to expire etcd data")
    args = etcd_parser.parse_args()
    return args


def setup_data(args):
    data = _get_handler(args, 'data')
    counter = _get_handler(args, 'counter', default_factory=int)
    return data, counter


env_args = _env_args()


if sys.stdout.isatty():
    args = _cli_args(env_args)
    data, counter = setup_data(args)
    app.run(port=args.port, host=args.host)
else:
    data, counter = setup_data(env_args)
