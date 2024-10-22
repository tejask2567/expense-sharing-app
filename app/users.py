from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from .models import User, ExpenseParticipant, Expense, db
from sqlalchemy.exc import IntegrityError

users_bp = Blueprint('users', __name__)

@users_bp.route('/user', methods=['GET'])
@jwt_required()
def get_user_details():
    """Get current user's details"""
    current_user_id = get_jwt_identity()
    user = User.query.get_or_404(current_user_id)
    
    return jsonify({
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'mobile': user.mobile
    }), 200

@users_bp.route('/user', methods=['PUT'])
@jwt_required()
def update_user_details():
    """Update current user's details"""
    current_user_id = get_jwt_identity()
    user = User.query.get_or_404(current_user_id)
    data = request.get_json()
    
    # Fields that are allowed to be updated
    allowed_fields = ['name', 'mobile']
    
    try:
        for field in allowed_fields:
            if field in data:
                setattr(user, field, data[field])
        
        db.session.commit()
        return jsonify({
            'message': 'User details updated successfully',
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'mobile': user.mobile
            }
        }), 200
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Mobile number already in use'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update user details'}), 500

@users_bp.route('/users/search', methods=['GET'])
@jwt_required()
def search_users():
    """Search users by name or email"""
    query = request.args.get('q', '')
    if len(query) < 3:
        return jsonify({'error': 'Search query must be at least 3 characters long'}), 400
    
    users = User.query.filter(
        (User.name.ilike(f'%{query}%')) |
        (User.email.ilike(f'%{query}%'))
    ).limit(10).all()
    
    return jsonify([{
        'id': user.id,
        'name': user.name,
        'email': user.email
    } for user in users]), 200

@users_bp.route('/users/recent-contacts', methods=['GET'])
@jwt_required()
def get_recent_contacts():
    """Get list of users who shared expenses with current user"""
    current_user_id = get_jwt_identity()
    
    # Get unique users from recent expenses (limited to last 5 unique contacts)
    recent_contacts = db.session.query(User).distinct().\
        join(ExpenseParticipant, User.id == ExpenseParticipant.user_id).\
        join(Expense).\
        filter(
            Expense.id.in_(
                db.session.query(Expense.id).\
                join(ExpenseParticipant).\
                filter(ExpenseParticipant.user_id == current_user_id).\
                order_by(Expense.date.desc()).\
                limit(20)
            ),
            User.id != current_user_id
        ).\
        limit(5).\
        all()
    
    return jsonify([{
        'id': user.id,
        'name': user.name,
        'email': user.email
    } for user in recent_contacts]), 200

@users_bp.route('/user/change-password', methods=['PUT'])
@jwt_required()
def change_password():
    """Change user's password"""
    current_user_id = get_jwt_identity()
    user = User.query.get_or_404(current_user_id)
    data = request.get_json()
    
    if not all(k in data for k in ['current_password', 'new_password']):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Verify current password
    if not user.check_password(data['current_password']):
        return jsonify({'error': 'Current password is incorrect'}), 401
    
    # Validate new password
    from .auth import validate_password
    if not validate_password(data['new_password']):
        return jsonify({
            'error': 'New password must be at least 8 characters long and contain uppercase, lowercase, numbers, and special characters'
        }), 400
    
    try:
        user.set_password(data['new_password'])
        db.session.commit()
        return jsonify({'message': 'Password updated successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update password'}), 500

@users_bp.route('/user/balance', methods=['GET'])
@jwt_required()
def get_user_balance():
    """Get user's overall balance with other users"""
    current_user_id = get_jwt_identity()
    
    # Calculate amounts owed by others (where current user is creator)
    owed_by_others = db.session.query(
        User,
        db.func.sum(ExpenseParticipant.share_amount).label('amount')
    ).\
    select_from(User).\
    join(ExpenseParticipant, User.id == ExpenseParticipant.user_id).\
    join(Expense, Expense.id == ExpenseParticipant.expense_id).\
    filter(
        Expense.creator_id == current_user_id,
        ExpenseParticipant.user_id != current_user_id
    ).\
    group_by(User.id).all()
    
    # Calculate amounts owed to others (where current user is participant)
    owed_to_others = db.session.query(
        User,
        db.func.sum(ExpenseParticipant.share_amount).label('amount')
    ).\
    select_from(User).\
    join(Expense, User.id == Expense.creator_id).\
    join(ExpenseParticipant, ExpenseParticipant.expense_id == Expense.id).\
    filter(
        ExpenseParticipant.user_id == current_user_id,
        Expense.creator_id != current_user_id
    ).\
    group_by(User.id).all()
    
    # Compile balances
    balances = {}
    
    # Add amounts owed by others
    for user, amount in owed_by_others:
        balances[user.id] = {
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email
            },
            'amount': amount or 0
        }
    
    # Subtract amounts owed to others
    for user, amount in owed_to_others:
        if user.id in balances:
            balances[user.id]['amount'] -= (amount or 0)
        else:
            balances[user.id] = {
                'user': {
                    'id': user.id,
                    'name': user.name,
                    'email': user.email
                },
                'amount': -(amount or 0)
            }
    
    return jsonify({
        'balances': list(balances.values()),
        'total_balance': sum(b['amount'] for b in balances.values())
    }), 200