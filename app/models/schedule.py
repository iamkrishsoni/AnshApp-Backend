from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from ..db import db

class Schedule(db.Model):
    __tablename__ = 'schedules'
    
    id = Column(Integer, primary_key=True)
    professional_id = Column(Integer, ForeignKey('professionals.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    user_name = Column(String, nullable=True)
    slot_id = Column(Integer, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    date = Column(DateTime, nullable=False)
    
    # New fields
    user_looking_for = Column(String, nullable=True)  # User's requirements
    message_by_user = Column(String, nullable=True)  # Message left by the user
    reminder_activated = Column(Boolean, default=False)  # Whether a reminder is activated
    anonymous = Column(Boolean, default=False)  # Whether the user wants to remain anonymous
    status = db.Column(db.String(50), nullable=False, default="active")  # Example: pending, confirmed, cancelled
    schedule_type = db.Column(db.String(50)) 
    # Relationships
    professional = relationship("Professional", back_populates="schedules")
    user = relationship("User", back_populates="schedules", lazy=True)
    user_attended = db.Column(db.Boolean, default=False)  # Tracks if the user attended the session
    professional_attended = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return (f"<Schedule(id={self.id}, professional_id={self.professional_id}, "
                f"slot_id={self.slot_id}, date={self.date}, anonymous={self.anonymous})>")
