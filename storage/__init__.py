from flask import Flask
from os import environ, path
from datetime import timedelta
from storage.stats import Stats
from storage.zoo import Zoo
from redis import Redis
from kazoo.client import KazooClient
import urllib.parse
import requests
import os

stats = None
redis = None
zk = None
app_address = 'http://disastergram.nikolaidis.tech/'
app_pubkey = None


def create_app(test_config=None):

    # create the app configuration
    app = Flask(__name__,
                instance_path=environ.get('FLASK_APP_INSTANCE', '/user/src/app/instance'))  # instance path

    app.config.from_mapping(
        UPLOAD_FOLDER=environ.get('UPLOAD_FOLDER', '/user/src/app/storage/images'),
        AUTH_LEEWAY=timedelta(seconds=int(environ.get('AUTH_LEEWAY', '30'))),  # leeway in seconds
        STATIC_URL=environ.get('STATIC_URL', '/static'),
        STORAGE_ID=int(environ.get('STORAGE_ID', '-1')),
        BASEURL=environ.get('BASEURL', ''),
        DOCKER_HOST=environ.get('DOCKER_HOST', ''),
        DOCKER_BASEURL='http://{}'.format(environ.get('DOCKER_HOST', '')),
        REDIS_HOST=environ.get('REDIS_HOST'),
        REDIS_PORT=int(environ.get('REDIS_PORT', '6379')),
        ZOOKEEPER_CONNECTION_STR=environ.get('ZOOKEEPER_CONNECTION_STR', 'zoo1,zoo2,zoo3'),
    )

    if test_config is None:
        # load the instance config if it exists, when not testing
        app.config.from_pyfile(path.join(app.instance_path, 'config.py'), silent=True)
    else:
        app.config.from_mapping(test_config)

    if app.config.get('STORAGE_ID') == -1:
        raise Exception('No storage id was provided. '
                        'STORAGE_ID environment variable cannot be omitted')

    if app.config.get('BASEURL') == '':
        raise Exception('No service base url was provided. '
                        'BASEURL environment variable cannot be omitted')

    if app.config.get('DOCKER_HOST') == '':
        raise Exception('No network host within docker was provided. '
                        'DOCKER_HOST environment variable cannot be omitted')

    if app.config.get('REDIS_HOST') is None:
        raise Exception('No redis host was provided. '
                        'REDIS_HOST environment variable cannot be omitted')

    # Make sure the upload folder exists
    os.makedirs(app.config.get('UPLOAD_FOLDER', '/'), exist_ok=True)

    # INIT
    
    global redis
    redis = Redis(host=app.config.get('REDIS_HOST'), port=app.config.get('REDIS_PORT'), db=0)

    global stats
    stats = Stats(redis)

    znode_data = {
        'BASEURL': app.config['BASEURL'],
        'DOCKER_HOST': app.config['DOCKER_HOST'],
        'DOCKER_BASEURL': app.config['DOCKER_BASEURL']
    }

    global zk
    zk = Zoo(KazooClient(hosts=app.config['ZOOKEEPER_CONNECTION_STR'], logger=app.logger),
             app.config['STORAGE_ID'],
             znode_data)

    global app_pubkey
    app_pubkey = requests.get(urllib.parse.urljoin(app_address, '/api/pubkey')).json()['public_key']

    from storage import service

    app.register_blueprint(service.bp)

    return app
