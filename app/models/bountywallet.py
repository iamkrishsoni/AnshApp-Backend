from ..db import db

class BugBountyWallet(db.Model):
    __tablename__ = 'bug_bounty_wallet'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    total_points = db.Column(db.Integer, default=0)
    recommended_points = db.Column(db.Integer, default=0)

    # Relationship to User
    user = db.relationship('User', back_populates='bug_bounty_wallet')

    # Relationship to BountyPoints
    bounty_points = db.relationship('BountyPoints', backref='wallet', lazy=True)
