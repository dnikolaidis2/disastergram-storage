from flask import Flask
from os import environ, path


def create_app(test_config=None):
    # Get environment variables
    instance_path = environ.get('FLASK_APP_INSTANCE', '/user/src/app/instance')

    # create the app configuration
    app = Flask(__name__,
                instance_path=instance_path,
                static_url_path='/imstore')

    app.config['UPLOAD_FOLDER'] = environ.get('UPLOAD_FOLDER', '/user/src/app/storage/static')

    if test_config is None:
        # load the instance config if it exists, when not testing
        app.config.from_pyfile(path.join(app.instance_path, 'config.py'), silent=True)
    else:
        app.config.from_mapping(test_config)

    # INIT

    from storage import storage

    app.register_blueprint(storage.bp)

    return app
