import logging
import os
import sys
import json
import shutil
from functools import wraps
from os import listdir
from os.path import isfile, join
from flask import request, Response, render_template, abort, jsonify
from flask import Flask
from flask_restful import Resource, Api
from flask_httpauth import HTTPBasicAuth
#from flask uploads import UploadSet, IMAGES
import imghdr

__title__ = 'Prato'

app = Flask(__name__)
api = Api(app)
auth = HTTPBasicAuth()

URL_PREFIX = '/API/V1'
# Users login data are stored in a json file in the server
USERDATA_FILENAME = 'userdata.json'

logger = logging.getLogger('Server log')
# Set the default logging level, actually used if the module is imported:
logger.setLevel(logging.WARN)

userdata = {}
img = ('jpg', 'gif', 'png', 'tif', 'bmp') 

# HTTP STATUS CODES
HTTP_OK = 200
HTTP_CREATED = 201
HTTP_ACCEPTED = 202
HTTP_BAD_REQUEST = 400
HTTP_UNAUTHORIZED = 401
HTTP_FORBIDDEN = 403
HTTP_NOT_FOUND = 404
HTTP_CONFLICT = 409

FILE_ROOT = 'files'



def load_userdata():
    data = {}
    try:
        with open(USERDATA_FILENAME, 'rb') as fp:
            data = json.load(fp, 'utf-8')
    except IOError:
        # If the user data file does not exists, don't raise an exception.
        # (the file will be created with the first user creation)
        pass
    logger.debug('Registered user(s): {}'.format(', '.join(data.keys())))
    logger.info('{:,} registered user(s) found'.format(len(data)))
    return data

def save_userdata():
    """
    Save module level <userdata> dict to disk as json.
    :return: None
    """
    with open(USERDATA_FILENAME, 'wb') as fp:
        json.dump(userdata, fp, 'utf-8', indent=4)
    logger.info('Saved {:,} users'.format(len(userdata)))

def init_user_directory(username):
    """
    Create the default user directory.
    :param username: str
    """
    dirpath = os.path.join(FILE_ROOT, username)
    if os.path.isdir(dirpath):
        shutil.rmtree(dirpath)
        logger.info('"{}" directory removed'.format(dirpath))
    os.makedirs(dirpath)
        
    logger.info('{} created'.format(dirpath))
    return 1


@app.route('{}/signup'.format(URL_PREFIX), methods=['POST'])
def create_user():
    """
    Handle the creation of a new user.
    """
    # Example of creation using requests:
    # requests.post('http://127.0.0.1:5000/API/V1/signup',
    #               data={'username': 'Pippo', 'password': 'ciao'})
    logger.debug('Creating user...')
    username = request.form.get('username')
    password = request.form.get('password')
    if username and password:
        if username in userdata:
            # user already exists!
            response = 'Error: username "{}" already exists!\n'.format(username), HTTP_CONFLICT
        else:
            userdata[username] = password
            save_userdata()
            init_user_directory(username)
            response = 'User "{}" created.\n'.format(username), HTTP_CREATED
    else:
        response = 'Error: username or password is missing.\n', HTTP_BAD_REQUEST
    logger.debug(response)
    return response

def check_path(path, username):
    """
    Check that a path don't fall in other user directories or upper.
    Examples:

    >>> check_path('Photos/myphoto.jpg', 'pippo')
    True
    >>> check_path('Photos/../../ciao.txt', 'paperino')
    False
    """
    path = os.path.abspath(os.path.join(FILE_ROOT, username, path))
    root = os.path.abspath(os.path.join(FILE_ROOT, username))
    if root in path:
        return True
    return False

# ------------------------AUTENTICAZIONE----------------------------

def check_auth(username, password):
    if username in userdata:
        if userdata[username]== password:
            return True
    return False

def authenticate():
    message = {'message': "Authenticate."}
    resp = jsonify(message)

    resp.status_code = 401
    resp.headers['WWW-Authenticate'] = 'Basic realm="Example"'

    return resp

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth: 
            return authenticate()

        elif not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)

    return decorated
#------------------AUTENTICAZIONE----------------------------------

@app.route('{}/upload'.format(URL_PREFIX), methods= ['POST'])
@requires_auth
def upload_file():
    if request.method == 'POST'and img in request.files:
        f = request.files['file']
        username = auth.username()
        dirdir = os.path.join(FILE_ROOT,username)
        f.save(os.path.join(dirdir,'file'))
        return '200'
    else:
        return 'Upload Page'
    
@app.route('{}/lista'.format(URL_PREFIX), methods= ['GET'])
@requires_auth
def lista_file():
    elenco=[]
    if request.method == 'GET':
        username = auth.username()
        dirdir = os.path.join(FILE_ROOT,username)
        dirs = os.listdir(dirdir)
        return 'Logged in as %s' % dirs
        return True
    else:
        return 'lista'

def main():
   
    userdata.update(load_userdata())
    app.run(debug = True)

if __name__ == '__main__':
    main()
