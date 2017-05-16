from distutils.util import strtobool

import etcd
from flask import Flask, render_template, url_for, redirect

app = Flask(__name__)

ETCD_HOST_TUPLES = (('etcd01.rba.rackspace.com', 443),
                    ('etcd02.rba.rackspace.com', 443),
                    ('etcd03.rba.rackspace.com', 443))


etcd_client = etcd.Client(ETCD_HOST_TUPLES, protocol='https',
                          allow_reconnect=True, ca_cert='rs_ca_level1.crt')


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


@app.route('/')
def get_statuses():
    return render_template('main.html', environments=_get_all_statuses())


@app.route('/enable/<env_name>')
def enable_env(env_name):
    _set_env_status(env_name, True)
    return redirect(url_for('get_statuses'))


@app.route('/disable/<env_name>')
def disable_env(env_name):
    _set_env_status(env_name, False)
    return redirect(url_for('get_statuses'))
