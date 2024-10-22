from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from flask_jwt_extended import (
    create_access_token, 
    jwt_required, 
    get_jwt,
    get_jwt_identity,
    verify_jwt_in_request
)
from .models import User, db
import re
from . import jwt_blocklist, jwt
from datetime import datetime, timezone
auth_bp = Blueprint('auth', __name__)

def validate_password(password):
    """
    Validate password strength:
    - At least 8 characters long
    - Contains uppercase and lowercase letters
    - Contains numbers
    - Contains special characters
    """
    if len(password) < 8:
        return False
    if not re.search(r'[A-Z]', password):
        return False
    if not re.search(r'[a-z]', password):
        return False
    if not re.search(r'[0-9]', password):
        return False
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False
    return True

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['email', 'name', 'mobile', 'password']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Validate email format
    if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', data['email']):
        return jsonify({'error': 'Invalid email format'}), 400
    
    # Validate mobile number
    if not re.match(r'^\+?[\d\s-]{10,}$', data['mobile']):
        return jsonify({'error': 'Invalid mobile number'}), 400
    
    # Validate password strength
    if not validate_password(data['password']):
        return jsonify({
            'error': 'Password must be at least 8 characters long and contain uppercase, lowercase, numbers, and special characters'
        }), 400
    
    # Check if user already exists
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 400
    
    if User.query.filter_by(mobile=data['mobile']).first():
        return jsonify({'error': 'Mobile number already registered'}), 400
    
    # Create new user
    user = User(
        email=data['email'],
        name=data['name'],
        mobile=data['mobile']
    )
    user.set_password(data['password'])
    
    try:
        db.session.add(user)
        db.session.commit()
        access_token = create_access_token(identity=user.id)
        return jsonify({
            'message': 'Registration successful',
            'access_token': access_token
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Registration failed'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not all(k in data for k in ['email', 'password']):
        return jsonify({'error': 'Missing email or password'}), 400
    
    user = User.query.filter_by(email=data['email']).first()
    
    if user and user.check_password(data['password']):
        login_user(user)
        access_token = create_access_token(identity=user.id)
        return jsonify({
            'message': 'Login successful',
            'access_token': access_token
        }), 200
    
    return jsonify({'error': 'Invalid email or password'}), 401

@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    jti = jwt_payload["jti"]
    token_blocked = jwt_blocklist.get(jti, None)
    if token_blocked is None:
        return False
    # Check if the token has expired
    expiry = datetime.fromtimestamp(token_blocked, tz=timezone.utc)
    if datetime.now(timezone.utc) > expiry:
        del jwt_blocklist[jti]
        return False
    return True

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    try:
        # Get JWT claims
        token = get_jwt()
        jti = token["jti"]
        exp = token["exp"]
        
        # Store the token's JTI and expiry time in the blocklist
        jwt_blocklist[jti] = exp
        
        # Also logout from Flask-Login session if user is logged in
        if current_user.is_authenticated:
            logout_user()
        
        return jsonify({'message': 'Logout successful'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500