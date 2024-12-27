from flask import Blueprint, request, jsonify
from ..models import Journaling, User, DailyActivity
from ..db import db
from ..utils import token_required
from datetime import datetime

journaling_bp = Blueprint('journaling', __name__)

# Add a new journaling entry
@journaling_bp.route('/add', methods=['POST'])
@token_required
def add_journaling(current_user):  # Assuming `current_user` is passed by the `token_required` decorator
    data = request.get_json()
    try:
        # Create a new Journaling object
        print(current_user)
        new_journal = Journaling(
            user_id=current_user.get('user_id'),  # Use the ID of the currently authenticated user
            title=data['title'],
            description=data.get('description'),
            day_overall=data.get('day_overall'),
            image=data.get('image'),
            audio=data.get('audio'),
            bg_color=data.get('bg_color', "#ffffff"),  # Default value if not provided
            date=datetime.utcnow()  # Ensure UTC date is set
        )

        # Add and commit to the database
        db.session.add(new_journal)
        today = datetime.today().strftime('%Y-%m-%d')
        daily_activity = DailyActivity.query.filter_by(user_id=current_user.get('user_id'), date=today).first()

        # If DailyActivity doesn't exist, create one
        if not daily_activity:
            daily_activity = DailyActivity(
                user_id=current_user.get('user_id'),
                date=today,
                affirmation_completed=False,  # Set default values as False
                journaling=True,
                mindfulness=False,
                goalsetting=False,
                visionboard=False,  # Mark vision board as completed
                app_usage_time=0
            )
            db.session.add(daily_activity)
        else:
            # If DailyActivity exists, update visionboard to True
            daily_activity.journaling = True
        db.session.commit()

        return jsonify({"message": "Journaling entry added successfully!", "data": new_journal.to_dict()}), 201
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
