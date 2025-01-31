from ..db import db
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    avatar = db.Column(db.String(500), nullable=True)
    role = db.Column(db.String(50), nullable=False, default='user')
    type = db.Column(db.String(50), nullable=False, default='user')
    subtype = db.Column(db.String(100))
    user_name = db.Column(db.String(100), nullable=False)
    surname = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    hashed_password = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(15))
    date_of_birth = db.Column(db.String(10))
    user_gender = db.Column(db.String(10))
    location = db.Column(db.String(255))
    email_verified = db.Column(db.Boolean, default=False)
    mobile_verified = db.Column(db.Boolean, default=False)
    term_conditions_signed = db.Column(db.Boolean, default=False)
    is_anonymous = db.Column(db.String(10), default='no')
    plan= db.Column(db.String(255), default='basic')
    user_status = db.Column(db.Integer, nullable=False, default=1)
    sign_up_date = db.Column(db.String(50))
    permanent_affirmation = db.relationship('PermanentAffirmation', back_populates='user', uselist=False)
    daily_affirmations = db.relationship('DailyAffirmation', back_populates='user')
    reminders = db.relationship('Reminder', back_populates='user')
    daily_activities = db.relationship('DailyActivity', back_populates='user')
    # Relationship to BugBountyWallet
    bug_bounty_wallet = db.relationship('BugBountyWallet', back_populates='user', uselist=False)
    schedules = db.relationship('Schedule', back_populates='user')
    device = db.relationship('Device', back_populates='user', uselist=False)
    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)

    def to_dict(self):
        return {
            "id": self.id,
            "avatar":self.avatar,
            "role": self.role,
            "user_name": self.user_name,
            "email": self.email,
            "phone": self.phone,
            "date_of_birth": self.date_of_birth,
            "user_gender": self.user_gender,
            "location": self.location,
            "email_verified": self.email_verified,
            "mobile_verified": self.mobile_verified,
            "term_conditions_signed": self.term_conditions_signed,
            "is_anonymous": self.is_anonymous,
            "user_status": self.user_status,
            "plan": self.plan,
            "sign_up_date": self.sign_up_date,
            "surname":self.surname,
            "device": self.device.to_dict() if self.device else None
        }

        