from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import secrets

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_urlsafe(32)
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['ADMIN_PASSWORD'] = secrets.token_hex(32)
app.config['ADMIN_UPLOAD_FOLDER'] = 'src/admin_data_uploaded'
db = SQLAlchemy(app)

from .blueprints.render import render_bp
from .blueprints.api import api_bp

app.register_blueprint(render_bp, url_prefix='/')
app.register_blueprint(api_bp, url_prefix='/api')

from src.models.user import User
from src.models.inventory import Inventory
from src.models.reset_token import ResetToken
from src.create_admin import create_admin

with app.app_context():
    db.create_all()
    create_admin(username='admin', password=app.config['ADMIN_PASSWORD'])