OAUTH2_JWT_ENABLED = True

OAUTH2_JWT_ISS = 'https://authlib.org'
OAUTH2_JWT_KEY = 'secret-key'
OAUTH2_JWT_ALG = 'HS256'

OAUTH2_REFRESH_TOKEN_GENERATOR = True
OAUTH2_ALLOW_IMPLICIT_FLOW = True # I dont know if this actually does something
OAUTH2_TOKEN_EXPIRES_IN = {
    'authorization_code': 864000,
    'implicit': 3600,
    'password': 864000,
    'client_credentials': 864000,
    'refresh_token': 864000
}


# ! Ask for what the secret key and its ISS