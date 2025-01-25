from datetime import datetime
from ..db import db

class ExpiredToken(db.Model):
    __tablename__ = 'expired_tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.Text, nullable=False)  # Changed to Text for longer tokens
    expiration_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ExpiredToken {self.token[:30]}...>'  # Truncate display for readability
