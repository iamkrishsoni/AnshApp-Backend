from ..db import db
from datetime import datetime

class AppUsage(db.Model):
    __tablename__ = "app_usage"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, nullable=False)  # Foreign key to the user table, if applicable
    date = db.Column(db.Date, nullable=False, default=lambda: datetime.utcnow().date())
    time_spent = db.Column(db.Float, nullable=False, default=0.0)  # Time spent in seconds
    usage_type = db.Column(db.String(255), nullable=False)  # Example: "foreground", "background", etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "date": self.date.isoformat(),
            "time_spent": self.time_spent,
            "usage_type": self.usage_type,
            "created_at": self.created_at.isoformat(),
        }
