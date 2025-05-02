from sqlalchemy import Column, Float, String, Integer
from sqlalchemy.orm import relationship

from src.app import db
import uuid

class User(db.Model):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    uuid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    role = Column(String(10), nullable=False, default='user')
    username = Column(String(40), unique=True, nullable=False)
    password = Column(String(170), nullable=False)
    balance = Column(Float, default=20)

    inventory = relationship('Inventory', back_populates='user')

    def __repr__(self):
        return f"<User(id={self.id}, uuid={self.uuid}, role={self.role}, username={self.username}, password={self.password}, balance={self.balance})>"