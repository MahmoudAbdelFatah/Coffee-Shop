import json
from flask import request, _request_ctx_stack
from functools import wraps
from jose import jwt
from urllib.request import urlopen


AUTH0_DOMAIN = 'udacity-teha.us.auth0.com'
ALGORITHMS = ['RS256']
API_AUDIENCE = 'image'
 
## AuthError Exception
'''
AuthError Exception
A standardized way to communicate auth failure modes
'''
class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


## Auth Header

'''
@TODO implement get_token_auth_header() method
    it should attempt to get the header from the request
        it should raise an AuthError if no header is present
    it should attempt to split bearer and the token
        it should raise an AuthError if the header is malformed
    return the token part of the header
'''
def get_token_auth_header():
    auth_header = request.headers.get("Authorization", None)
    if auth_header is None:
        raise AuthError({
            'success': False,
            'message': 'JWT not found',
            'error': 401
        }, 401)
        
    auth_header_values = auth_header.split(" ")
    if len(auth_header_values) != 2 or auth_header_values[0].lower() != "bearer":
        raise AuthError({
            'success': False,
            'message': 'JWT not found',
            'error': 401
        }, 401)
    return auth_header_values[1]

'''
@TODO implement check_permissions(permission, payload) method
    @INPUTS
        permission: string permission (i.e. 'post:drink')
        payload: decoded jwt payload

    it should raise an AuthError if permissions are not included in the payload
        !!NOTE check your RBAC settings in Auth0
    it should raise an AuthError if the requested permission string is not in the payload permissions array
    return true otherwise
'''
def check_permissions(permission, payload):
    if 'permissions' not in payload:
        raise AuthError({
            'success': False,
            'message': 'Permissions not found in JWT',
            'error': 400
            },)

    if permission not in payload['permissions']:
        raise AuthError({
            'success': False,
            'message': 'Requested Permissions not found',
            'error': 401
            },)

    return True

'''
@TODO implement verify_decode_jwt(token) method
    @INPUTS
        token: a json web token (string)

    it should be an Auth0 token with key id (kid)
    it should verify the token using Auth0 /.well-known/jwks.json
    it should decode the payload from the token
    it should validate the claims
    return the decoded payload

    !!NOTE urlopen has a common certificate error described here: https://stackoverflow.com/questions/50236117/scraping-ssl-certificate-verify-failed-error-for-http-en-wikipedia-org
'''
def verify_decode_jwt(token):
    json_url = "https://{}/.well-known/jwks.json".format(AUTH0_DOMAIN)
    jwks = json.loads(json_url.read())
    unverified_header = jwt.get_unverified_header(token)
    rsa_key = {}
    if 'kid' not in unverified_header:
        raise AuthError({
            'success': False,
            'message': 'Authorization Header is malformed',
            'error': 401,
        }, 401)

    for key in jwks['keys']:
        if key['kid'] == unverified_header['kid']:
            rsa_key = {
                'kty': key['kty'],
                'kid': key['kid'],
                'use': key['use'],
                'n': key['n'],
                'e': key['e']
            }

    if rsa_key:
        try:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=ALGORITHMS,
                audience=API_AUDIENCE,
                issuer='https://{}/'.format(AUTH0_DOMAIN)
            )

            return payload

        except jwt.ExpiredSignatureError:
            raise AuthError({
                'success': False,
                'message': 'Token expired',
                'error': 401,
            }, 401)

        except jwt.JWTClaimsError:
            raise AuthError({
                'success': False,
                'message': 'Incorrect claim',
                'error': 401,
            }, 401)
            
        except Exception:
            raise AuthError({
                'success': False,
                'message': 'Unable to parse the authentication token',
                'error': 400,
            }, 400)
    raise AuthError({
        'success': False,
        'message': 'Unable to find the appropriate key',
        'error': 400,
    }, 400)


'''
@TODO implement @requires_auth(permission) decorator method
    @INPUTS
        permission: string permission (i.e. 'post:drink')

    it should use the get_token_auth_header method to get the token
    it should use the verify_decode_jwt method to decode the jwt
    it should use the check_permissions method validate claims and check the requested permission
    return the decorator which passes the decoded payload to the decorated method
'''
def requires_auth(permission=''):
    def requires_auth_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            tokens = get_token_auth_header()
            payload = verify_decode_jwt(tokens)
            check_permissions(permission, payload)
            return f(payload, *args, **kwargs)

        return wrapper
    return requires_auth_decorator