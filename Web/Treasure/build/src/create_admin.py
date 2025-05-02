from werkzeug.security import generate_password_hash

from src.app import db
from src.models.user import User

def create_admin(username, password):
    admin_user = User.query.filter_by(role='admin').first()
    hashed_password = generate_password_hash(password)
    if admin_user is None:
        admin_user = User(username=username, password=hashed_password, role='admin', balance=999999)
        db.session.add(admin_user)
    else:
        db.session.query(User).filter_by(username=username).update({'password': hashed_password})
    
    db.session.commit()