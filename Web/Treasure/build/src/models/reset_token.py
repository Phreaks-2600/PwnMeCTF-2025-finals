from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timedelta

from src.app import db

class ResetToken(db.Model):
    __tablename__ = 'reset_token'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    token = Column(String(255), nullable=False, unique=True)
    expired_at = Column(DateTime, default=lambda: datetime.now() + timedelta(hours=2), nullable=False)

    def is_expired(self):
        if datetime.now() > self.expired_at:
            db.session.delete(self)
            db.session.commit()
            return True
        return False

    def __repr__(self):
        return f"<ResetToken(id={self.id}, user_id={self.user_id}, token={self.token}, expired_at={self.expired_at})>"