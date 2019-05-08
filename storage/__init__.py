from flask import Flask
from os import environ, path
from datetime import timedelta
from storage.stats import Stats
from redis import Redis
import requests


stats = None
app_address = 'http://app:5000'
app_pubkey = None
redis = None


def create_app(test_config=None):

    # create the app configuration
    app = Flask(__name__,
                instance_path=environ.get('FLASK_APP_INSTANCE', '/user/src/app/instance'))  # instance path

    app.config.from_mapping(
        UPLOAD_FOLDER=environ.get('UPLOAD_FOLDER', '/user/src/app/storage/images'),
        AUTH_LEEWAY=timedelta(seconds=int(environ.get('AUTH_LEEWAY', '30'))),  # leeway in seconds
        STATIC_URL=environ.get('STATIC_URL', '/static')
    )

    if test_config is None:
        # load the instance config if it exists, when not testing
        app.config.from_pyfile(path.join(app.instance_path, 'config.py'), silent=True)
    else:
        app.config.from_mapping(test_config)

    # INIT
    global redis
    redis = Redis(host='storage_redis_1', port=6379, db=0)

    global app_pubkey
    # app_pubkey = requests.get(app_address+'/api/pubkey').json()['public_key']
    from instance.config import PRIVATE_KEY, PUBLIC_KEY
    app_pubkey = PUBLIC_KEY

    global stats
    stats = Stats(redis)

    from storage import service

    app.register_blueprint(service.bp)

    return app
