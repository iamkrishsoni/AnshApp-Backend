class Reminder(db.Model):
    __tablename__ = 'reminders'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    reminder_text = db.Column(db.String(255), nullable=False)
    reminder_time = db.Column(db.String(50), nullable=False)  # Storing time as string (you can also use DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship('User', back_populates='reminders')

    def __init__(self, reminder_text, reminder_time, user_id):
        self.reminder_text = reminder_text
        self.reminder_time = reminder_time
        self.user_id = user_id

    def to_dict(self):
        return {
            "id": self.id,
            "reminder_text": self.reminder_text,
            "reminder_time": self.reminder_time,
            "user_id": self.user_id
        }