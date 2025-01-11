from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from ..models import Professional, BountyPoints
from ..db import db
from ..utils import token_required  
from sqlalchemy.exc import SQLAlchemyError
from marshmallow import Schema, fields, validate
from sqlalchemy import or_, and_
from datetime import datetime, timedelta
import jwt

professional_bp = Blueprint('professional', __name__)

@professional_bp.route('/professionals', methods=['POST'])
def create_professional():
    data = request.get_json()
    print("Data in professional signup request:", data.get('email'))
    try:
        # Ensure at least one of email or phone and password is provided
        if not data.get('password') or not (data.get('email') or data.get('phone')):
            return jsonify({"error": "Password and either email or phone are required."}), 400
        email = data.get('email') or f"noemail{str(datetime.utcnow().timestamp())}@gmail.com"
        phone = data.get('phone')
        # Check if a professional with the same email or phone already exists
        existing_professional = Professional.query.filter(
        or_(
            and_(Professional.email == email, email is not None),
            and_(Professional.phone == phone, phone is not None)
        )
        ).first()

        if existing_professional:
            return jsonify({"error": "A professional with this email or phone already exists."}), 409

        # Hash the password
        hashed_password = data['password']

        # Create a new professional
        professional = Professional(
            email=data.get('email'),
            phone=data.get('phone'),
            hashed_password=hashed_password,
            type=data.get('role', 'professional'),  # Default to 'professional'
            sign_up_date=datetime.utcnow(),
            user_status=1  # Default active status
        )

        db.session.add(professional)
        db.session.commit()  # Commit the professional creation

        # Generate JWT token
        token_data = {
            'user_id': new_user.id,
            'role': "Professionals",
            'exp': (datetime.utcnow() + timedelta(days=365)).timestamp()  # Set expiry to 1 year (365 days)
            }
        token = jwt.encode(token_data, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')

        # Convert professional object to dictionary for JSON response
        professional_data = {
            "id": professional.id,
            "email": professional.email,
            "phone": professional.phone,
            "userName": professional.user_name,
            "type": professional.type,
            "signUpDate": professional.sign_up_date,
            "userStatus": professional.user_status
        }

        return jsonify({
            "message": "Professional account created successfully",
            "user": professional.to_dict(),
            "token": token
        }), 201
    except Exception as e:
        print(str(e))
        return jsonify({"error": str(e)}), 400

@professional_bp.route('/professionals/<int:id>', methods=['GET'])
@token_required
def get_professional(current_user,id):
    """Retrieve a professional account by ID."""
    professional = Professional.query.get(id)
    if not professional:
        return jsonify({"error": "Professional not found"}), 404

    return jsonify({
        "id": professional.id,
        "type": professional.type,
        "specialty": professional.specialty,
        "softSkills": professional.soft_skills,
        "resume": professional.resume,
        "identity": professional.identity,
        "bio": professional.bio,
        "ratingsAllowed": professional.ratings_allowed,
        "isAnonymous": professional.is_anonymous,
        "licenseNumber": professional.license_number,
        "yearsOfExperience": professional.years_of_experience,
        "userName": professional.user_name,
        "email": professional.email,
        "phone": professional.phone,
        "dateOfBirth": professional.date_of_birth,
        "userGender": professional.user_gender,
        "location": professional.location,
        "emailVerified": professional.email_verified,
        "mobileVerified": professional.mobile_verified,
        "termconditionesSigned": professional.term_conditions_signed,
        "signUpDate": professional.sign_up_date,
        "userStatus": professional.user_status
    })


@professional_bp.route('/professionals/<int:id>', methods=['PUT'])
@token_required
def update_professional(current_user,id):
    """Update a professional account by ID."""
    data = request.json
    professional = Professional.query.get(id)
    if not professional:
        return jsonify({"error": "Professional not found"}), 404

    try:
        professional.specialty = data.get('specialty', professional.specialty)
        professional.avatar = data.get('avatar', professional.avatar)
        professional.soft_skills = data.get('softSkills', professional.soft_skills)
        professional.resume = data.get('resume', professional.resume)
        professional.identity = data.get('identity', professional.identity)
        professional.bio = data.get('bio', professional.bio)
        professional.ratings_allowed = data.get('ratingsAllowed', professional.ratings_allowed)
        professional.is_anonymous = data.get('isAnonymous', professional.is_anonymous)
        professional.license_number = data.get('licenseNumber', professional.license_number)
        professional.years_of_experience = data.get('yearsOfExperience', professional.years_of_experience)
        professional.user_name = data.get('userName', professional.user_name)
        professional.email = data.get('email', professional.email)
        professional.phone = data.get('phone', professional.phone)
        professional.date_of_birth = data.get('dateOfBirth', professional.date_of_birth)
        professional.user_gender = data.get('userGender', professional.user_gender)
        professional.location = data.get('location', professional.location)
        professional.email_verified = data.get('emailVerified', professional.email_verified)
        professional.mobile_verified = data.get('mobileVerified', professional.mobile_verified)
        professional.term_conditions_signed = data.get('termconditionesSigned', professional.term_conditions_signed)
        professional.user_status = data.get('userStatus', professional.user_status)

        db.session.commit()
        return jsonify({
            "message": "Professional account updated successfully",
            "user": professional.to_dict(),
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@professional_bp.route('/professionals/<int:id>', methods=['DELETE'])
@token_required
def delete_professional(current_user,id):
    """Delete a professional account by ID."""
    professional = Professional.query.get(id)
    if not professional:
        return jsonify({"error": "Professional not found"}), 404

    try:
        db.session.delete(professional)
        db.session.commit()
        return jsonify({"message": "Professional account deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@professional_bp.route('/signin', methods=['POST'])
def signin():
    data = request.get_json()
    print("data", data)
    email = data.get('email')
    phone = data.get('phone')
    password = data.get('password')
    role = data.get('role')

    if not email and not phone:
        return jsonify({"message": "Either email or phone number must be provided"}), 400

    if not role:
        return jsonify({"message": "Role must be provided"}), 400
    # Dynamically filter based on email or phone
    user = None
    if email:
        user = Professional.query.filter_by(email=email).first()
    elif phone:
        user = Professional.query.filter_by(phone=phone).first()

    if user is None:
        return jsonify({"message": "User not found"}), 404
    
    if role == "ComfortBuddy" and user.type != "ComfortBuddy":
        return jsonify({"message": "Unauthorized role for the user"}), 403

    if role == "Psychologist" and user.type != "Psychologist":
        return jsonify({"message": "Unauthorized role for the user"}), 403
    # Check if the provided password is correct
    if user.hashed_password != password:
        return jsonify({"message": "Invalid password"}), 401

    # Generate JWT token
    token_data = {
        'user_id': user.id,
        'role': "Professional",
        'exp': datetime.utcnow() + timedelta(seconds=current_app.config['JWT_EXPIRATION_DELTA'])
    }
    token = jwt.encode(token_data, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')


    # Return full user data along with token and bug bounty wallet
    return jsonify({
        "message": "Login successful",
        "token": token,
        "user": user.to_dict()
    }), 200

@professional_bp.route('/getpsychologist', methods=['GET'])
@token_required
def getPsychologist(current_user):
    # Retrieve the category from the URL parameters
    category = request.args.get('category')
    
    if not category:
        return jsonify({"error": "Category is required"}), 400

    try:
        # Query the database for psychologists with the specified specialty
        psychologists = Professional.query.filter_by(type='Psychologist', specialty=category).all()
        
        if not psychologists:
            return jsonify({"message": "No psychologists found for the given category"}), 404

        # Convert query results to dictionaries
        results = [psychologist.to_dict() for psychologist in psychologists]
        return jsonify(results), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
