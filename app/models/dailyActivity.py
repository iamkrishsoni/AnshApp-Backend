from datetime import datetime
from ..db import db

class DailyActivity(db.Model):
    __tablename__ = 'daily_activity'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    date = db.Column(db.String(10), nullable=False, default=datetime.today().strftime('%Y-%m-%d'))
    affirmation_completed = db.Column(db.Boolean, default=False)
    journaling = db.Column(db.Boolean, default=False)
    mindfulness = db.Column(db.Boolean, default=False)
    goalsetting = db.Column(db.Boolean, default=False)
    visionboard = db.Column(db.Boolean, default=False)
    app_usage_time = db.Column(db.Integer, default=0)  # Time in minutes
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationship to User model
    user = db.relationship('User', back_populates='daily_activities')

    def to_dict(self):
        return {
            "date": self.date,
            "affirmation_completed": self.affirmation_completed,
            "journaling": self.journaling,
            "mindfulness": self.mindfulness,
            "goalsetting": self.goalsetting,
            "visionboard": self.visionboard,
            "app_usage_time": self.app_usage_time
        }

# Add the relationship to the User model

