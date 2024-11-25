from ..db import db
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    type = db.Column(db.String(50), nullable=False, default='user')
    subtype = db.Column(db.String(100))
    user_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    hashed_password = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(15))
    date_of_birth = db.Column(db.String(10))
    user_gender = db.Column(db.String(10))
    location = db.Column(db.String(255))
    email_verified = db.Column(db.Boolean, default=False)
    mobile_verified = db.Column(db.Boolean, default=False)
    term_conditions_signed = db.Column(db.Boolean, default=False)
    is_anonymous = db.Column(db.String(10), default='no')
    user_status = db.Column(db.Integer, nullable=False, default=1)
    sign_up_date = db.Column(db.String(50))

    # Relationship to BugBountyWallet
    bug_bounty_wallet = db.relationship('BugBountyWallet', back_populates='user', uselist=False)
    schedules = db.relationship('Schedule', back_populates='user', lazy=True)
    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "subtype": self.subtype,
            "user_name": self.user_name,
            "email": self.email,
            "phone": self.phone,
        }

        