from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash
from ..models import Schedule, Professional
from ..db import db
from ..utils import token_required  
from sqlalchemy.exc import SQLAlchemyError
from marshmallow import Schema, fields, validate
from datetime import datetime

schedule_bp = Blueprint('schedules', __name__)
@schedule_bp.route('/create', methods=['POST'])
@token_required
def create_schedule():
    data = request.get_json()
    
    professional_id = data.get('professionalId')
    slot_id = data.get('slotId')
    start_time = data.get('startTime')
    end_time = data.get('endTime')
    date = data.get('date')

    if not all([professional_id, slot_id, start_time, end_time, date]):
        return jsonify({"message": "All fields (professionalId, slotId, startTime, endTime, date) are required"}), 400
    
    # Validate Professional Exists
    professional = Professional.query.get(professional_id)
    if not professional:
        return jsonify({"message": "Professional not found"}), 404

    # Convert date/time fields
    try:
        start_time = datetime.strptime(start_time, '%Y-%m-%dT%H:%M:%S')
        end_time = datetime.strptime(end_time, '%Y-%m-%dT%H:%M:%S')
        date = datetime.strptime(date, '%Y-%m-%d')
    except ValueError as e:
        return jsonify({"message": "Invalid date/time format. Use ISO8601 format"}), 400

    # Create the schedule
    schedule = Schedule(
        professional_id=professional_id,
        user_id=data.get('userId', None),
        user_name=data.get('userName', None),
        slot_id=slot_id,
        start_time=start_time,
        end_time=end_time,
        date=date,
        user_looking_for=data.get('userLookingFor', None),
        message_by_user=data.get('messageByUser', None),
        reminder_activated=data.get('reminderActivated', False),
        anonymous=data.get('anonymous', False),
        status=data.get('status', 'active'),
        schedule_type=data.get('scheduleType', "Active"),
        user_attended=data.get('userAttended', False),
        professional_attended=data.get('professionalAttended', False)
    )
    db.session.add(schedule)
    db.session.commit()

    return jsonify({
        "message": "Schedule created successfully",
        "schedule": {
            "id": schedule.id,
            "professionalId": schedule.professional_id,
            "slotId": schedule.slot_id,
            "startTime": schedule.start_time,
            "endTime": schedule.end_time,
            "date": schedule.date.strftime('%Y-%m-%d')
        }
    }), 201

@schedule_bp.route('/update/<int:schedule_id>', methods=['PUT'])
@token_required
def update_schedule(schedule_id):
    data = request.get_json()
    
    # Find the schedule
    schedule = Schedule.query.get(schedule_id)
    if not schedule:
        return jsonify({"message": "Schedule not found"}), 404

    # Update the fields if they exist in the request body
    schedule.user_id = data.get('userId', schedule.user_id)
    schedule.user_name = data.get('userName', schedule.user_name)
    schedule.user_looking_for = data.get('userLookingFor', schedule.user_looking_for)
    schedule.message_by_user = data.get('messageByUser', schedule.message_by_user)
    schedule.reminder_activated = data.get('reminderActivated', schedule.reminder_activated)
    schedule.anonymous = data.get('anonymous', schedule.anonymous)
    schedule.start_time = datetime.strptime(data.get('startTime'), '%Y-%m-%dT%H:%M:%S') if data.get('startTime') else schedule.start_time
    schedule.end_time = datetime.strptime(data.get('endTime'), '%Y-%m-%dT%H:%M:%S') if data.get('endTime') else schedule.end_time
    schedule.date = datetime.strptime(data.get('date'), '%Y-%m-%d') if data.get('date') else schedule.date
    schedule.status = data.get('status', schedule.status)
    schedule.schedule_type = data.get('scheduleType', schedule.schedule_type)
    
    if schedule.status == 'attended':
        schedule.user_attended = data.get('userAttended', schedule.user_attended)
        schedule.professional_attended = data.get('professionalAttended', schedule.professional_attended)
    # Commit the changes
    db.session.commit()

    return jsonify({
        "message": "Schedule updated successfully",
        "schedule": {
            "id": schedule.id,
            "professionalId": schedule.professional_id,
            "userId": schedule.user_id,
            "userName": schedule.user_name,
            "userLookingFor": schedule.user_looking_for,
            "messageByUser": schedule.message_by_user,
            "reminderActivated": schedule.reminder_activated,
            "anonymous": schedule.anonymous,
            "startTime": schedule.start_time.strftime('%Y-%m-%dT%H:%M:%S'),
            "endTime": schedule.end_time.strftime('%Y-%m-%dT%H:%M:%S'),
            "date": schedule.date.strftime('%Y-%m-%d'),
            "status": schedule.status,
            "scheduleType": schedule.schedule_type
        }
    }), 200

