from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship

from src.app import db

class Inventory(db.Model):
    __tablename__ = 'inventory'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    item_id = Column(Integer, nullable=False)
    rarity = Column(String, nullable=False)
    name = Column(String, nullable=False)
    image = Column(String, nullable=False)
    quantity = Column(Integer, default=1)
    
    user = relationship('User', back_populates='inventory')

    def __repr__(self):
        return f"<Inventory(id={self.id}, user_id={self.user_id}, item_id={self.item_id}, rarity={self.rarity}, name={self.name}, image={self.image}, quantity={self.quantity})>"