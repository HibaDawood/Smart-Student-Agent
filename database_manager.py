import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional

class ChatDatabase:
    def __init__(self, db_path: str = "chat_history.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                title TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create messages table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                role TEXT,
                content TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def backup_database(self, backup_path: str):
        """Create a backup of the database"""
        import shutil
        shutil.copy2(self.db_path, backup_path)
    
    def get_database_stats(self) -> Dict:
        """Get database statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM sessions')
        session_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM messages')
        message_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(DISTINCT user_id) FROM sessions')
        user_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'sessions': session_count,
            'messages': message_count,
            'users': user_count
        }
    
    def export_user_data(self, user_id: str) -> Dict:
        """Export all data for a specific user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get user sessions
        cursor.execute('''
            SELECT id, title, created_at, updated_at
            FROM sessions
            WHERE user_id = ?
            ORDER BY created_at DESC
        ''', (user_id,))
        
        sessions = []
        for row in cursor.fetchall():
            session_id = row[0]
            
            # Get messages for this session
            cursor.execute('''
                SELECT role, content, timestamp
                FROM messages
                WHERE session_id = ?
                ORDER BY timestamp ASC
            ''', (session_id,))
            
            messages = [
                {
                    'role': msg[0],
                    'content': msg[1],
                    'timestamp': msg[2]
                }
                for msg in cursor.fetchall()
            ]
            
            sessions.append({
                'id': session_id,
                'title': row[1],
                'created_at': row[2],
                'updated_at': row[3],
                'messages': messages
            })
        
        conn.close()
        
        return {
            'user_id': user_id,
            'export_date': datetime.now().isoformat(),
            'sessions': sessions
        }

# Usage example
if __name__ == "__main__":
    db = ChatDatabase()
    stats = db.get_database_stats()
    print(f"Database Stats: {stats}")
