from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash
from ..models import Schedule, Professional, BountyPoints, BugBountyWallet, User
from ..db import db
from ..utils import token_required  
from sqlalchemy.exc import SQLAlchemyError
from marshmallow import Schema, fields, validate
from datetime import datetime, timedelta
from sqlalchemy import cast, DateTime
from ..services import schedule_session_notifications

schedule_bp = Blueprint('schedules', __name__)
@schedule_bp.route('/create', methods=['POST'])
@token_required
def create_schedule(current_user):
    data = request.get_json()
    
    professional_id = data.get('professionalId')
    slot_id = data.get('slotId')
    start_time = data.get('startTime')
    end_time = data.get('endTime')
    date = data.get('date')
    status = data.get('status')

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
        status=data.get('status', 'open'),
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


@schedule_bp.route('/getall', methods=['GET'])
@token_required
def get_all_open_schedules(current_user):
    try:
        # Get the current datetime
        current_time = datetime.utcnow()

        # Query schedules with status 'open' and start_time > current time
        schedules = Schedule.query.filter(
            Schedule.status == 'open',
            Schedule.start_time > current_time
        ).all()

        if not schedules:
            return jsonify({"message": "No open schedules found"}), 404

        # Serialize the schedules including Professional details
        schedules_data = [
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
                "scheduleType": schedule.schedule_type,
                "userAttended": schedule.user_attended,
                "professionalAttended": schedule.professional_attended,
                # Professional details
                "professionalDetails": {
                    "id": schedule.professional.id,
                    "name": schedule.professional.user_name,
                    "email": schedule.professional.email,
                    "type":schedule.professional.type,
                    "phone": schedule.professional.phone,
                    "specialization": schedule.professional.specialty,
                    "dateOfBirth": schedule.professional.date_of_birth,
                    "gender":schedule.professional.user_gender,
                } if schedule.professional else None,
            }
            for schedule in schedules
        ]

        return jsonify(schedules_data), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "An error occurred while fetching schedules", "error": str(e)}), 500

@schedule_bp.route('/update/<int:schedule_id>', methods=['PUT'])
@token_required
def update_schedule(current_user, schedule_id):
    data = request.get_json()
    
    # Find the schedule by ID
    schedule = Schedule.query.get(schedule_id)
    if not schedule:
        return jsonify({"message": "Schedule not found"}), 404

    # Update fields with values from the request
    schedule.user_id = data.get('user_id', schedule.user_id)
    schedule.user_name = data.get('user_name', schedule.user_name)
    schedule.user_looking_for = data.get('user_looking_for', schedule.user_looking_for)
    schedule.message_by_user = data.get('message_by_user', schedule.message_by_user)
    schedule.reminder_activated = data.get('reminder_activated', schedule.reminder_activated)
    schedule.anonymous = data.get('anonymous', schedule.anonymous)
    schedule.start_time = datetime.strptime(data.get('startTime'), '%Y-%m-%dT%H:%M:%S') if data.get('startTime') else schedule.start_time
    schedule.end_time = datetime.strptime(data.get('endTime'), '%Y-%m-%dT%H:%M:%S') if data.get('endTime') else schedule.end_time
    schedule.date = datetime.strptime(data.get('date'), '%Y-%m-%d') if data.get('date') else schedule.date
    schedule.status = data.get('status', schedule.status)
    schedule.schedule_type = data.get('scheduleType', schedule.schedule_type)
    
    if schedule.status == 'attended':
        schedule.user_attended = data.get('userAttended', schedule.user_attended)
        schedule.professional_attended = data.get('professionalAttended', schedule.professional_attended)

    # Check if the status is 'session-completed' to add bounty points
    if schedule.status == 'session-completed':
        # Retrieve the user's wallet
        wallet = BountyWallet.query.filter_by(user_id=schedule.user_id).first()
        if wallet:
            # Update wallet's total points
            wallet.total_points += 50
            wallet.recommended_points += 50

            # Add a new entry to the bounty points
            new_bounty_points = BountyPoints(
                user_id=schedule.user_id,
                name="Session Completed Bonus",
                category="Session Reward",
                points=50,
                recommended_points=50,
                last_added_points=50,
                date=datetime.utcnow()
            )
            db.session.add(new_bounty_points)

    # Commit the changes
    db.session.commit()
    if schedule.reminder_activated:
        schedule_session_notifications(schedule)

    # Return updated schedule
    return jsonify({
        "message": "Schedule updated successfully",
        "schedule": {
            "id": schedule.id,
            "userId": schedule.user_id,
            "userName": schedule.user_name or "Default Name",
            "userLookingFor": schedule.user_looking_for or "",
            "messageByUser": schedule.message_by_user or "",
            "reminderActivated": schedule.reminder_activated,
            "anonymous": schedule.anonymous,
            "startTime": schedule.start_time.strftime('%Y-%m-%dT%H:%M:%S') if schedule.start_time else "",
            "endTime": schedule.end_time.strftime('%Y-%m-%dT%H:%M:%S') if schedule.end_time else "",
            "date": schedule.date.strftime('%Y-%m-%d') if schedule.date else "",
            "status": schedule.status,
            "scheduleType": schedule.schedule_type
        }
    }), 200

