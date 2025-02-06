from ..utils import token_required
from flask import Blueprint, request, jsonify, current_app
from ..models import Notifications
from ..db import db
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timedelta
from sqlalchemy import or_, and_

notifications_bp = Blueprint('notifications',__name__)

@notifications_bp.route("/", methods=['GET'])
@token_required
def get_notifications(current_user):
    user_id = current_user.get('user_id')

    if not user_id:
        return jsonify({"message": "User ID not found"}), 400

    notifications = Notifications.query.filter_by(user_id=user_id).order_by(Notifications.created_at.desc()).all()

    # Serialize notifications
    notifications_data = [notification.to_dict() for notification in notifications]

    return jsonify({
        "message": "Notifications fetched successfully",
        "notifications": notifications_data
    }), 200
    
@notifications_bp.route("/<int:notification_id>", methods=['PATCH'])
@token_required
def update_notification(current_user, notification_id):
    user_id = current_user.get('user_id')

    if not user_id:
        return jsonify({"message": "User ID not found"}), 400

    notification = Notifications.query.filter_by(id=notification_id, user_id=user_id).first()

    if not notification:
        return jsonify({"message": "Notification not found"}), 404

    data = request.json

    # Update notification fields
    if "status" in data:
        notification.status = data["status"]
    if "is_read" in data:
        notification.is_read = data["is_read"]  # ✅ Update read status
    if "live_until" in data:
        notification.live_until = datetime.strptime(data["live_until"], "%Y-%m-%d %H:%M:%S")

    # Commit changes
    try:
        db.session.commit()
        return jsonify({
            "message": "Notification updated successfully",
            "notification": notification.to_dict()
        }), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"message": "Error updating notification", "error": str(e)}), 500
