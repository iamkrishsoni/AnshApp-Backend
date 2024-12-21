from ..db import db
from datetime import datetime

class VisionBoard(db.Model):
    __tablename__ = "visionboard"

    # Define the columns
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    title = db.Column(db.String(255), nullable=True)

    # Define the objects (0, 1, 2, 3, 4)
    object_0_title = db.Column(db.String(255), nullable=True)
    object_0_image_url = db.Column(db.String(500), nullable=True)

    object_1_title = db.Column(db.String(255), nullable=True)
    object_1_image_url = db.Column(db.String(500), nullable=True)

    object_2_title = db.Column(db.String(255), nullable=True)
    object_2_image_url = db.Column(db.String(500), nullable=True)

    object_3_title = db.Column(db.String(255), nullable=True)
    object_3_image_url = db.Column(db.String(500), nullable=True)

    object_4_title = db.Column(db.String(255), nullable=True)
    object_4_image_url = db.Column(db.String(500), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "date": self.date.isoformat(),
            "title":self.title,
            "objects": [
                {"id": 0, "title": self.object_0_title, "image_url": self.object_0_image_url},
                {"id": 1, "title": self.object_1_title, "image_url": self.object_1_image_url},
                {"id": 2, "title": self.object_2_title, "image_url": self.object_2_image_url},
                {"id": 3, "title": self.object_3_title, "image_url": self.object_3_image_url},
                {"id": 4, "title": self.object_4_title, "image_url": self.object_4_image_url}
            ]
        }
