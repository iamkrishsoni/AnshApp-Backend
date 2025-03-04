from ..db import db
from sqlalchemy.orm import relationship
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash

class Professional(db.Model):
    __tablename__ = 'professionals'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    avatar = db.Column(db.String(500), nullable=True)
    type = db.Column(db.String(50), nullable=False, default='professional')
    specialty = db.Column(db.String(100), nullable=False, default="default")
    soft_skills = db.Column(db.String(255))
    resume = db.Column(db.String(500))
    identity = db.Column(db.String(500))
    bio = db.Column(db.Text)
    ratings_allowed = db.Column(db.String(10), default='yes')
    is_anonymous = db.Column(db.String(10), default='no')
    license_number = db.Column(db.String(500))
    years_of_experience = db.Column(db.Integer)
    user_name = db.Column(db.String(100), nullable=False, default ="user name")
    email = db.Column(db.String(255), unique=True, nullable=True)
    hashed_password = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(15))
    date_of_birth = db.Column(db.Date)
    user_gender = db.Column(db.String(10))
    location = db.Column(db.String(255))
    qualification = db.Column(db.String(255), nullable=True)
    email_verified = db.Column(db.Boolean, default=False)
    mobile_verified = db.Column(db.Boolean, default=False)
    term_conditions_signed = db.Column(db.Boolean, default=True)
    sign_up_date = db.Column(db.String(50))
    user_status = db.Column(db.Integer, nullable=False, default=1)
    signup_using = db.Column(db.String(10), nullable=False, default='phone')
    # New relationship with Schedule
    schedules = db.relationship('Schedule', back_populates='professional', lazy=True)
    # device = db.relationship('Device', back_populates='user', uselist=False)
    
    def to_dict(self):
        return {
            "id": self.id,
            "avatar": self.avatar,
            "role": self.type,
            "specialty": self.specialty,
            "soft_skills": self.soft_skills,
            "resume": self.resume,
            "identity": self.identity,
            "bio": self.bio,
            "ratings_allowed": self.ratings_allowed,
            "is_anonymous": self.is_anonymous,
            "license_number": self.license_number,
            "years_of_experience": self.years_of_experience,
            "user_name": self.user_name,
            "email": self.email,
            "phone": self.phone,
            "date_of_birth": self.date_of_birth.isoformat() if self.date_of_birth else None,  # Convert to string
            "user_gender": self.user_gender,
            "location": self.location,
            "email_verified": self.email_verified,
            "mobile_verified": self.mobile_verified,
            "term_conditions_signed": self.term_conditions_signed,
            "sign_up_date": str(self.sign_up_date) if self.sign_up_date else None,  # Ensure string format
            "user_status": self.user_status,
        }
  