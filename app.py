from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
import os
from dotenv import load_dotenv
import hashlib
import logging
from datetime import datetime, timedelta
from database import get_all_users, get_user_messages, search_messages, search_users, get_user_stats, get_db_connection, init_db
import psycopg2
from psycopg2.extras import RealDictCursor
import sys

load_dotenv()

app = Flask(__name__, template_folder='templates')
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
CORS(app)

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)

logger.info("Flask app initialized")
logger.info(f"Template folder: {app.template_folder}")

# Initialize database on startup
try:
    init_db()
    logger.info("Database initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize database: {e}")

# ==================== HELPER FUNCTIONS ====================

def hash_token(token):
    """Hash Discord token for storage"""
    return hashlib.sha256(token.encode()).hexdigest()

def store_session(discord_id, token_hash):
    """Store user session in database"""
    conn = get_db_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO sessions (discord_id, token_hash, created_at, last_activity)
            VALUES (%s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT (discord_id) DO UPDATE
            SET token_hash = %s, last_activity = CURRENT_TIMESTAMP
        """, (discord_id, token_hash, token_hash))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error storing session: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def verify_session(discord_id, token_hash):
    """Verify if session is valid"""
    conn = get_db_connection()
    if not conn:
        return False
    
    cursor = conn.cursor(RealDictCursor)
    try:
        cursor.execute("""
            SELECT * FROM sessions
            WHERE discord_id = %s AND token_hash = %s
            AND last_activity > NOW() - INTERVAL '30 days'
        """, (discord_id, token_hash))
        
        result = cursor.fetchone()
        return result is not None
    except Exception as e:
        logger.error(f"Error verifying session: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

# ==================== ROUTES ====================

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint for Railway"""
    try:
        conn = get_db_connection()
        if conn:
            conn.close()
            return jsonify({"status": "healthy", "timestamp": datetime.utcnow().isoformat()}), 200
        else:
            return jsonify({"status": "degraded", "message": "Database unavailable"}), 200
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({"status": "degraded", "message": str(e)}), 200

@app.route('/', methods=['GET'])
def index():
    """Main page"""
    if 'discord_id' not in session:
        return redirect(url_for('login'))
    try:
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Error rendering index: {e}")
        return jsonify({"error": f"Template error: {str(e)}"}), 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        try:
            data = request.get_json()
            token = data.get('token')
            
            if not token:
                return jsonify({"error": "Token required"}), 400
            
            # For demonstration, we'll use a hash of the token as ID
            token_hash = hash_token(token)
            discord_id = int(token.split('.')[-1][:10], 16) if '.' in token else hash(token) % 1000000
            
            # Store session
            if store_session(discord_id, token_hash):
                session['discord_id'] = discord_id
                session['token_hash'] = token_hash
                return jsonify({"status": "success", "redirect": url_for('index')}), 200
            else:
                return jsonify({"error": "Failed to create session"}), 500
                
        except Exception as e:
            logger.error(f"Login error: {e}")
            return jsonify({"error": f"Login failed: {str(e)}"}), 500
    
    try:
        return render_template('login.html')
    except Exception as e:
        logger.error(f"Error rendering login template: {e}")
        return f"<html><body><h1>Template Error</h1><p>{str(e)}</p></body></html>", 500

@app.route('/logout', methods=['POST'])
def logout():
    """Logout"""
    session.clear()
    return jsonify({"status": "success"}), 200

@app.route('/api/users', methods=['GET'])
def api_get_users():
    """Get all users"""
    if 'discord_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        users = get_all_users()
        return jsonify(users), 200
    except Exception as e:
        logger.error(f"Error getting users: {e}")
        return jsonify({"error": "Failed to get users"}), 500

@app.route('/api/users/search', methods=['GET'])
def api_search_users():
    """Search users"""
    if 'discord_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    query = request.args.get('q', '')
    if not query:
        return jsonify({"error": "Query required"}), 400
    
    try:
        results = search_users(query)
        return jsonify(results), 200
    except Exception as e:
        logger.error(f"Error searching users: {e}")
        return jsonify({"error": "Search failed"}), 500

@app.route('/api/users/<int:user_id>/messages', methods=['GET'])
def api_get_user_messages(user_id):
    """Get messages from a user"""
    if 'discord_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        channel_id = request.args.get('channel_id', type=int)
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        messages = get_user_messages(user_id, channel_id, limit, offset)
        return jsonify(messages), 200
    except Exception as e:
        logger.error(f"Error getting user messages: {e}")
        return jsonify({"error": "Failed to get messages"}), 500

@app.route('/api/messages/search', methods=['GET'])
def api_search_messages():
    """Search messages"""
    if 'discord_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    query = request.args.get('q', '')
    user_id = request.args.get('user_id', type=int)
    limit = request.args.get('limit', 100, type=int)
    
    if not query:
        return jsonify({"error": "Query required"}), 400
    
    try:
        results = search_messages(query, user_id, limit)
        return jsonify(results), 200
    except Exception as e:
        logger.error(f"Error searching messages: {e}")
        return jsonify({"error": "Search failed"}), 500

@app.route('/api/users/<int:user_id>/stats', methods=['GET'])
def api_get_user_stats(user_id):
    """Get user statistics"""
    if 'discord_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        stats = get_user_stats(user_id)
        return jsonify(stats), 200
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({"error": "Failed to get stats"}), 500

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    logger.warning(f"404 error: {e}")
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def internal_error(e):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {e}")
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8000))
    logger.info(f"Starting app on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
