from configparser import ConfigParser
from os import path, environ
import subprocess

from flask import Flask, Blueprint, request
from flask_restplus import Api, Resource


app = Flask(__name__)
app.config.SWAGGER_UI_DOC_EXPANSION = 'full'
app.url_map.strict_slashes = False

authorizations = {
    'apiKey': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'X-Auth-Token'
    }
}

bp = Blueprint('api', __name__, url_prefix='/trigger_update')
api = Api(bp, title='Server Updater', doc='/doc', authorizations=authorizations)
ns = api.namespace('', description='update server')


def updater_configs():
    parser = ConfigParser()
    file_path = environ.get('CONFIG_FILE_PATH')
    assert parser.read(file_path), 'Error: can not find {}'.format(file_path)
    assert 'updater' in parser.sections(), '"updater" section missing in {}'.format(file_path)
    updater_configs = parser['updater']
    required_keys = ('repo_name', 'token', 'services')
    missing_keys = list(filter(lambda x: x not in updater_configs, required_keys))
    missing_key_msg = 'Required keys ({}) were missing from the config file at {}.'
    assert not missing_keys, missing_key_msg.format(missing_keys, file_path)
    return updater_configs


CONFIGS = updater_configs()


def _get_repo_path():
    return path.join(path.expanduser('~'), CONFIGS['repo_name'])


def _comma_separated_to_list(comma_separated):
    return [x.strip() for x in comma_separated.split(',')]


def update_repo(repo_path):
    subprocess.check_call('git reset --hard HEAD'.split(), cwd=repo_path)
    subprocess.check_call('git clean -fdx'.split(), cwd=repo_path)
    subprocess.check_call('git pull origin master'.split(), cwd=repo_path)


def restart_servers():
    for service in _comma_separated_to_list(CONFIGS['services']):
        subprocess.check_call('supervisorctl signal HUP {}'.format(service).split())


def package_updater(repo_path):
    updater_path = path.join(repo_path, 'artifactory_updater')
    subprocess.check_call(['./updater.py'], cwd=updater_path)


@ns.route('/', endpoint='TriggerUpdate')
class UpdaterAPI(Resource):
    @api.header('X-Auth-Token', 'Shared token', required=True)
    @api.response(200, 'OK')
    @api.response(403, 'Not Authorized')
    @api.response(500, 'Server Error')
    @api.doc('Trigger-Update')
    def put(self):
        repo_path = _get_repo_path()
        token = request.headers.get('X-Auth-Token')
        if token != CONFIGS['token']:
            api.abort(403)
        try:
            update_repo(repo_path)
            restart_servers()
            package_updater(repo_path)
        except subprocess.CalledProcessError as e:
            return {'message': 'Failed to update',
                    'error': str(e)}, 500
        return {'message': 'Update successfully triggered!'}, 200


app.register_blueprint(bp)

if __name__ == '__main__':
    app.run()
