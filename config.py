import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-2.0-flash"

# Database Configuration
DATABASE_PATH = "chat_history.db"

# Session Configuration
MAX_SESSIONS_PER_USER = 50
MAX_MESSAGES_PER_SESSION = 1000

# UI Configuration
WELCOME_MESSAGE = "Hello! How can I help you today?"
SESSION_ACTIONS_ENABLED = True

# Backup Configuration
AUTO_BACKUP = True
BACKUP_INTERVAL_HOURS = 24
