from flask import Blueprint, request, jsonify
from ..models.reminder import Reminder
from ..db import db
from ..services.reminder_service import schedule_reminder_notifications

reminder_routes = Blueprint('reminder_routes', __name__)

@reminder_routes.route('/', methods=['POST'])
def create_reminder():
    data = request.get_json()
    reminder = Reminder(data['reminder_text'], data['reminder_time'], data['user_id'])
    db.session.add(reminder)
    db.session.commit()

    # Schedule notifications for this reminder
    schedule_reminder_notifications(reminder)

    return jsonify(reminder.to_dict()), 201
