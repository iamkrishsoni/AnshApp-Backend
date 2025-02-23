from flask import Blueprint, request, jsonify
from ..models import Journaling, User, DailyActivity, BountyPoints, BugBountyWallet
from ..db import db
from ..utils import token_required
from datetime import datetime, timedelta
from sqlalchemy import func

journaling_bp = Blueprint('journaling', __name__)

# Add a new journaling entry
@journaling_bp.route('/add', methods=['POST'])
@token_required
def add_journaling(current_user):  
    data = request.get_json()
    try:
        user_id = current_user.get('user_id')

        # Check if this is the first journaling entry of today
        today = datetime.utcnow().date()  # Get today's date (YYYY-MM-DD)
        existing_journal = Journaling.query.filter_by(user_id=user_id).filter(
            func.date(Journaling.date) == today  # Convert `Journaling.date` to just the date part
        ).first()
        print("existing journaling", existing_journal)

        first_journaling = existing_journal is None # True if no journaling exists for today

        # Create a new Journaling object
        new_journal = Journaling(
            user_id=user_id,
            title=data['title'],
            description=data.get('description'),
            day_overall=data.get('day_overall'),
            image=data.get('image'),
            audio=data.get('audio'),
            bg_color=data.get('bg_color', "#ffffff"),  # Default value if not provided
            date=datetime.utcnow()  
        )

        # Add to database
        db.session.add(new_journal)

        # Handle DailyActivity
        daily_activity = DailyActivity.query.filter_by(user_id=user_id).filter(
            func.date(DailyActivity.date) == today
        ).first()
        if not daily_activity:
            daily_activity = DailyActivity(
                user_id=user_id,
                date=today,
                affirmation_completed=False,  
                journaling=True,  # Set journaling to True
                mindfulness=False,
                goalsetting=False,
                visionboard=False,  
                app_usage_time=0
            )
            db.session.add(daily_activity)
        else:
            daily_activity.journaling = True  # Update journaling status

        # Logic for awarding bounty points
        user = User.query.get(user_id)
        bounty_wallet = BugBountyWallet.query.filter_by(user_id=user.id).first()
        first_time_journaling = not DailyActivity.query.filter_by(user_id=user_id).first()
        if first_time_journaling:
            bounty_points = BountyPoints(
                wallet_id=bounty_wallet.id,
                user_id=user_id,
                name="Journaling",
                category="First Time Update",
                points=30,
                recommended_points=30,
                last_added_points=30,
                date=datetime.utcnow(),
                month=datetime.utcnow().strftime('%m-%Y')
            )
            db.session.add(bounty_points)

            # Update bounty wallet
            if bounty_wallet:
                bounty_wallet.total_points += 30
                bounty_wallet.recommended_points += 30

        # Check for 3 consecutive days of journaling
        last_three_days = [
            (datetime.utcnow() - timedelta(days=i)).strftime('%Y-%m-%d')
            for i in range(3)
        ]
        consecutive_activities = DailyActivity.query.filter(
            DailyActivity.user_id == user_id,
            DailyActivity.date.in_(last_three_days),
            DailyActivity.journaling == True
        ).count()

        if consecutive_activities == 3:
            bounty_points = BountyPoints(
                user_id=user_id,
                name="Journaling",
                category="3 Day Update",
                points=20,
                recommended_points=20,
                last_added_points=20,
                date=datetime.utcnow()
            )
            db.session.add(bounty_points)

            # Update bounty wallet
            if bounty_wallet:
                bounty_wallet.total_points += 20
                bounty_wallet.recommended_points += 20

        # Commit changes
        db.session.commit()

        return jsonify({
            "message": "Journaling entry added successfully!",
            "first_journaling": first_journaling,  # Include this in response
            "data": new_journal.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        print(str(e))
        return jsonify({"error": str(e)}), 400

# Get all journaling entries for the current user
@journaling_bp.route('/get', methods=['GET'])
@token_required
def get_all_journals(current_user):
    try:
        # Filter journals by the current user's ID
        journals = Journaling.query.filter_by(user_id=current_user.get('user_id')).all()
        return jsonify({"data": [journal.to_dict() for journal in journals]}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# Get a specific journaling entry by ID
@journaling_bp.route('/get/<int:journal_id>', methods=['GET'])
@token_required
def get_journal_by_id(current_user, journal_id):
    try:
        journal = Journaling.query.filter_by(id=journal_id, user_id=current_user.get('user_id')).first()
        if not journal:
            return jsonify({"error": "Journal not found"}), 404

        return jsonify({"data": journal.to_dict()}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# Update a specific journaling entry by ID
@journaling_bp.route('/update/<int:journal_id>', methods=['PUT'])
@token_required
def update_journal(current_user, journal_id):
    data = request.get_json()
    try:
        journal = Journaling.query.filter_by(id=journal_id, user_id=current_user.get('user_id')).first()
        if not journal:
            return jsonify({"error": "Journal not found"}), 404

        # Update fields if present in the request
        journal.title = data.get('title', journal.title)
        journal.description = data.get('description', journal.description)
        journal.day_overall = data.get('day_overall', journal.day_overall)
        journal.image = data.get('image', journal.image)
        journal.audio = data.get('audio', journal.audio)
        journal.bg_color = data.get('bg_color', journal.bg_color)

        # Commit changes to the database
        db.session.commit()

        return jsonify({"message": "Journaling entry updated successfully!", "data": journal.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

# Delete a specific journaling entry by ID
@journaling_bp.route('/delete/<int:journal_id>', methods=['DELETE'])
@token_required
def delete_journal(current_user, journal_id):
    try:
        journal = Journaling.query.filter_by(id=journal_id, user_id=current_user.get('user_id')).first()
        if not journal:
            return jsonify({"error": "Journal not found"}), 404

        # Delete the journal
        db.session.delete(journal)
        db.session.commit()

        return jsonify({"message": "Journaling entry deleted successfully!"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400
