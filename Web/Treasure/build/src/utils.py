from functools import wraps
from flask import redirect, session, url_for, request
import hashlib

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('render.login'))
        return f(*args, **kwargs)
    return decorated_function

def nologin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' in session:
            return redirect(url_for('render.index'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'admin':
            return redirect(url_for('render.index'))
        return f(*args, **kwargs)
    return decorated_function

def localhost_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.headers.get('Host') not in ['127.0.0.1:5000', 'localhost:5000']:
            return f'Forbidden', 403
        return f(*args, **kwargs)
    return decorated_function

def generate_reset_token(username, uuid):
    reset_token = hashlib.sha1(username.encode() + uuid.encode()).hexdigest()
    return reset_token

def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions