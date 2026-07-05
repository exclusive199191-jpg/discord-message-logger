import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel(logging.INFO)

def get_db_connection():
    """Get database connection"""
    try:
        db_url = os.getenv('DATABASE_URL')
        if not db_url:
            logger.warning("DATABASE_URL not set, using local fallback")
            # Fallback for local development
            db_url = 'postgresql://discord_logger:discord_password@localhost:5432/discord_logger'
        
        logger.info(f"Connecting to database...")
        conn = psycopg2.connect(db_url, connect_timeout=5)
        logger.info("Database connection successful")
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return None

def init_db():
    """Initialize database with tables"""
    logger.info("Initializing database...")
    conn = get_db_connection()
    if not conn:
        logger.error("Failed to connect to database for initialization")
        return
    
    cursor = conn.cursor()
    
    try:
        # Create messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                username VARCHAR(255) NOT NULL,
                display_name VARCHAR(255),
                content TEXT NOT NULL,
                channel_id BIGINT NOT NULL,
                channel_name VARCHAR(255),
                server_id BIGINT,
                server_name VARCHAR(255),
                is_dm BOOLEAN DEFAULT FALSE,
                timestamp TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                discord_id BIGINT UNIQUE NOT NULL,
                username VARCHAR(255) NOT NULL,
                display_name VARCHAR(255),
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id SERIAL PRIMARY KEY,
                discord_id BIGINT UNIQUE NOT NULL,
                token_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_id ON messages(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_channel_id ON messages(channel_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_server_id ON messages(server_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON messages(timestamp)")
        
        conn.commit()
        logger.info("Database initialized successfully")
        
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def get_all_users():
    """Get all users with message counts"""
    conn = get_db_connection()
    if not conn:
        return []
    
    cursor = conn.cursor(RealDictCursor)
    
    try:
        cursor.execute("""
            SELECT u.id, u.discord_id, u.username, u.display_name, COUNT(m.id) as message_count
            FROM users u
            LEFT JOIN messages m ON u.discord_id = m.user_id
            GROUP BY u.id, u.discord_id, u.username, u.display_name
            ORDER BY message_count DESC
            LIMIT 100
        """)
        
        results = cursor.fetchall()
        return [dict(row) for row in results]
        
    except Exception as e:
        logger.error(f"Error getting users: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def get_user_messages(discord_id, channel_id=None, limit=100, offset=0):
    """Get messages from a specific user"""
    conn = get_db_connection()
    if not conn:
        return []
    
    cursor = conn.cursor(RealDictCursor)
    
    try:
        if channel_id:
            cursor.execute("""
                SELECT * FROM messages
                WHERE user_id = %s AND channel_id = %s
                ORDER BY timestamp DESC
                LIMIT %s OFFSET %s
            """, (discord_id, channel_id, limit, offset))
        else:
            cursor.execute("""
                SELECT * FROM messages
                WHERE user_id = %s
                ORDER BY timestamp DESC
                LIMIT %s OFFSET %s
            """, (discord_id, limit, offset))
        
        results = cursor.fetchall()
        return [dict(row) for row in results]
        
    except Exception as e:
        logger.error(f"Error getting user messages: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def search_messages(query, user_id=None, limit=100):
    """Search messages by keyword"""
    conn = get_db_connection()
    if not conn:
        return []
    
    cursor = conn.cursor(RealDictCursor)
    
    try:
        if user_id:
            cursor.execute("""
                SELECT * FROM messages
                WHERE user_id = %s AND content ILIKE %s
                ORDER BY timestamp DESC
                LIMIT %s
            """, (user_id, f"%{query}%", limit))
        else:
            cursor.execute("""
                SELECT * FROM messages
                WHERE content ILIKE %s
                ORDER BY timestamp DESC
                LIMIT %s
            """, (f"%{query}%", limit))
        
        results = cursor.fetchall()
        return [dict(row) for row in results]
        
    except Exception as e:
        logger.error(f"Error searching messages: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def search_users(query):
    """Search users by username or display name"""
    conn = get_db_connection()
    if not conn:
        return []
    
    cursor = conn.cursor(RealDictCursor)
    
    try:
        cursor.execute("""
            SELECT u.id, u.discord_id, u.username, u.display_name, COUNT(m.id) as message_count
            FROM users u
            LEFT JOIN messages m ON u.discord_id = m.user_id
            WHERE u.username ILIKE %s OR u.display_name ILIKE %s OR u.discord_id::TEXT ILIKE %s
            GROUP BY u.id, u.discord_id, u.username, u.display_name
            LIMIT 50
        """, (f"%{query}%", f"%{query}%", f"%{query}%"))
        
        results = cursor.fetchall()
        return [dict(row) for row in results]
        
    except Exception as e:
        logger.error(f"Error searching users: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def get_user_stats(discord_id):
    """Get statistics for a user"""
    conn = get_db_connection()
    if not conn:
        return {}
    
    cursor = conn.cursor(RealDictCursor)
    
    try:
        cursor.execute("""
            SELECT 
                COUNT(*) as total_messages,
                COUNT(DISTINCT channel_id) as channels,
                COUNT(DISTINCT server_id) as servers,
                MIN(timestamp) as first_message,
                MAX(timestamp) as last_message
            FROM messages
            WHERE user_id = %s
        """, (discord_id,))
        
        result = cursor.fetchone()
        return dict(result) if result else {}
        
    except Exception as e:
        logger.error(f"Error getting user stats: {e}")
        return {}
    finally:
        cursor.close()
        conn.close()
