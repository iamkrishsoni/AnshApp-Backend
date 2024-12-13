from flask import Blueprint, request, jsonify
from ..db import db
from datetime import datetime
from ..models import BountyPoints

bounty_bp = Blueprint('bounty',__name__)

@bounty_bp.route('/update', methods=['POST'])
def update_bounty_points():
    try:
        # Parse the input data
        data = request.get_json()
        wallet_id = data.get('wallet_id')
        user_id = data.get('user_id')
        category = data.get('category')
        points = data.get('points')
        
        if not all([wallet_id, user_id, category, points]):
            return jsonify({'error': 'All fields are required'}), 400

        # Query the database for an existing record
        bounty = BountyPoints.query.filter_by(wallet_id=wallet_id, user_id=user_id, category=category).first()

        if bounty:
            # Update existing record
            bounty.points += points
            bounty.last_added_points = points
            bounty.date = datetime.utcnow()
        else:
            # Create a new record
            bounty = BountyPoints(
                wallet_id=wallet_id,
                user_id=user_id,
                category=category,
                points=points,
                recommended_points=0,  # Default or calculated value
                last_added_points=points,
                date=datetime.utcnow()
            )
            db.session.add(bounty)

        # Commit the changes
        db.session.commit()
        return jsonify({'message': 'Bounty points updated successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500