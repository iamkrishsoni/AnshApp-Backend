from flask import Blueprint, request, jsonify
from ..db import db
from ..models import VisionBoard, User, DailyActivity, BountyPoints, BountyWallet
from datetime import datetime
from ..utils import token_required

vision_board_bp = Blueprint('vision_board', __name__)


@vision_board_bp.route('/create', methods=['POST'])
@token_required
def create_vision_board(current_user):  # Assuming `current_user` is passed by the `token_required` decorator
    data = request.get_json()

    try:
        # Create a new VisionBoard object
        new_board = VisionBoard(
            user_id=current_user.get('user_id'),  # Use the ID of the currently authenticated user
            date=datetime.utcnow(),
            title=data.get("title"),
            object_0_title=data.get('object_0_title'),
            object_0_image_url=data.get('object_0_image_url'),
            object_1_title=data.get('object_1_title'),
            object_1_image_url=data.get('object_1_image_url'),
            object_2_title=data.get('object_2_title'),
            object_2_image_url=data.get('object_2_image_url'),
            object_3_title=data.get('object_3_title'),
            object_3_image_url=data.get('object_3_image_url'),
            object_4_title=data.get('object_4_title'),
            object_4_image_url=data.get('object_4_image_url'),
        )

        # Add the VisionBoard to the database
        db.session.add(new_board)
        today = datetime.today().strftime('%Y-%m-%d')
        daily_activity = DailyActivity.query.filter_by(user_id=current_user.get('user_id'), date=today).first()

        # If DailyActivity doesn't exist, create one
        if not daily_activity:
            daily_activity = DailyActivity(
                user_id=current_user.get('user_id'),
                date=today,
                affirmation_completed=False,  # Set default values as False
                journaling=False,
                mindfulness=False,
                goalsetting=False,
                visionboard=True,  # Mark vision board as completed
                app_usage_time=0
            )
            db.session.add(daily_activity)
        else:
            # If DailyActivity exists, update visionboard to True
            daily_activity.visionboard = True

        # Logic to award 50 bounty points for first-time vision board creation
        user_id = current_user.get('user_id')
        first_time_vision_board = not VisionBoard.query.filter_by(user_id=user_id).first()  # Check if this is the first vision board

        if first_time_vision_board:
            # Add 50 bounty points
            bounty_points = BountyPoints(
                user_id=user_id,
                name="Vision Board",
                category="First Time Update",
                points=50,
                recommended_points=50,
                last_added_points=50,
                date=datetime.utcnow()
            )
            db.session.add(bounty_points)

            # Update the user's bounty wallet
            wallet = BugBountyWallet.query.filter_by(user_id=user_id).first()
            if wallet:
                wallet.total_points += 50
                wallet.recommended_points += 50

        # Commit the changes to the database
        db.session.commit()

        return jsonify({"message": "VisionBoard created successfully!", "data": new_board.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

# 2. GET Endpoint to retrieve VisionBoard by user
@vision_board_bp.route('/<int:user_id>', methods=['GET'])
@token_required
def get_vision_board(current_user, user_id):
    if current_user.get('user_id') != user_id:  # Ensure the current user can only fetch their own vision boards
        return jsonify({"message": "Unauthorized access!"}), 403

    try:
        # Fetch all vision boards for the user
        vision_boards = VisionBoard.query.filter_by(user_id=user_id).all()

        if not vision_boards:
            return jsonify({"message": "No VisionBoards found for this user!"}), 404

        # Convert each vision board to a dictionary
        vision_boards_data = [board.to_dict() for board in vision_boards]

        return jsonify({
            "message": "VisionBoards retrieved successfully!",
            "data": vision_boards_data
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400



# 3. PUT Endpoint to update an existing VisionBoard
@vision_board_bp.route('/update/<int:board_id>', methods=['PUT'])
@token_required
def update_vision_board(current_user, board_id):
    try:
        # Find the VisionBoard by its ID
        vision_board = VisionBoard.query.get(board_id)

        # Check if the VisionBoard exists
        if not vision_board:
            return jsonify({"message": "VisionBoard not found!"}), 404

        # Ensure the current user owns the vision board
        if vision_board.user_id != current_user.get('user_id'):
            return jsonify({"message": "Unauthorized access! You can only update your own VisionBoard."}), 403

        # Get the data from the request
        data = request.get_json()

        # Update the VisionBoard object with new values
        vision_board.object_0_title = data.get('object_0_title', vision_board.object_0_title)
        vision_board.object_0_image_url = data.get('object_0_image_url', vision_board.object_0_image_url)

        vision_board.object_1_title = data.get('object_1_title', vision_board.object_1_title)
        vision_board.object_1_image_url = data.get('object_1_image_url', vision_board.object_1_image_url)

        vision_board.object_2_title = data.get('object_2_title', vision_board.object_2_title)
        vision_board.object_2_image_url = data.get('object_2_image_url', vision_board.object_2_image_url)

        vision_board.object_3_title = data.get('object_3_title', vision_board.object_3_title)
        vision_board.object_3_image_url = data.get('object_3_image_url', vision_board.object_3_image_url)

        vision_board.object_4_title = data.get('object_4_title', vision_board.object_4_title)
        vision_board.object_4_image_url = data.get('object_4_image_url', vision_board.object_4_image_url)

        # Commit the changes to the database
        db.session.commit()

        return jsonify({"message": "VisionBoard updated successfully!", "data": vision_board.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400
