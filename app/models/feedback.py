from ..db import db

class Feedback(db.Model):
    __tablename__ = 'feedback'

    # Define the columns
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    userid = db.Column(db.Integer, nullable=False)
    username = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=True)
    phone = db.Column(db.String(20), nullable=True)  # Phone is nullable
    feedback = db.Column(db.Text, nullable=False)
    ratings = db.Column(db.Integer, nullable=False)  # Assuming ratings are integers, adjust if needed

    def __init__(self, userid, username, email, phone, feedback, ratings):
        self.userid = userid
        self.username = username
        self.email = email
        self.phone = phone
        self.feedback = feedback
        self.ratings = ratings

    def to_dict(self):
        return {
            "userid": self.userid,
            "username": self.username,
            "email": self.email,
            "phone": self.phone,
            "feedback": self.feedback,
            "ratings": self.ratings
        }
