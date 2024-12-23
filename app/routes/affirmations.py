from ..utils import token_required
from flask import Blueprint, request, jsonify, current_app
from ..models import DailyAffirmation, PermanentAffirmation, User
from ..db import db
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timedelta
from sqlalchemy import or_, and_

affirmation_bp = Blueprint('affirmation', __name__)

# Route for creating Permanent Affirmations
@affirmation_bp.route('/permanent', methods=['POST'])
@token_required
def create_permanent_affirmation(current_user):
    data = request.get_json()
    user_id = data.get('user_id')
    affirmation_text = data.get('affirmation_text')
    reminder_active = data.get('reminder_active', False)
    reminder_time = data.get('reminder_time')

    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    permanent_affirmation = PermanentAffirmation(
        affirmation_text=affirmation_text, 
        user_id=user_id,
        reminder_active=reminder_active,
        reminder_time=reminder_time
    )
    try:
        db.session.add(permanent_affirmation)
        db.session.commit()
        return jsonify({"message": "Permanent affirmation created successfully"}), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 500

# Route for creating Daily Affirmations
@affirmation_bp.route('/daily', methods=['POST'])
@token_required
def create_daily_affirmation(current_user):
    data = request.get_json()
    user_id = data.get('user_id')
    affirmation_text = data.get('affirmation_text')
    reminder_active = data.get('reminder_active', False)
    reminder_time = data.get('reminder_time')

    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    daily_affirmation = DailyAffirmation(
        affirmation_text=affirmation_text,
        user_id=user_id,
        reminder_active=reminder_active,
        reminder_time=reminder_time
    )
    try:
        db.session.add(daily_affirmation)
        db.session.commit()
        return jsonify({"message": "Daily affirmation created successfully"}), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 500

# Route for getting Daily Affirmations for a user
@affirmation_bp.route('/daily', methods=['GET'])
@token_required
def get_daily_affirmations(current_user):
    userid = current_user.get('user_id')
    user = User.query.get(userid)
    if not user:
        return jsonify({"message": "User not found"}), 404

    daily_affirmations = DailyAffirmation.query.filter_by(user_id=user_id).all()
    if not daily_affirmations:
        return jsonify({"message": "No daily affirmations found"}), 404

    affirmations_list = [{
        "affirmation_text": aff.affirmation_text,
        "date": aff.date,
        "reminder_active": aff.reminder_active,
        "reminder_time": aff.reminder_time
    } for aff in daily_affirmations]

    return jsonify(affirmations_list), 200

# Route for getting Permanent Affirmations for a user
@affirmation_bp.route('/permanent', methods=['GET'])
@token_required
def get_permanent_affirmations(current_user):
    userid = current_user.get('user_id')
    user = User.query.get(userid)
    if not user:
        return jsonify({"message": "User not found"}), 404

    permanent_affirmations = PermanentAffirmation.query.filter_by(user_id=user_id).all()
    if not permanent_affirmations:
        return jsonify({"message": "No permanent affirmations found"}), 404

    affirmations_list = [{
        "affirmation_text": aff.affirmation_text,
        "reminder_active": aff.reminder_active,
        "reminder_time": aff.reminder_time
    } for aff in permanent_affirmations]

    return jsonify(affirmations_list), 200