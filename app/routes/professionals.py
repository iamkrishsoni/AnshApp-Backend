from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from ..models import Professional, BountyPoints
from ..db import db
from ..utils import token_required  
from sqlalchemy.exc import SQLAlchemyError
from marshmallow import Schema, fields, validate
from datetime import datetime, timedelta
import jwt

professional_bp = Blueprint('professional', __name__)

@professional_bp.route('/professionals', methods=['POST'])
def create_professional():
    data = request.json
    try:
        # Check if professional with the same email already exists
        existing_professional = Professional.query.filter(
            (Professional.email == data['email']) | (Professional.phone == data.get('phone'))
        ).first()

        # If professional already exists, return error message
        if existing_professional:
            return jsonify({"error": "A professional with this email or phone number already exists."}), 409

        # Create a new professional if not already existing
        professional = Professional(
            type=data.get('type', 'professional'),
            specialty=data['specialty'],
            soft_skills=data.get('softSkills'),
            resume=data.get('resume'),
            identity=data.get('identity'),
            bio=data.get('bio'),
            ratings_allowed=data.get('ratingsAllowed', 'yes'),
            is_anonymous=data.get('isAnonymous', 'no'),
            license_number=data.get('licenseNumber'),
            years_of_experience=data.get('yearsOfExperience', 0),
            user_name=data['userName'],
            email=data['email'],
            hashed_password=data['password'],
            phone=data.get('phone'),
            date_of_birth=data.get('dateOfBirth'),
            user_gender=data.get('userGender'),
            location=data.get('location'),
            email_verified=data.get('emailVerified', False),
            mobile_verified=data.get('mobileVerified', False),
            term_conditions_signed=data.get('termconditionesSigned', False),
            sign_up_date=data.get('signUpDate'),
            user_status=data.get('userStatus', 1)
        )

        db.session.add(professional)
        db.session.commit()

        # Generate JWT token
        token_data = {
            'user_id': professional.id,
            'role': 'Professional',  # Corrected typo here ('Preofessional' to 'Professional')
            'exp': datetime.utcnow() + timedelta(seconds=current_app.config['JWT_EXPIRATION_DELTA'])
        }
        token = jwt.encode(token_data, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')
        professional_data = professional.to_dict()
        return jsonify({"message": "Professional account created successfully", "id": professional.id, "token": token,"professional": professional_data}), 201
    except Exception as e:
        print(str(e))
        return jsonify({"error": str(e)}), 400


@professional_bp.route('/professionals/<int:id>', methods=['GET'])
@token_required
def get_professional(id):
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
def update_professional(id):
    """Update a professional account by ID."""
    data = request.json
    professional = Professional.query.get(id)
    if not professional:
        return jsonify({"error": "Professional not found"}), 404

    try:
        professional.specialty = data.get('specialty', professional.specialty)
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
        return jsonify({"message": "Professional account updated successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@professional_bp.route('/professionals/<int:id>', methods=['DELETE'])
@token_required
def delete_professional(id):
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

    if not email and not phone:
        return jsonify({"message": "Either email or phone number must be provided"}), 400

    # Dynamically filter based on email or phone
    user = None
    if email:
        user = Professional.query.filter_by(email=email).first()
    elif phone:
        user = Professional.query.filter_by(phone=phone).first()

    if user is None:
        return jsonify({"message": "User not found"}), 404

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

