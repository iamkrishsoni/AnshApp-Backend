from flask import Blueprint, request, jsonify,url_for, redirect
from authlib.integrations.flask_client import OAuth
from ..models import OTP, User, BountyPoints, BugBountyWallet, Professional, ExpiredToken, Device, RefreshToken
from ..db import db
import jwt
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timedelta
from flask import current_app
from sqlalchemy import or_, and_
from ..utils import token_required
from .aws import send_email, send_sms

oauth = OAuth()

auth_bp = Blueprint('auth', __name__)

ACCESS_TOKEN_EXPIRY = timedelta(days=7)
REFRESH_TOKEN_EXPIRY = timedelta(days=90)
GOOGLE_SECRET_KEY = "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"
GOOGLE_CLIENT_ID="1091879209729-cgcpomne1038165a5k3c5jge2vg90a7l.apps.googleusercontent.com"

google = oauth.register(
    'google',
    consumer_key=GOOGLE_CLIENT_ID,
    consumer_secret=GOOGLE_SECRET_KEY,
    request_token_params={"scope": "email profile"},
    base_url="https://www.googleapis.com/oauth2/v1/",
    request_token_url=None,
    access_token_method="POST",
    access_token_url="https://accounts.google.com/o/oauth2/token",
    authorize_url="https://accounts.google.com/o/oauth2/auth",
)

def generate_jwt_token(user, expires_in):
    payload = {
        "user_id":user.id,
        "user": user.to_dict(),
        "role":"user",
        "exp": (datetime.utcnow() + expires_in).timestamp()
    }
    return jwt.encode(payload, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')

# signup with google
@auth_bp.route("/google/signup", methods=["POST"])
def google_login():
    return google.authorize(callback=url_for("auth.google_authorized", _external=True))

@auth_bp.route("/login/google/callback")
def google_authorized():
    response = google.authorized_response()
    if response is None or response.get("access_token") is None:
        return jsonify({"message": "Google login failed"}), 400

    google_data = google.get("userinfo")
    email = google_data.data["email"]
    
    # Check if user exists
    user = User.query.filter_by(email=email).first()

    if not user:
        user = User(
            user_name=google_data.data["name"],
            email=email,
            signup_using="google",
            email_verified=True,  # Since Google verifies email
        )
        db.session.add(user)
        db.session.commit()

    token = generate_jwt_token(user, ACCESS_TOKEN_EXPIRY)

    return jsonify({"message": "Login successful", "token": token, "user": user.to_dict()}), 200

@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    print("Data in signup request:", data)

    role = data.get('role')
    email = data.get('email')
    phone = data.get('phone')
    password = data.get('password')
    print("Password is here:", password)

    # Determine signup method
    if phone:
        signup_using = 'phone'
    elif email:
        signup_using = 'email'
    else:
        return jsonify({"message": "Either phone or email is required"}), 400

    # Check if user already exists by email or phone
    existing_user = User.query.filter(
        or_(
            and_(User.email == email, email is not None),
            and_(User.phone == phone, phone is not None)
        )
    ).first()
    if existing_user:
        return jsonify({"message": "User already exists"}), 409

    # Create a new user
    new_user = User(
        type='user',  # Default type
        role=role,
        user_name=data.get('user_name', 'Anonymous User'),  # Default to 'Anonymous User' if not provided
        email=email,
        surname=data.get('surname', 'No Surname'),
        phone=phone,
        hashed_password=password,  # Will be set later by the password hash function
        date_of_birth=data.get('date_of_birth', ''),  # Default empty string if not provided
        user_gender=data.get('user_gender', 'Unknown'),  # Default to 'Unknown' if not provided
        location=data.get('location', ''),  # Default to empty string if not provided
        email_verified=False,  # Default to False
        mobile_verified=False,  # Default to False
        term_conditions_signed=False,  # Default to False
        is_anonymous='no',  # Default to 'no'
        user_status=1,  # Default to active status
        sign_up_date=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),  # Set current time as signup date
        signup_using=signup_using  # Store signup method
    )

    # Set the password
    new_user.set_password(password)

    try:
        db.session.add(new_user)
        db.session.flush()  # Flush to get the new user ID before committing

        bug_bounty_wallet = BugBountyWallet(
            user_id=new_user.id,
            total_points=50,
            recommended_points=50,
            # bounty_points=[initial_bounty_points]
        )
        db.session.add(bug_bounty_wallet)
        db.session.flush()
        # Create initial bounty points
        initial_bounty_points = BountyPoints(
            wallet_id=bug_bounty_wallet.id,
            user_id=new_user.id,
            name="Welcome Bonus",
            category="Signup Reward",
            points=50,
            recommended_points=50,
            last_added_points=50,
            date=datetime.utcnow(),
            month=datetime.utcnow().strftime('%m-%Y')
        )
        db.session.add(initial_bounty_points)

        # Create a wallet and link the bounty points

        token = generate_jwt_token(new_user, ACCESS_TOKEN_EXPIRY)
        refresh_token = generate_jwt_token(new_user, REFRESH_TOKEN_EXPIRY)
        
        RefreshToken.revoke_old_tokens(new_user.id, role)
        new_refresh_token = RefreshToken(user_id=new_user.id, token=refresh_token, role=role)
        db.session.add(new_refresh_token)
        db.session.commit()
        
        return jsonify({
            "message": "New registration successful",
            "user": new_user.to_dict(),  # Return full user object
            "bugBountyWallet": {
                "totalPoints": bug_bounty_wallet.total_points,
                "recommendedPoints": bug_bounty_wallet.recommended_points,
                "bountyPoints": [
                    {
                        "id": initial_bounty_points.id,
                        "name": initial_bounty_points.name,
                        "category": initial_bounty_points.category,
                        "points": initial_bounty_points.points,
                        "date": initial_bounty_points.date.strftime("%Y-%m-%d")
                    }
                ]
            },
            "token": token,
            "refresh-token": refresh_token
        }), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Database Error: {e}")
        return jsonify({"message": "An error occurred during registration"}), 500



