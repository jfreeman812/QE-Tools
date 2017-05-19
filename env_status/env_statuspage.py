import argparse
import os
from types import SimpleNamespace
from distutils.util import strtobool

import etcd
from flask import Blueprint, Flask, render_template, url_for, redirect

app = Flask(__name__)

bp = Blueprint('bp', __name__, template_folder='templates')


def _lowest_level_only(key):
    return key.split('/')[-1]


def _get_env_list():
    response = etcd_client.read('environments')
    return [_lowest_level_only(x['key']) for x in response._children]


def _get_env_status(environment):
    try:
        response = etcd_client.read('environments/{}'.format(environment))
        return bool(strtobool(response.value))
    except etcd.EtcdKeyNotFound:
        return None


def _set_env_status(environment, value_bool):
    etcd_client.write('environments/{}'.format(environment), bool(value_bool))


def _get_all_statuses():
    return [{'name': x, 'status': _get_env_status(x)} for x in sorted(_get_env_list())]


@bp.route('/')
def get_statuses():
    return render_template('main.html', environments=_get_all_statuses())


@bp.route('/enable/<env_name>')
def enable_env(env_name):
    _set_env_status(env_name, True)
    return redirect(url_for('bp.get_statuses'))


@bp.route('/disable/<env_name>')
def disable_env(env_name):
    _set_env_status(env_name, False)
    return redirect(url_for('bp.get_statuses'))


def _host_tuples(hosts, port):
    return tuple(((host, port) for host in hosts))


def _env_args():
    args = SimpleNamespace()
    hostnames = os.environ.get('ETCD_HOSTNAMES', '')
    args.flask_url_prefix = os.environ.get('FLASK_URL_PREFIX', '/environments')
    args.etcd_hostnames = hostnames.split(',') if hostnames else None
    args.etcd_port = os.environ.get('ETCD_PORT', 443)
    args.etcd_protocol = os.environ.get('ETCD_PROTOCOL', 'https')
    args.etcd_ca_cert_path = os.environ.get('ETCD_CA_CERT_PATH', 'env_status/rs_ca_level1.crt')
    return args


def _cli_args(env_args):
    etcd_parser = argparse.ArgumentParser()
    etcd_parser.add_argument("--port", type=int, default=5000)
    etcd_parser.add_argument("--host", default="127.0.0.1")
    etcd_parser.add_argument('---flask-url-prefix', default=env_args.flask_url_prefix,
                             help="URL prefix off FQDN where app runs")
    etcd_parser.add_argument("--etcd-hostnames", nargs="+", default=env_args.etcd_hostnames,
                             help="FQDNs of etcd cluster nodes. Falls back to local datastore.")
    etcd_parser.add_argument("--etcd-port", type=int, default=env_args.etcd_port,
                             help="port to use for etcd cluster hosts")
    etcd_parser.add_argument("--etcd-protocol", default=env_args.etcd_protocol,
                             help="protocol for etcd connection")
    etcd_parser.add_argument("--etcd-ca-cert-path", default=env_args.etcd_ca_cert_path,
                             help="path to ca cert")
    args = etcd_parser.parse_args()
    return args


def _get_etcd_client(args):
    if not args.etcd_hostnames:
        raise KeyError('No etcd hostnames provided, can not connect!')
    etcd_client = etcd.Client(_host_tuples(args.etcd_hostnames, args.etcd_port),
                              protocol=args.etcd_protocol,
                              allow_reconnect=True, ca_cert=args.etcd_ca_cert_path)
    return etcd_client


env_args = _env_args()

if __name__ == '__main__':
    args = _cli_args(env_args)
    etcd_client = _get_etcd_client(args)
    app.register_blueprint(bp, url_prefix=args.flask_url_prefix)
    app.run(host=args.host, port=args.port)
else:
    etcd_client = _get_etcd_client(env_args)
    app.register_blueprint(bp, url_prefix=env_args.flask_url_prefix)
