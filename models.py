# models.py - Database models for Bingo Bot
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
import json

# Initialize SQLAlchemy
db = SQLAlchemy()

# ==================== USER MODEL ====================
class User(db.Model):
    """User model to store player information"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    telegram_id = db.Column(db.Integer, unique=True, nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    name = db.Column(db.String(100), nullable=True)
    language = db.Column(db.String(10), default='en')
    balance = db.Column(db.Float, default=0.0)
    bonus_balance = db.Column(db.Float, default=0.0)
    profile_pic = db.Column(db.String(255), nullable=True)
    referral_code = db.Column(db.String(20), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    games = db.relationship('Game', backref='player', lazy=True)
    transactions = db.relationship('Transaction', backref='user', lazy=True)
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def to_dict(self):
        """Convert user to dictionary"""
        return {
            'id': self.id,
            'telegram_id': self.telegram_id,
            'username': self.username,
            'phone': self.phone,
            'name': self.name,
            'language': self.language,
            'balance': self.balance,
            'bonus_balance': self.bonus_balance,
            'profile_pic': self.profile_pic,
            'referral_code': self.referral_code,
            'created_at': self.created_at.isoformat()
        }


# ==================== GAME MODEL ====================
class Game(db.Model):
    """Game model to track each bingo game"""
    __tablename__ = 'games'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    stake_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, active, completed
    card1_data = db.Column(db.Text)  # JSON format
    card2_data = db.Column(db.Text, nullable=True)  # JSON format
    called_numbers = db.Column(db.Text, default='[]')  # JSON array
    winner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    cards = db.relationship('Card', backref='game', lazy=True, cascade='all, delete-orphan')
    called = db.relationship('CalledNumber', backref='game', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Game {self.id} - User {self.user_id}>'
    
    def get_called_numbers(self):
        """Get called numbers as list"""
        return json.loads(self.called_numbers)
    
    def add_called_number(self, number):
        """Add a called number"""
        numbers = self.get_called_numbers()
        if number not in numbers:
            numbers.append(number)
        self.called_numbers = json.dumps(numbers)
    
    def to_dict(self):
        """Convert game to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'stake_amount': self.stake_amount,
            'status': self.status,
            'card1_data': json.loads(self.card1_data) if self.card1_data else None,
            'card2_data': json.loads(self.card2_data) if self.card2_data else None,
            'called_numbers': self.get_called_numbers(),
            'created_at': self.created_at.isoformat()
        }


# ==================== CARD MODEL ====================
class Card(db.Model):
    """Card model to store individual bingo cards"""
    __tablename__ = 'cards'
    
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'), nullable=False)
    card_number = db.Column(db.Integer)  # 1 or 2
    card_data = db.Column(db.Text)  # JSON format with 75 numbers
    marked_numbers = db.Column(db.Text, default='[]')  # JSON array of marked numbers
    is_winner = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<Card {self.id} - Game {self.game_id}>'
    
    def get_marked_numbers(self):
        """Get marked numbers as list"""
        return json.loads(self.marked_numbers)
    
    def mark_number(self, number):
        """Mark a number on the card"""
        marked = self.get_marked_numbers()
        if number not in marked:
            marked.append(number)
        self.marked_numbers = json.dumps(marked)
    
    def check_win(self):
        """Check if card has all 75 numbers marked (bingo!)"""
        marked = self.get_marked_numbers()
        return len(marked) == 75
    
    def to_dict(self):
        """Convert card to dictionary"""
        return {
            'id': self.id,
            'game_id': self.game_id,
            'card_number': self.card_number,
            'card_data': json.loads(self.card_data) if self.card_data else None,
            'marked_numbers': self.get_marked_numbers(),
            'is_winner': self.is_winner
        }


# ==================== TRANSACTION MODEL ====================
class Transaction(db.Model):
    """Transaction model to track wallet operations"""
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    transaction_type = db.Column(db.String(20))  # deposit, withdraw, transfer
    amount = db.Column(db.Float, nullable=False)
    method = db.Column(db.String(20))  # telebirr, cbe, commercial
    status = db.Column(db.String(20), default='pending')  # pending, completed, failed
    description = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Transaction {self.id} - {self.transaction_type}>'
    
    def to_dict(self):
        """Convert transaction to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'transaction_type': self.transaction_type,
            'amount': self.amount,
            'method': self.method,
            'status': self.status,
            'description': self.description,
            'created_at': self.created_at.isoformat()
        }


# ==================== CALLED NUMBER MODEL ====================
class CalledNumber(db.Model):
    """CalledNumber model to track numbers called during games"""
    __tablename__ = 'called_numbers'
    
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'), nullable=False)
    number = db.Column(db.Integer, nullable=False)
    called_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<CalledNumber {self.number} - Game {self.game_id}>'
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'game_id': self.game_id,
            'number': self.number,
            'called_at': self.called_at.isoformat()
        }