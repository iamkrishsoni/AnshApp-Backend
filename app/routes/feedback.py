from flask import Blueprint, request, jsonify
from ..models import Feedback, BountyPoints, BugBountyWallet
from ..db import db

feedback_bp = Blueprint('feedback', __name__)

@feedback_bp.route('/submit', methods=['POST'])
def submitFeedback():
    data = request.get_json()

    # Extract the required fields from the request
    userid = data.get('userid')
    username = data.get('username')
    email = data.get('email')
    phone = data.get('phone')
    feedback = data.get('feedback')
    ratings = data.get('ratings')

    # Validate the required fields
    if not userid or not username or not feedback or ratings is None:
        return jsonify({"message": "Missing required fields"}), 400

    # Create a new Feedback instance
    new_feedback = Feedback(
        userid=userid,
        username=username,
        email=email,  # email can be None
        phone=phone,  # phone can be None
        feedback=feedback,
        ratings=ratings
    )

    # Add the new feedback to the database
    try:
        db.session.add(new_feedback)
        wallet = BugBountyWallet.query.filter_by(user_id=userid).first()
        new_bounty_points = BountyPoints(
            wallet_id=wallet.id,
            user_id=userid,
            name="Feedback Submission",
            category="Feedback",
            points=10,
            recommended_points=10,
            last_added_points=10,
        )
        db.session.add(new_bounty_points)

        # Update the wallet's total and recommended points
        wallet.total_points += 10
        wallet.recommended_points += 10
        db.session.commit()
        return jsonify({"message": "Feedback submitted successfully"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Error: {str(e)}"}), 500
