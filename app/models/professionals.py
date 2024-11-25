from ..db import db
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash

class Professional(db.Model):
    __tablename__ = 'professionals'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    type = db.Column(db.String(50), nullable=False, default='professional')
    specialty = db.Column(db.String(100), nullable=False)
    soft_skills = db.Column(db.String(255))
    resume = db.Column(db.String(500))
    identity = db.Column(db.String(500))
    bio = db.Column(db.Text)
    ratings_allowed = db.Column(db.String(10), default='yes')
    is_anonymous = db.Column(db.String(10), default='no')
    license_number = db.Column(db.String(100))
    years_of_experience = db.Column(db.Integer)
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
    sign_up_date = db.Column(db.String(50))
    user_status = db.Column(db.Integer, nullable=False, default=1)
    # New relationship with Schedule
    schedules = db.relationship('Schedule', back_populates='professional', lazy=True)