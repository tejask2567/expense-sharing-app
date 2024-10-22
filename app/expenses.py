from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from flask_jwt_extended import jwt_required, get_jwt_identity
from .models import Expense, ExpenseParticipant, User, db
import csv
from io import StringIO
import datetime
expenses_bp = Blueprint('expenses', __name__)

def validate_split(participants, split_type, total_amount):
    """Validate split amounts based on the split type"""
    if split_type == 'equal':
        share = total_amount / len(participants)
        return [{**p, 'share_amount': share} for p in participants]
    
    elif split_type == 'exact':
        total_shares = sum(p.get('share_amount', 0) for p in participants)
        if abs(total_shares - total_amount) > 0.01:  # Allow small floating-point differences
            return None
        return participants
    
    elif split_type == 'percentage':
        total_percentage = sum(p.get('share_percentage', 0) for p in participants)
        if abs(total_percentage - 100) > 0.01:  # Allow small floating-point differences
            return None
        return [{
            **p,
            'share_amount': (p['share_percentage'] / 100) * total_amount
        } for p in participants]
    
    return None

@expenses_bp.route('/expense', methods=['POST'])
@jwt_required()
def add_expense():
    data = request.get_json()
    required_fields = ['description', 'amount', 'split_type', 'participants']
    
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    if data['split_type'] not in ['equal', 'exact', 'percentage']:
        return jsonify({'error': 'Invalid split type'}), 400
    
    # Validate and process participants
    validated_participants = validate_split(
        data['participants'],
        data['split_type'],
        data['amount']
    )
    
    if not validated_participants:
        return jsonify({'error': 'Invalid split amounts'}), 400
    
    try:
        expense = Expense(
            description=data['description'],
            amount=data['amount'],
            split_type=data['split_type'],
            creator_id=get_jwt_identity()
        )
        db.session.add(expense)
        
        # Add participants
        for participant in validated_participants:
            exp_participant = ExpenseParticipant(
                expense=expense,
                user_id=participant['user_id'],
                share_amount=participant['share_amount'],
                share_percentage=participant.get('share_percentage')
            )
            db.session.add(exp_participant)
        
        db.session.commit()
        return jsonify({'message': 'Expense added successfully', 'expense_id': expense.id}), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to add expense'}), 500

@expenses_bp.route('/expenses/user')
@jwt_required()
def get_user_expenses():
    user_id = get_jwt_identity()
    
    # Get expenses where user is either creator or participant
    expenses = db.session.query(Expense).join(
        ExpenseParticipant
    ).filter(
        (Expense.creator_id == user_id) |
        (ExpenseParticipant.user_id == user_id)
    ).all()
    
    expenses_list = []
    for expense in expenses:
        expense_data = {
            'id': expense.id,
            'description': expense.description,
            'amount': expense.amount,
            'date': expense.date.isoformat(),
            'split_type': expense.split_type,
            'creator': expense.creator.name,
            'participants': [{
                'user_name': p.user.name,
                'share_amount': p.share_amount,
                'share_percentage': p.share_percentage
            } for p in expense.participants]
        }
        expenses_list.append(expense_data)
    
    return jsonify(expenses_list), 200

@expenses_bp.route('/balance-sheet/download')
@jwt_required()
def download_balance_sheet():
    user_id = get_jwt_identity()
    
    # Get all expenses involving the user
    expenses = db.session.query(Expense).join(
        ExpenseParticipant
    ).filter(
        (Expense.creator_id == user_id) |
        (ExpenseParticipant.user_id == user_id)
    ).all()
    
    # Create CSV file
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Date', 'Description', 'Amount', 'Split Type', 'Your Share', 'Status'])
    
    for expense in expenses:
        user_participation = next(
            (p for p in expense.participants if p.user_id == user_id),
            None
        )
        
        status = 'Paid' if expense.creator_id == user_id else 'Owe'
        writer.writerow([
            expense.date.strftime('%Y-%m-%d'),
            expense.description,
            expense.amount,
            expense.split_type,
            user_participation.share_amount if user_participation else 0,
            status
        ])
    
    return jsonify({
        'csv_content': output.getvalue(),
        'filename': f'balance_sheet_{datetime.datetime.now().strftime("%Y%m%d")}.csv'
    }), 200