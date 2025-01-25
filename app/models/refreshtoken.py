from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from ..db import db

class RefreshToken(db.Model):
    __tablename__ = "refresh_tokens"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False, index=True)
    token_hash = db.Column(db.String(256), nullable=False, unique=True)  # Store hashed token
    role = db.Column(db.String(50), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    issued_at = db.Column(db.DateTime, default=datetime.utcnow)
    revoked = db.Column(db.Boolean, default=False)

    def __init__(self, user_id, token, role, expires_in_days=90):
        self.user_id = user_id
        self.token_hash = generate_password_hash(token)  # Store token securely
        self.role = role
        self.expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def revoke(self):
        self.revoked = True
        db.session.commit()

    @classmethod
    def is_valid(cls, user_id, token, role):
        stored_token = cls.query.filter_by(user_id=user_id, role=role, revoked=False).first()
        if stored_token and check_password_hash(stored_token.token_hash, token):
            if stored_token.expires_at > datetime.utcnow():
                return stored_token
        return None

    @classmethod
    def revoke_old_tokens(cls, user_id, role):
        cls.query.filter_by(user_id=user_id, role=role).delete()
        db.session.commit()
