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