@schedule_bp.route('/get/<int:schedule_id>', methods=['GET'])
@token_required
def get_schedule(schedule_id):
    schedule = Schedule.query.get(schedule_id)
    if not schedule:
        return jsonify({"message": "Schedule not found"}), 404

    return jsonify({
        "id": schedule.id,
        "professionalId": schedule.professional_id,
        "userId": schedule.user_id,
        "userName": schedule.user_name,
        "slotId": schedule.slot_id,
        "startTime": schedule.start_time.strftime('%Y-%m-%dT%H:%M:%S'),
        "endTime": schedule.end_time.strftime('%Y-%m-%dT%H:%M:%S'),
        "date": schedule.date.strftime('%Y-%m-%d'),
        "userLookingFor": schedule.user_looking_for,
        "messageByUser": schedule.message_by_user,
        "reminderActivated": schedule.reminder_activated,
        "anonymous": schedule.anonymous,
        "status": schedule.status,
        "scheduleType": schedule.schedule_type
    }), 200

@schedule_bp.route('/delete/<int:schedule_id>', methods=['DELETE'])
@token_required
def delete_schedule(schedule_id):
    schedule = Schedule.query.get(schedule_id)
    if not schedule:
        return jsonify({"message": "Schedule not found"}), 404

    db.session.delete(schedule)
    db.session.commit()
    return jsonify({"message": "Schedule deleted successfully"}), 200

# get all schedules for any specific user
@schedule_bp.route('/user/<int:user_id>/schedules', methods=['GET'])
@token_required
def get_schedules_for_user(user_id):
    schedules = Schedule.query.filter_by(user_id=user_id).all()
    if not schedules:
        return jsonify({"message": "No schedules found for this user"}), 404

    return jsonify([
        {
            "id": schedule.id,
            "professionalId": schedule.professional_id,
            "userId": schedule.user_id,
            "userName": schedule.user_name,
            "slotId": schedule.slot_id,
            "startTime": schedule.start_time.strftime('%Y-%m-%dT%H:%M:%S'),
            "endTime": schedule.end_time.strftime('%Y-%m-%dT%H:%M:%S'),
            "date": schedule.date.strftime('%Y-%m-%d'),
            "userLookingFor": schedule.user_looking_for,
            "messageByUser": schedule.message_by_user,
            "reminderActivated": schedule.reminder_activated,
            "anonymous": schedule.anonymous,
            "status": schedule.status,
            "scheduleType": schedule.schedule_type
        } for schedule in schedules
    ]), 200
    
# get all schedules for any specific professional
@schedule_bp.route('/professional/<int:professional_id>/schedules', methods=['GET'])
@token_required
def get_schedules_for_professional(professional_id):
    schedules = Schedule.query.filter_by(professional_id=professional_id).all()
    if not schedules:
        return jsonify({"message": "No schedules found for this professional"}), 404

    return jsonify([
        {
            "id": schedule.id,
            "professionalId": schedule.professional_id,
            "userId": schedule.user_id,
            "userName": schedule.user_name,
            "slotId": schedule.slot_id,
            "startTime": schedule.start_time.strftime('%Y-%m-%dT%H:%M:%S'),
            "endTime": schedule.end_time.strftime('%Y-%m-%dT%H:%M:%S'),
            "date": schedule.date.strftime('%Y-%m-%d'),
            "userLookingFor": schedule.user_looking_for,
            "messageByUser": schedule.message_by_user,
            "reminderActivated": schedule.reminder_activated,
            "anonymous": schedule.anonymous,
            "status": schedule.status,
            "scheduleType": schedule.schedule_type
        } for schedule in schedules
    ]), 200

@schedule_bp.route('/stats/last-week', methods=['GET'])
@token_required
def get_last_week_statistics():
    today = datetime.utcnow().date()
    last_week = today - timedelta(days=7)

    # Query sessions in the last 7 days
    schedules = Schedule.query.filter(Schedule.date >= last_week, Schedule.date <= today).all()

    stats = {
        "attended": 0,
        "cancelled": 0,
        "scheduled": 0,
    }

    # Count sessions by status
    for schedule in schedules:
        if schedule.status == "attended":
            stats["attended"] += 1
        elif schedule.status == "cancelled":
            stats["cancelled"] += 1
        elif schedule.status == "pending":
            stats["scheduled"] += 1

    return jsonify(stats), 200

