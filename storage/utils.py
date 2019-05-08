from flask import current_app, abort
from datetime import timedelta
import jwt


def check_token(pub_key, token, sub, purpose):

    token_payload = None
    # verify token
    try:
        token_payload = jwt.decode(token,
                                   pub_key,
                                   leeway=current_app.config.get('AUTH_LEEWAY', timedelta(seconds=30)), # give 30 second leeway on time checks
                                   issuer='applogic',
                                   algorithms='RS256')
    except jwt.InvalidSignatureError:
        # signature of token does not match
        abort(403, 'Invalid token signature.')
    except jwt.ExpiredSignatureError:
        # token has expired
        abort(403, 'Token has expired.')
    except jwt.InvalidIssuerError:
        # token issuer is invalid
        abort(403, 'Invalid token issuer.')
    except jwt.exceptions.DecodeError:
        # something went wrong here
        abort(403, 'Invalid token.')

    token_sub = token_payload.get('sub')
    if token_sub is None:
        abort(403, 'No sub field in token.')

    if token_sub != sub:
        abort(403, 'Token sub mismatch.')

    token_purpose = token_payload.get('purpose')
    if token_purpose is None:
        abort(403, 'No purpose field in token.')

    if token_purpose != purpose:
        abort(403, 'Token purpose mismatch.')

    return True