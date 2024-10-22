from datetime import datetime
from flask_login import UserMixin
from . import db, bcrypt,login_manager 

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(80), nullable=False)
    mobile = db.Column(db.String(15), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    expenses_created = db.relationship('Expense', backref='creator', lazy=True)
    participations = db.relationship('ExpenseParticipant', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    split_type = db.Column(db.String(20), nullable=False)  # 'equal', 'exact', 'percentage'
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    participants = db.relationship('ExpenseParticipant', backref='expense', lazy=True)

class ExpenseParticipant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    expense_id = db.Column(db.Integer, db.ForeignKey('expense.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    share_amount = db.Column(db.Float, nullable=False)  # For exact splits
    share_percentage = db.Column(db.Float)  # For percentage splits