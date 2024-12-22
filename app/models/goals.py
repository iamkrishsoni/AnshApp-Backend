from ..db import db 
from datetime import datetime

class Goals(db.Model):
    __tablename__="goals"
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    userid = db.Column(db.Integer, nullable=False)
    title = db.Column(db.Text, nullable = False)
    description = db.Column(db.Text, nullable = True)
    image = db.Column(db.String(500), nullable=True)
    type=db.Column(db.String(255), nullable=False)
    start_time = db.Column(db.Time, nullable=True)  # For daily goals
    end_time = db.Column(db.Time, nullable=True)    # For daily goals
    start_date = db.Column(db.Date, nullable=True)  # For monthly and yearly goals
    end_date = db.Column(db.Date, nullable=True)    # For monthly and yearly goals
    status = db.Column(db.String(255), default="Added", nullable=False)
    
    def to_dict(self):
        
        return {
            "id": self.id,
            "userid": self.userid,
            "title": self.title,
            "description": self.description,
            "image": self.image,
            "type": self.type,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "status": self.status,
        }