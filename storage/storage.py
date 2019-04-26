from flask import Blueprint, jsonify, request, url_for, current_app, abort
import os

bp = Blueprint('storage', __name__, url_prefix='/')


@bp.errorhandler(400)
def bad_request_handler(error):
    return jsonify(error=error.description), 400


@bp.route('/<image_id>', methods=['POST'])
def upload_file(image_id):
    # check if the post request has the file part
    if 'file' not in request.files:
        abort(400, 'No file part')

    file = request.files['file']
    # if user does not select file, browser also
    # submit an empty part without filename
    if file.filename == '':
        abort(400, 'No selected file')

    filename = image_id + '.' + file.filename.rsplit('.', 1)[-1]
    file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
    return jsonify(image_url=url_for('static', filename=filename))


@bp.route('/', methods=['GET'])
def test():
    return jsonify(status='OK')
