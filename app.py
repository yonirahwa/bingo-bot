# app.py - Complete Flask Backend for Bingo Game
# Customized for Telegram Bot & Render Deployment

from flask import Flask, jsonify, request, render_template, send_from_directory
from flask_cors import CORS
from datetime import datetime
import sqlite3
import os
import random
import json
from pathlib import Path

app = Flask(__name__, 
            template_folder='frontend',
            static_folder='frontend',
            static_url_path='')

CORS(app)

# Database setup
DB_PATH = os.path.join(os.path.dirname(__file__), 'bingo.db')

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with tables"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE NOT NULL,
            username TEXT UNIQUE NOT NULL,
            phone TEXT NOT NULL,
            name TEXT,
            language TEXT DEFAULT 'English',
            balance REAL DEFAULT 0.0,
            bonus_balance REAL DEFAULT 0.0,
            profile_pic TEXT,
            referral_code TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Games table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            stake_amount REAL NOT NULL,
            status TEXT DEFAULT 'created',
            cards_selected INTEGER DEFAULT 0,
            called_numbers TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ended_at TIMESTAMP,
            winner_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Cards table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_id INTEGER NOT NULL,
            card_number INTEGER,
            card_data TEXT,
            marked_numbers TEXT,
            FOREIGN KEY (game_id) REFERENCES games(id)
        )
    ''')
    
    # Transactions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            amount REAL NOT NULL,
            method TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Called Numbers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS called_numbers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_id INTEGER NOT NULL,
            number INTEGER NOT NULL,
            called_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (game_id) REFERENCES games(id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

# ===================== FRONTEND ROUTES =====================

@app.route('/')
def index():
    """Serve the main game page"""
    return render_template('index.html')

@app.route('/<path:path>')
def serve_static(path):
    """Serve static files"""
    return send_from_directory('frontend', path)

# ===================== TEST ROUTE =====================

@app.route('/api/test', methods=['GET'])
def test():
    """Test endpoint to verify backend is running"""
    return jsonify({
        'status': 'success',
        'message': 'Bingo Bot Backend is Running!',
        'timestamp': datetime.now().isoformat()
    }), 200

# ===================== USER ROUTES =====================

@app.route('/api/users/register', methods=['POST'])
def register_user():
    """Register a new user"""
    try:
        data = request.json
        telegram_id = data.get('telegram_id')
        username = data.get('username')
        phone = data.get('phone')
        name = data.get('name', username)
        
        if not all([telegram_id, username, phone]):
            return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if user already exists
        cursor.execute('SELECT id FROM users WHERE telegram_id = ?', (telegram_id,))
        if cursor.fetchone():
            conn.close()
            return jsonify({'status': 'error', 'message': 'User already registered'}), 400
        
        # Create referral code
        referral_code = f"ref_{telegram_id}_{random.randint(1000, 9999)}"
        
        # Insert user with welcome bonus
        cursor.execute('''
            INSERT INTO users (telegram_id, username, phone, name, referral_code, balance)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (telegram_id, username, phone, name, referral_code, 10.0))
        
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        
        return jsonify({
            'status': 'success',
            'message': 'User registered successfully',
            'user_id': user_id,
            'telegram_id': telegram_id,
            'balance': 10.0,
            'referral_code': referral_code
        }), 201
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/users/<int:telegram_id>', methods=['GET'])
def get_user(telegram_id):
    """Get user profile"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, telegram_id, username, phone, name, language, 
                   balance, bonus_balance, profile_pic, referral_code, created_at
            FROM users WHERE telegram_id = ?
        ''', (telegram_id,))
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            return jsonify({'status': 'error', 'message': 'User not found'}), 404
        
        return jsonify({
            'status': 'success',
            'user': {
                'id': user['id'],
                'telegram_id': user['telegram_id'],
                'username': user['username'],
                'phone': user['phone'],
                'name': user['name'],
                'language': user['language'],
                'balance': user['balance'],
                'bonus_balance': user['bonus_balance'],
                'profile_pic': user['profile_pic'],
                'referral_code': user['referral_code'],
                'created_at': user['created_at']
            }
        }), 200
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/users/<int:telegram_id>', methods=['PUT'])
def update_user(telegram_id):
    """Update user profile"""
    try:
        data = request.json
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute('SELECT id FROM users WHERE telegram_id = ?', (telegram_id,))
        user = cursor.fetchone()
        if not user:
            conn.close()
            return jsonify({'status': 'error', 'message': 'User not found'}), 404
        
        # Update fields if provided
        if 'name' in data:
            cursor.execute('UPDATE users SET name = ? WHERE telegram_id = ?', 
                         (data['name'], telegram_id))
        if 'phone' in data:
            cursor.execute('UPDATE users SET phone = ? WHERE telegram_id = ?', 
                         (data['phone'], telegram_id))
        if 'language' in data:
            cursor.execute('UPDATE users SET language = ? WHERE telegram_id = ?', 
                         (data['language'], telegram_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'message': 'User updated successfully'
        }), 200
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ===================== GAME ROUTES =====================

@app.route('/api/games/create', methods=['POST'])
def create_game():
    """Create a new bingo game"""
    try:
        data = request.json
        telegram_id = data.get('telegram_id')
        stake_amount = data.get('stake_amount', 1.0)
        
        if not telegram_id:
            return jsonify({'status': 'error', 'message': 'Missing telegram_id'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Get user
        cursor.execute('SELECT id, balance FROM users WHERE telegram_id = ?', (telegram_id,))
        user = cursor.fetchone()
        if not user:
            conn.close()
            return jsonify({'status': 'error', 'message': 'User not found'}), 404
        
        # Check balance
        if user['balance'] < stake_amount:
            conn.close()
            return jsonify({'status': 'error', 'message': 'Insufficient balance'}), 400
        
        # Deduct stake from balance
        cursor.execute('UPDATE users SET balance = balance - ? WHERE id = ?', 
                      (stake_amount, user['id']))
        
        # Create game
        cursor.execute('''
            INSERT INTO games (user_id, stake_amount, status, called_numbers)
            VALUES (?, ?, ?, ?)
        ''', (user['id'], stake_amount, 'created', '[]'))
        
        conn.commit()
        game_id = cursor.lastrowid
        conn.close()
        
        return jsonify({
            'status': 'success',
            'game_id': game_id,
            'stake_amount': stake_amount,
            'message': 'Game created successfully'
        }), 201
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/games/<int:game_id>', methods=['GET'])
def get_game(game_id):
    """Get game details"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, user_id, stake_amount, status, called_numbers, created_at
            FROM games WHERE id = ?
        ''', (game_id,))
        game = cursor.fetchone()
        
        if not game:
            conn.close()
            return jsonify({'status': 'error', 'message': 'Game not found'}), 404
        
        # Get cards for this game
        cursor.execute('SELECT id, card_number, card_data, marked_numbers FROM cards WHERE game_id = ?', 
                      (game_id,))
        cards = cursor.fetchall()
        
        conn.close()
        
        return jsonify({
            'status': 'success',
            'game': {
                'id': game['id'],
                'user_id': game['user_id'],
                'stake_amount': game['stake_amount'],
                'status': game['status'],
                'called_numbers': json.loads(game['called_numbers']),
                'cards': [dict(card) for card in cards],
                'created_at': game['created_at']
            }
        }), 200
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/games/<int:game_id>/select-cards', methods=['POST'])
def select_cards(game_id):
    """Select 1-2 cards for the game"""
    try:
        data = request.json
        num_cards = data.get('num_cards', 1)
        
        if num_cards < 1 or num_cards > 2:
            return jsonify({'status': 'error', 'message': 'Select 1 or 2 cards'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Check game exists
        cursor.execute('SELECT id, status FROM games WHERE id = ?', (game_id,))
        game = cursor.fetchone()
        if not game:
            conn.close()
            return jsonify({'status': 'error', 'message': 'Game not found'}), 404
        
        # Generate cards
        cards_data = []
        for i in range(num_cards):
            # Create a random bingo card (1-75 numbers in 5x5 grid)
            card_numbers = random.sample(range(1, 76), 25)
            card_data = {
                'numbers': card_numbers,
                'grid': [card_numbers[j*5:(j+1)*5] for j in range(5)]
            }
            
            cursor.execute('''
                INSERT INTO cards (game_id, card_number, card_data, marked_numbers)
                VALUES (?, ?, ?, ?)
            ''', (game_id, i+1, json.dumps(card_data), '[]'))
            
            cards_data.append(card_data)
        
        # Update game status
        cursor.execute('UPDATE games SET status = ?, cards_selected = ? WHERE id = ?', 
                      ('playing', num_cards, game_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'game_id': game_id,
            'cards': cards_data,
            'message': f'{num_cards} card(s) selected'
        }), 200
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/games/<int:game_id>/call-number', methods=['POST'])
def call_number(game_id):
    """Call a random number (1-75)"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get game and existing called numbers
        cursor.execute('SELECT called_numbers FROM games WHERE id = ?', (game_id,))
        game = cursor.fetchone()
        if not game:
            conn.close()
            return jsonify({'status': 'error', 'message': 'Game not found'}), 404
        
        called_numbers = json.loads(game['called_numbers'])
        
        # Find next number to call
        available = [n for n in range(1, 76) if n not in called_numbers]
        if not available:
            conn.close()
            return jsonify({'status': 'error', 'message': 'All numbers have been called'}), 400
        
        number = random.choice(available)
        called_numbers.append(number)
        
        # Update game
        cursor.execute('UPDATE games SET called_numbers = ? WHERE id = ?', 
                      (json.dumps(called_numbers), game_id))
        
        # Log called number
        cursor.execute('INSERT INTO called_numbers (game_id, number) VALUES (?, ?)', 
                      (game_id, number))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'number': number,
            'called_numbers': called_numbers
        }), 200
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/games/<int:game_id>/mark-number', methods=['POST'])
def mark_number(game_id):
    """Mark a number on the card"""
    try:
        data = request.json
        card_id = data.get('card_id')
        number = data.get('number')
        
        if not card_id or not number:
            return jsonify({'status': 'error', 'message': 'Missing fields'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Get card
        cursor.execute('SELECT marked_numbers FROM cards WHERE id = ?', (card_id,))
        card = cursor.fetchone()
        if not card:
            conn.close()
            return jsonify({'status': 'error', 'message': 'Card not found'}), 404
        
        marked = json.loads(card['marked_numbers'])
        if number not in marked:
            marked.append(number)
        
        cursor.execute('UPDATE cards SET marked_numbers = ? WHERE id = ?', 
                      (json.dumps(marked), card_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'marked_numbers': marked
        }), 200
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/games/<int:game_id>/check-bingo', methods=['POST'])
def check_bingo(game_id):
    """Check if player won (full card marked)"""
    try:
        data = request.json
        card_id = data.get('card_id')
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Get card
        cursor.execute('SELECT card_data, marked_numbers FROM cards WHERE id = ?', (card_id,))
        card = cursor.fetchone()
        if not card:
            conn.close()
            return jsonify({'status': 'error', 'message': 'Card not found'}), 404
        
        card_data = json.loads(card['card_data'])
        marked = json.loads(card['marked_numbers'])
        
        # Check if all numbers are marked
        all_numbers = card_data['numbers']
        is_bingo = len(marked) == len(all_numbers) and all(n in marked for n in all_numbers)
        
        if is_bingo:
            # Get game and stake amount
            cursor.execute('SELECT user_id, stake_amount FROM games WHERE id = ?', (game_id,))
            game = cursor.fetchone()
            
            # Award winnings (2x stake)
            winnings = game['stake_amount'] * 2
            cursor.execute('UPDATE users SET balance = balance + ? WHERE id = ?', 
                          (winnings, game['user_id']))
            
            # Update game status
            cursor.execute('UPDATE games SET status = ?, ended_at = CURRENT_TIMESTAMP, winner_id = ? WHERE id = ?', 
                          ('won', game['user_id'], game_id))
            
            conn.commit()
            
            return jsonify({
                'status': 'success',
                'is_bingo': True,
                'message': 'Congratulations! You won!',
                'winnings': winnings
            }), 200
        
        conn.close()
        return jsonify({
            'status': 'success',
            'is_bingo': False,
            'message': 'Not a bingo yet'
        }), 200
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ===================== WALLET ROUTES =====================

@app.route('/api/wallet/balance/<int:telegram_id>', methods=['GET'])
def get_balance(telegram_id):
    """Get wallet balance"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT balance, bonus_balance FROM users WHERE telegram_id = ?', (telegram_id,))
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            return jsonify({'status': 'error', 'message': 'User not found'}), 404
        
        return jsonify({
            'status': 'success',
            'balance': user['balance'],
            'bonus_balance': user['bonus_balance']
        }), 200
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/wallet/deposit', methods=['POST'])
def deposit():
    """Deposit funds"""
    try:
        data = request.json
        telegram_id = data.get('telegram_id')
        amount = data.get('amount')
        method = data.get('method', 'TeleBirr')
        
        if not all([telegram_id, amount]):
            return jsonify({'status': 'error', 'message': 'Missing fields'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Get user
        cursor.execute('SELECT id FROM users WHERE telegram_id = ?', (telegram_id,))
        user = cursor.fetchone()
        if not user:
            conn.close()
            return jsonify({'status': 'error', 'message': 'User not found'}), 404
        
        # Add balance
        cursor.execute('UPDATE users SET balance = balance + ? WHERE id = ?', 
                      (amount, user['id']))
        
        # Log transaction
        cursor.execute('''
            INSERT INTO transactions (user_id, type, amount, method, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (user['id'], 'deposit', amount, method, 'completed'))
        
        conn.commit()
        trans_id = cursor.lastrowid
        conn.close()
        
        return jsonify({
            'status': 'success',
            'message': f'Deposit of {amount} successful',
            'transaction_id': trans_id
        }), 200
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/wallet/withdraw', methods=['POST'])
def withdraw():
    """Withdraw funds"""
    try:
        data = request.json
        telegram_id = data.get('telegram_id')
        amount = data.get('amount')
        method = data.get('method', 'Bank')
        
        if not all([telegram_id, amount]):
            return jsonify({'status': 'error', 'message': 'Missing fields'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Get user
        cursor.execute('SELECT id, balance FROM users WHERE telegram_id = ?', (telegram_id,))
        user = cursor.fetchone()
        if not user:
            conn.close()
            return jsonify({'status': 'error', 'message': 'User not found'}), 404
        
        # Check balance
        if user['balance'] < amount:
            conn.close()
            return jsonify({'status': 'error', 'message': 'Insufficient balance'}), 400
        
        # Deduct balance
        cursor.execute('UPDATE users SET balance = balance - ? WHERE id = ?', 
                      (amount, user['id']))
        
        # Log transaction
        cursor.execute('''
            INSERT INTO transactions (user_id, type, amount, method, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (user['id'], 'withdraw', amount, method, 'pending'))
        
        conn.commit()
        trans_id = cursor.lastrowid
        conn.close()
        
        return jsonify({
            'status': 'success',
            'message': f'Withdrawal request of {amount} submitted',
            'transaction_id': trans_id
        }), 200
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/wallet/transfer', methods=['POST'])
def transfer():
    """Transfer funds to another user"""
    try:
        data = request.json
        from_telegram_id = data.get('from_telegram_id')
        to_phone = data.get('to_phone')
        amount = data.get('amount')
        
        if not all([from_telegram_id, to_phone, amount]):
            return jsonify({'status': 'error', 'message': 'Missing fields'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Get sender
        cursor.execute('SELECT id, balance FROM users WHERE telegram_id = ?', (from_telegram_id,))
        sender = cursor.fetchone()
        if not sender:
            conn.close()
            return jsonify({'status': 'error', 'message': 'Sender not found'}), 404
        
        # Check balance
        if sender['balance'] < amount:
            conn.close()
            return jsonify({'status': 'error', 'message': 'Insufficient balance'}), 400
        
        # Get recipient
        cursor.execute('SELECT id FROM users WHERE phone = ?', (to_phone,))
        recipient = cursor.fetchone()
        if not recipient:
            conn.close()
            return jsonify({'status': 'error', 'message': 'Recipient not found'}), 404
        
        # Transfer
        cursor.execute('UPDATE users SET balance = balance - ? WHERE id = ?', 
                      (amount, sender['id']))
        cursor.execute('UPDATE users SET balance = balance + ? WHERE id = ?', 
                      (amount, recipient['id']))
        
        # Log transaction
        cursor.execute('''
            INSERT INTO transactions (user_id, type, amount, method, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (sender['id'], 'transfer', amount, f'to_{to_phone}', 'completed'))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'message': f'Transfer of {amount} to {to_phone} successful'
        }), 200
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ===================== LEADERBOARD ROUTES =====================

@app.route('/api/leaderboard', methods=['GET'])
def get_leaderboard():
    """Get top 50 players by balance"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT username, balance, bonus_balance, created_at
            FROM users
            ORDER BY balance DESC
            LIMIT 50
        ''')
        users = cursor.fetchall()
        conn.close()
        
        leaderboard = [
            {
                'rank': i+1,
                'username': user['username'],
                'balance': user['balance'],
                'bonus_balance': user['bonus_balance']
            }
            for i, user in enumerate(users)
        ]
        
        return jsonify({
            'status': 'success',
            'leaderboard': leaderboard
        }), 200
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/referrals/<int:telegram_id>', methods=['GET'])
def get_referrals(telegram_id):
    """Get referral info"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT referral_code FROM users WHERE telegram_id = ?', (telegram_id,))
        user = cursor.fetchone()
        
        if not user:
            conn.close()
            return jsonify({'status': 'error', 'message': 'User not found'}), 404
        
        referral_code = user['referral_code']
        
        conn.close()
        
        return jsonify({
            'status': 'success',
            'referral_code': referral_code,
            'referral_link': f'https://t.me/YOUR_BOT_NAME?start={referral_code}',
            'referral_count': 0
        }), 200
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ===================== ERROR HANDLERS =====================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'status': 'error', 'message': 'Endpoint not found'}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({'status': 'error', 'message': 'Server error'}), 500

# ===================== RUN SERVER =====================

if __name__ == '__main__':
    # For local development
    app.run(debug=True, host='0.0.0.0', port=5000)
    
    # For production (Render will use this)

    # app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
