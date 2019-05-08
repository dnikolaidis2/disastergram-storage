from flask import Blueprint, jsonify, request, current_app, abort, send_file, make_response
from storage import stats, app_pubkey, redis
from storage.utils import check_token
import os
from json import JSONDecodeError, loads, dumps

bp = Blueprint('storage', __name__, url_prefix='/')


@bp.errorhandler(400)
def bad_request_handler(error):
    return jsonify(error=error.description), 400


@bp.errorhandler(403)
def bad_request_handler(error):
    return jsonify(error=error.description), 403


@bp.errorhandler(500)
def bad_request_handler(error):
    return jsonify(error=error.description), 500


@bp.route('/<image_id>/<auth_token>', methods=['POST'])
def upload_image(image_id, auth_token):
    # check that we got the appropriate token
    if not check_token(app_pubkey, auth_token, image_id, 'CREATE'):
        abort(403, 'Token could not be verified')

    # check if the post request has the file part
    if 'file' not in request.files:
        abort(400, 'No file part')

    file = request.files['file']
    # if user does not select file, browser also
    # submit an empty part without filename
    if file.filename == '':
        abort(400, 'No selected file')

    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filepath)

    # wannabe json store for redis. Cause rejson-py is a little bitch (╯°□°）╯︵ ┻━┻
    if not redis.set(image_id, dumps({
        "filename": file.filename,
        "filepath": filepath,
        "mimetype": file.mimetype
    })):
        abort(500, 'Could not save image metadata')

    stats.increment_write_delete_requests()
    redis.bgsave()
    return jsonify(status='OK'), 201


@bp.route('/<image_id>/<auth_token>', methods=['DELETE'])
def delete_image(image_id, auth_token):
    # check that we got the appropriate token
    if not check_token(app_pubkey, auth_token, image_id, 'DELETE'):
        abort(403, 'Token could not be verified')

    metadata = None
    try:
        metadata = loads(redis.get(image_id))
    except JSONDecodeError:
        abort(500, 'Could not retrieve image metadata')

    os.remove(metadata['filepath'])
    redis.delete(image_id)
    stats.increment_write_delete_requests()
    redis.bgsave()
    return jsonify(status='OK')


@bp.route('/<image_id>/<access_token>', methods=['GET'])
def get_image(image_id, access_token):
    # check that we got the appropriate token
    if not check_token(app_pubkey, access_token, image_id, 'READ'):
        abort(403, 'Token could not be verified')

    metadata = None
    try:
        metadata = loads(redis.get(image_id))
    except JSONDecodeError:
        abort(500, 'Could not retrieve image metadata')

    stats.increment_read_requests()

    if current_app.env != 'nginx':
        return send_file('images/{}'.format(metadata['filename']), mimetype=metadata['mimetype'])
    else:
        resp = make_response('')
        resp.headers['X-Accel-Redirect'] = \
            '{}/{}'.format(current_app.config.get('STATIC_URL', 'imstore'), metadata['filename'])
        resp.headers['Content-Type'] = metadata['mimetype']
        return resp


@bp.route('/stats', methods=['GET'])
def get_stats():
    return jsonify(stats.get_stats_dict())


@bp.route('/', methods=['GET'])
def health_check():
    return jsonify(status='OK')
