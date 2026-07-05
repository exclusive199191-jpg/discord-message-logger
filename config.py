import os
from dotenv import load_dotenv

load_dotenv()

# Discord
DISCORD_USER_TOKEN = os.getenv('DISCORD_USER_TOKEN')
DISCORD_API_BASE = os.getenv('DISCORD_API_BASE', 'https://discord.com/api/v10')

# Database
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    DATABASE_URL = 'postgresql://localhost/discord_logger'

# Flask
FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-key-change-in-production')
FLASK_ENV = os.getenv('FLASK_ENV', 'production')

# Server
PORT = int(os.getenv('PORT', 8000))
HOST = os.getenv('HOST', '0.0.0.0')

# Logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# App Settings
MAX_MESSAGES_PER_QUERY = 100
SEARCH_RESULT_LIMIT = 50
SESSION_TIMEOUT_DAYS = 30