@auth_bp.route('/signin', methods=['POST'])
def signin():
    data = request.get_json()
    print("data", data)

    email = data.get('email')
    phone = data.get('phone')
    password = data.get('password')

    if not email and not phone:
        return jsonify({"message": "Either email or phone number must be provided"}), 400

    user = None
    login_method = None

    if email:
        user = User.query.filter_by(email=email).first()
        login_method = 'email'
    elif phone:
        user = User.query.filter_by(phone=phone).first()
        login_method = 'phone'

    if user is None:
        return jsonify({"message": "User not found"}), 404

    # Check if the login method matches the signup method
    if user.signup_using != login_method:
        return jsonify({"message": f"You must log in using {user.signup_using}"}), 403

    if not user.check_password(password):
        return jsonify({"message": "Invalid password"}), 401

    token = generate_jwt_token(user, ACCESS_TOKEN_EXPIRY)
    refresh_token = generate_jwt_token(user, REFRESH_TOKEN_EXPIRY)

    RefreshToken.revoke_old_tokens(user.id, user.role)
    new_refresh_token = RefreshToken(user_id=user.id, token=refresh_token, role=user.role)
    db.session.add(new_refresh_token)
    db.session.commit()

    bug_bounty_wallet = BugBountyWallet.query.filter_by(user_id=user.id).first()

    if not bug_bounty_wallet:
        return jsonify({"message": "User does not have a bounty wallet"}), 404

    bounty_points = [
        {
            "id": point.id,
            "name": point.name,
            "category": point.category,
            "points": point.points,
            "date": point.date.strftime("%Y-%m-%d")
        } for point in bug_bounty_wallet.bounty_points
    ]

    return jsonify({
        "message": "Login successful",
        "token": token,
        "refresh-token": refresh_token,
        "user": user.to_dict(),
        "bugBountyWallet": {
            "totalPoints": bug_bounty_wallet.total_points,
            "recommendedPoints": bug_bounty_wallet.recommended_points,
            "bountyPoints": bounty_points
        }
    }), 200

