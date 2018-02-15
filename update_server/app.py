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
api = Api(bp, title='Server Updater', doc='/trigger_update/doc', authorizations=authorizations)


def updater_configs():
    parser = ConfigParser()
    file_path = environ.get('CONFIG_FILE_PATH')
    assert parser.read(file_path), 'Error: can not find {}'.format(file_path)
    data = parser['updater']
    return data


CONFIGS = updater_configs()


def _comma_separated_to_list(comma_separated):
    return [x.strip() for x in comma_separated.split(',')]


def update_repo():
    cwd = path.join(path.expanduser('~'), CONFIGS['repo_name'])
    subprocess.check_call('git reset --hard HEAD'.split(), cwd=cwd)
    subprocess.check_call('git clean -fdx'.split(), cwd=cwd)
    subprocess.check_call('git pull origin master'.split(), cwd=cwd)


def restart_servers():
    for service in _comma_separated_to_list(CONFIGS['services']):
        subprocess.check_call('supervisorctl signal HUP {}'.format(service).split())


@bp.route('/', endpoint='TriggerUpdate')
class UpdaterAPI(Resource):
    @api.header('X-Auth-Token', 'Shared token', required=True)
    @api.response(200, 'OK')
    @api.response(403, 'Not Authorized')
    @api.response(500, 'Server Error')
    @api.doc('Trigger-Update')
    def put(self):
        token = request.headers.get('X-Auth-Token')
        if token != CONFIGS['token']:
            api.abort(403)
        try:
            update_repo()
            restart_servers()
        except subprocess.CalledProcessError as e:
            return {'message': 'Failed to update',
                    'error': str(e)}, 500
        return {'message': 'Update successfully triggered!'}, 200


app.register_blueprint(bp)

if __name__ == '__main__':
    app.run()
