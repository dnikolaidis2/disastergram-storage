from datetime import datetime, timedelta
import jwt
import urllib.parse
import requests


class Storage:

    def __init__(self, baseurl, issuer, private_key):
        self._baseurl = baseurl
        self._issuer = issuer
        self._private_key = private_key if not callable(private_key) else private_key()

    def upload_image(self, image_id, filename, file, mime_type):
        files = {'file': (filename, file, mime_type)}

        token = jwt.encode({
            'iss': self._issuer,
            'sub': image_id,
            'exp': datetime.utcnow() + timedelta(minutes=15),
            'purpose': 'CREATE',
        }, self._private_key, algorithm='RS256')

        return requests.post(urllib.parse.urljoin(self._baseurl, '{}/{}'.format(image_id, token.decode('utf-8'))),
                             files=files)

    def delete_image(self, image_id):

        token = jwt.encode({
            'iss': self._issuer,
            'sub': image_id,
            'exp': datetime.utcnow() + timedelta(minutes=15),
            'purpose': 'DELETE',
        }, self._private_key, algorithm='RS256')

        return requests.delete(urllib.parse.urljoin(self._baseurl, '{}/{}'.format(image_id, token.decode('utf-8'))))

    def gen_image_url(self, image_id):

        token = jwt.encode({
            'iss': self._issuer,
            'sub': image_id,
            'exp': datetime.utcnow() + timedelta(minutes=15),
            'purpose': 'READ',
        }, self._private_key, algorithm='RS256')

        return urllib.parse.urljoin(self._baseurl, '{}/{}'.format(image_id, token.decode('utf-8')))