@auth_bp.route('/refresh', methods=['POST'])
def refresh():
    token = request.headers.get('Authorization')
    
    if not token:
        return jsonify({"message": "Token is missing."}), 401
    
    try:
        # Extract the actual token from the Authorization header
        token = token.split(" ")[1]

        # Decode the access token
        decoded_token = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=["HS256"])
        user = decoded_token.get('user')  # Get the entire user object from the token
        role = decoded_token.get('role')  # Access the role from the token

        if not user or not role:
            return jsonify({"message": "Invalid token structure.", "status": "Unauthorized"}), 401

        # Check if the access token is in the expired tokens table
        expired_token = ExpiredToken.query.filter_by(token=token).first()
        if expired_token:
            return jsonify({"message": "User has logged out", "status": "Logged out"}), 401
        
        # Check if the access token is expired
        if datetime.utcfromtimestamp(decoded_token['exp']) < datetime.utcnow():
            # Access token is expired, now check for the refresh token in the database
            refresh_token = RefreshToken.query.filter_by(user_id=user['id'], role=role, revoked=False).first()
            
            if not refresh_token:
                return jsonify({"message": "Refresh token not found or revoked.", "status": "Unauthorized"}), 401
            
            # Generate a new access token and refresh token
            token = generate_jwt_token(user, ACCESS_TOKEN_EXPIRY)
            refresh_token = generate_jwt_token(user, REFRESH_TOKEN_EXPIRY)
        
            RefreshToken.revoke_old_tokens(user.id, role)
            new_refresh_token = RefreshToken(user_id=user.id, token=refresh_token, role=role)
            db.session.add(new_refresh_token)
            db.session.commit()

            return jsonify({
                "message": "New token generated",
                "status": "New token",
                "token": token,
                "refresh-token": refresh_token  # Send the new refresh token
            }), 200

        return jsonify({"message": "Access token is still valid", "status": "Valid token"}), 200

    except jwt.ExpiredSignatureError:
        return jsonify({"message": "Access token has expired.", "status": "Expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"message": "Invalid access token.", "status": "Unauthorized"}), 401


@auth_bp.route('/forgot-password', methods=['POST'])
def forgetPassword():
    data = request.get_json()
    print("data", data)
    
    # Extract fields from the request
    role = data.get('role')
    email = data.get('email')
    phone = data.get('phone')

    # Validate input
    if not role:
        return jsonify({"message": "Role must be provided"}), 400
    if not email and not phone:
        return jsonify({"message": "Either email or phone number must be provided"}), 400

    # Define the target model based on the role
    target_model = None
    if role == 'User':
        target_model = User
    elif role in ['ComfortBuddy', 'Psychologist']:
        target_model = Professional
    else:
        return jsonify({"message": "Invalid role provided"}), 400

    # Dynamically filter user based on email or phone
    user = None
    if email:
        user = target_model.query.filter_by(email=email).first()
    elif phone:
        user = target_model.query.filter_by(phone=phone).first()

    # Handle user not found
    if user is None:
        return jsonify({"message": "User not found"}), 404

    # Check if the professional's type matches the role
    if role == 'ComfortBuddy' and user.type != 'ComfortBuddy':
        return jsonify({"message": "Unauthorized access, invalid professional type"}), 403
    elif role == 'Psychologist' and user.type != 'Psychologist':
        return jsonify({"message": "Unauthorized access, invalid professional type"}), 403

    if email:
        # Send an email with the password
        subject = "Password Recovery"
        content = f"Hello {user.user_name},\n\nYour password is: {user.hashed_password}\n\nRegards,\nSupport Team"
        email_response = send_email(email=email, subject=subject, content=content)
        print(email_response)

        return jsonify({
            "message": "Password recovery email sent",
        }), 200
    
    elif phone:
        # Generate OTP and send it via SMS
        otp = user.hashed_password,  # Generate a 6-digit OTP
        sms_response = send_sms(phone, otp)
        print(sms_response)

        return jsonify({
            "message": "OTP sent to phone",
            "otp": otp,  # In real cases, you wouldn't return the OTP, it's just for demo
        }), 200
@auth_bp.route('/mobile-otp', methods=['POST'])
@token_required
def mobile_otp(current_user):
    data = request.get_json()
    phone = data.get('phone')
    user_id = data.get('user_id')

    if not phone or not user_id:
        return jsonify({"message": "Phone number and user_id are required"}), 400

    # Check if the user ID exists in either the User or Professional table
    user = User.query.get(user_id)
    professional = Professional.query.get(user_id)

    if not user and not professional:
        return jsonify({"message": "User not found"}), 404

    otp_code = OTP.generate_otp()
    transaction_id = OTP.generate_transaction_id()
    expires_at = datetime.utcnow() + timedelta(minutes=5)  # OTP valid for 5 minutes

    token_user_id = current_user.get('user_id')
    if token_user_id != user_id:
        return jsonify({"message": "Authentication error: User ID mismatch"}), 403

    new_otp = OTP(
        user_id=user_id,
        phone=phone,
        otp=otp_code,
        transaction_id=transaction_id,
        expires_at=expires_at
    )
    db.session.add(new_otp)
    db.session.commit()

    return jsonify({
        "otp": otp_code,
        "message": "OTP sent successfully",
        "transaction_id": transaction_id,
        "status": "OTP sent successfully"
    }), 200

@auth_bp.route('/resend-mobile-otp', methods=['POST'])
@token_required
def resend_mobile_otp(current_user):
    data = request.get_json()
    phone = data.get('phone')
    user_id = data.get('user_id')

    if not phone or not user_id:
        return jsonify({"message": "Phone number and user_id are required"}), 400

    otp_code = OTP.generate_otp()
    transaction_id = OTP.generate_transaction_id()
    expires_at = datetime.utcnow() + timedelta(minutes=5)  

    new_otp = OTP(
        user_id=user_id,
        phone=phone,
        otp=otp_code,
        transaction_id=transaction_id,
        expires_at=expires_at
    )
    db.session.add(new_otp)
    db.session.commit()

    return jsonify({
        "otp":otp_code,
        "message": "OTP sent successfully",
        "transaction_id": transaction_id,
        "status": "OTP sent successfully"
    }), 200

@auth_bp.route('/verify-mobile-otp', methods=['POST'])
@token_required
def verify_mobile_otp(current_user):
    data = request.get_json()
    transaction_id = data.get('transaction_id')
    otp_code = data.get('otp')
    user_id = current_user.get('user_id')

    if not transaction_id or not otp_code:
        return jsonify({"message": "Transaction ID and OTP are required"}), 400

    otp_entry = OTP.query.filter_by(transaction_id=transaction_id).first()

    if not otp_entry:
        return jsonify({"message": "Invalid transaction ID"}), 404

    if otp_entry.otp == otp_code and datetime.utcnow() < otp_entry.expires_at:
        user = User.query.get(user_id)
        professional = Professional.query.get(user_id)
        if user:
            user.mobile_verified = True
            db.session.commit()
            return jsonify({"message": "OTP verification successful"}), 200
        elif professional:
            professional.mobile_verified = True
            db.session.commit()
            return jsonify({"message": "OTP verification successful for Professional"}), 200
        else:
            return jsonify({"message": "User not found"}), 40
    else:
        return jsonify({"message": "OTP verification failed or expired"}), 400

@auth_bp.route('/email-otp', methods=['POST'])
@token_required
def email_otp(current_user):
    data = request.get_json()
    email = data.get('email')
    user_id = data.get('user_id')

    if not email or not user_id:
        return jsonify({"message": "Email and user_id are required"}), 400

    # Check if the user exists in User or Professional tables
    user = User.query.get(user_id)
    professional = Professional.query.get(user_id)

    if not user and not professional:
        return jsonify({"message": "User not found"}), 404

    # Generate OTP and transaction ID
    otp_code = OTP.generate_otp()
    transaction_id = OTP.generate_transaction_id()
    expires_at = datetime.utcnow() + timedelta(minutes=5)  # OTP valid for 5 minutes

    # Create a new OTP entry
    new_otp = OTP(
        user_id=user_id,
        email=email,
        otp=otp_code,
        transaction_id=transaction_id,
        expires_at=expires_at
    )
    db.session.add(new_otp)
    db.session.commit()

    # Return the OTP response
    return jsonify({
        "otp": otp_code,
        "message": "OTP sent successfully",
        "transaction_id": transaction_id,
        "status": "OTP sent successfully"
    }), 200

@auth_bp.route('/resend-email-otp', methods=['POST'])
@token_required
def resend_email_otp(current_user):
    data = request.get_json()
    email = data.get('email')
    user_id = data.get('user_id')

    if not email or not user_id:
        return jsonify({"message": "Email Id and user_id are required"}), 400

    otp_code = OTP.generate_otp()
    transaction_id = OTP.generate_transaction_id()
    expires_at = datetime.utcnow() + timedelta(minutes=5)  

    new_otp = OTP(
        user_id=user_id,
        email=email,
        otp=otp_code,
        transaction_id=transaction_id,
        expires_at=expires_at
    )
    db.session.add(new_otp)
    db.session.commit()

    return jsonify({
        "otp":otp_code,
        "message": "OTP sent successfully",
        "transaction_id": transaction_id,
        "status": "OTP sent successfully"
    }), 200

@auth_bp.route('/verify-email-otp', methods=['POST'])
@token_required
def verify_email_otp(current_user):
    data = request.get_json()
    transaction_id = data.get('transaction_id')
    otp_code = data.get('otp')
    user_id = current_user.get('user_id')

    # Validate input data
    if not transaction_id or not otp_code or not user_id:
        return jsonify({"message": "Transaction ID, OTP, and user_id are required"}), 400

    # Find OTP entry by transaction ID
    otp_entry = OTP.query.filter_by(transaction_id=transaction_id).first()

    if not otp_entry:
        return jsonify({"message": "Invalid transaction ID"}), 404

    # Check OTP code and expiry date
    if otp_entry.otp != otp_code:
        return jsonify({"message": "Invalid OTP"}), 400

    if datetime.utcnow() >= otp_entry.expires_at:
        return jsonify({"message": "OTP has expired"}), 400

    # Check if the user exists in User or Professional table
    user = User.query.get(user_id)
    professional = Professional.query.get(user_id)

    if not user and not professional:
        return jsonify({"message": "User not found"}), 404

    # Update email verification for the corresponding entity
    if user:
        user.email_verified = True
    elif professional:
        professional.email_verified = True

    # Commit the changes to the database
    try:
        db.session.commit()
        return jsonify({
            "message": "OTP verification successful",
            "status": "Email verified successfully"
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Error updating verification status", "error": str(e)}), 500

@auth_bp.route('/user/bountypoints', methods=['POST'])
def add_bounty_points(current_user):
    userid = current_user.get('user_id')
    data = request.get_json()

    # Fetch user and their bounty wallet
    user = User.query.get(userid)
    if not user:
        return jsonify({"message": "User not found"}), 404

    # Create new bounty points
    points_to_add = data.get('points', 0)
    if points_to_add <= 0:
        return jsonify({"message": "Invalid points value"}), 400

    # Create bounty points record
    new_bounty_points = BountyPoints(
        user_id=user.id,
        name=data.get('name', 'Bonus'),
        category=data.get('category', 'General'),
        points=points_to_add,
        recommended_points=data.get('recommended_points', 0),
        last_added_points=points_to_add,
        date=datetime.utcnow()
    )
    db.session.add(new_bounty_points)

    # Update total points in the user's wallet
    wallet = BugBountyWallet.query.filter_by(user_id=user.id).first()
    if wallet:
        wallet.total_points += points_to_add
    else:
        wallet = BugBountyWallet(
            user_id=user.id,
            total_points=points_to_add,
            recommended_points=0,
            bounty_points=[new_bounty_points]
        )
        db.session.add(wallet)

    # Commit the changes
    db.session.commit()

    return jsonify({
        "message": "Bounty points added successfully",
        "total_points": wallet.total_points,
        "wallet_id":wallet.id,
        "bountyPoints": {
            "id": new_bounty_points.id,
            "name": new_bounty_points.name,
            "category": new_bounty_points.category,
            "points": new_bounty_points.points,
            "date": new_bounty_points.date.strftime("%Y-%m-%d")
        }
    }), 200
# Update bounty points

@auth_bp.route('/signout', methods=['POST'])
def signout():
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"message": "Token is missing or invalid."}), 401

    token = auth_header.split(" ")[1]
    print("Received token:", token)

    try:
        # Decode JWT access token
        decoded_token = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=["HS256"])
        user_id = decoded_token["user"]["id"]  # Extract user ID
        role = decoded_token["role"]  # Extract user role

        # Blacklist the access token (store in database)
        expired_token = ExpiredToken(token=token, expiration_date=datetime.utcnow())
        db.session.add(expired_token)

        # Revoke all refresh tokens for this user & role
        RefreshToken.revoke_old_tokens(user_id, role)
        # Commit changes
        db.session.commit()

        return jsonify({"message": "Successfully signed out."}), 200

    except jwt.ExpiredSignatureError:
        return jsonify({"message": "Token has already expired."}), 401
    except jwt.InvalidTokenError:
        return jsonify({"message": "Invalid token."}), 401

@auth_bp.route('/device', methods=['POST'])
def store_device():
    data = request.get_json()

    # Validate incoming data
    required_fields = ['role', 'user_id', 'device_name', 'device_model', 'device_os', 'device_os_version', 'device_id']
    
    for field in required_fields:
        if field not in data:
            return jsonify({'message': f'{field} is required'}), 400

    # Determine the model based on the role
    if data['role'] == 'user':
        entity = User.query.get(data['user_id'])
    elif data['role'] == 'professional':
        entity = Professional.query.get(data['user_id'])
    else:
        return jsonify({'message': 'Invalid role'}), 400

    if not entity:
        return jsonify({'message': f'{data["role"].capitalize()} not found'}), 404

    try:
        # Create a new Device object
        device = Device(
            user_id=entity.id,
            device_name=data['device_name'],
            device_model=data['device_model'],
            device_os=data['device_os'],
            device_os_version=data['device_os_version'],
            device_id=data['device_id'],  # Device unique ID
            fcm_token=data.get('fcm_token', None),  # Optional FCM token
            device_manufacturer=data.get('device_manufacturer', None),
            device_screen_size=data.get('device_screen_size', None),
            device_resolution=data.get('device_resolution', None)
        )

        entity.device = device

        db.session.add(device)
        db.session.commit()

        return jsonify({'message': 'Device details stored successfully'}), 201

    except Exception as e:
        return jsonify({'message': str(e)}), 500
    
def register_routes(app):
    app.register_blueprint(auth_bp)