@schedule_bp.route('/get/<int:schedule_id>', methods=['GET'])
@token_required
def get_schedule(current_user,schedule_id):
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
def delete_schedule(current_user,schedule_id):
    schedule = Schedule.query.get(schedule_id)
    if not schedule:
        return jsonify({"message": "Schedule not found"}), 404

    db.session.delete(schedule)
    db.session.commit()
    return jsonify({"message": "Schedule deleted successfully"}), 200

# get all schedules for any specific user
@schedule_bp.route('/user/schedules', methods=['GET'])
@token_required
def get_schedules_for_user(current_user):
    userid = current_user.get('user_id')
    # Get the current time
    current_time = datetime.now()
    print(userid)
    print(current_time)

    # Query the schedules, filter for schedules after the current time
    schedules = Schedule.query.filter(
        Schedule.user_id == userid,
    ).all()  # Assuming Schedule has a relationship with Professional
        # cast(Schedule.start_time, DateTime) > current_time
    print(schedules)
    if not schedules:
        return jsonify({"message": "No upcoming schedules found for this user"}), 404

    schedules_data = [
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
            "scheduleType": schedule.schedule_type,
            "userAttended": schedule.user_attended,
            "professionalAttended": schedule.professional_attended,
            # Professional details
            "professionalDetails": {
                "id": schedule.professional.id,
                "name": schedule.professional.user_name,
                "email": schedule.professional.email,
                "phone": schedule.professional.phone,
                "type":schedule.professional.type,
                "specialization": schedule.professional.specialty,
            } if schedule.professional else None,
        }
        for schedule in schedules
    ]
    return jsonify(schedules_data), 200
    
    
# get all schedules for any specific professional
@schedule_bp.route('/professional/<int:professional_id>/schedules', methods=['GET'])
@token_required
def get_schedules_for_professional(current_user, professional_id):
    schedules = Schedule.query.filter_by(professional_id=professional_id).all()
    if not schedules:
        return jsonify({"message": "No schedules found for this professional"}), 404

    schedules_data = [
        {
            "id": schedule.id,
            "professionalId": schedule.professional_id,
            "userId": schedule.user_id,
            "userName": schedule.user.user_name if schedule.user else None,
            "slotId": schedule.slot_id,
            "startTime": schedule.start_time.strftime('%Y-%m-%dT%H:%M:%S'),
            "endTime": schedule.end_time.strftime('%Y-%m-%dT%H:%M:%S'),
            "date": schedule.date.strftime('%Y-%m-%d'),
            "userLookingFor": schedule.user_looking_for,
            "messageByUser": schedule.message_by_user,
            "reminderActivated": schedule.reminder_activated,
            "anonymous": schedule.anonymous,
            "status": schedule.status,
            "scheduleType": schedule.schedule_type,
            "userAttended": schedule.user_attended,
            "professionalAttended": schedule.professional_attended,
            "professionalDetails": {
                "id": schedule.professional.id,
                "name": schedule.professional.user_name,
                "email": schedule.professional.email,
                "phone": schedule.professional.phone,
                "type":schedule.professional.type,
                "specialization": schedule.professional.specialty,
            } if schedule.professional else None,
            # User details
            "userDetails": {
                "id": schedule.user.id,
                "name": schedule.user.user_name,
                "email": schedule.user.email,
                "phone": schedule.user.phone,
                "gender":schedule.user.user_gender,
                "dateOfBirth":schedule.user.date_of_birth
            } if schedule.user else None,
        }
        for schedule in schedules
    ]
    return jsonify(schedules_data), 200

@schedule_bp.route('/stats/lastweek', methods=['GET'])
@token_required
def get_last_week_statistics(current_user):
    professional_id = request.args.get('professional_id')  # Extract `professional_id` from query params
    if not professional_id:
        return jsonify({"error": "Professional ID is required"}), 400

    today = datetime.utcnow().date()
    last_week = today - timedelta(days=7)

        # Query schedules for the given professional in the last 7 days
    schedules = Schedule.query.filter(
        Schedule.professional_id == professional_id,
        Schedule.date >= last_week,
        Schedule.date <= today
    ).all()

    stats = {
        "attended": 0,
        "cancelled": 0,
        "scheduled": 0,  # Pending or open
    }

        # Count schedules based on their status and conditions
    for schedule in schedules:
        if schedule.professional_attended:  # Count attended sessions
            stats["attended"] += 1
        elif schedule.status.lower() == "cancelled":  # Count cancelled sessions
            stats["cancelled"] += 1
        elif schedule.status.lower() in ["booked", "open", "pending"]:  # Count scheduled sessions
            stats["scheduled"] += 1

    return jsonify(stats), 200

