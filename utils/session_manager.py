import uuid
from datetime import datetime
from typing import List, Dict, Optional
import sqlite3

class SessionManager:
    def __init__(self, db_path: str = "chat_history.db"):
        self.db_path = db_path
    
    def create_session(self, user_id: str, title: str = None) -> str:
        """Create a new chat session"""
        session_id = str(uuid.uuid4())
        if not title:
            title = f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO sessions (id, user_id, title, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (session_id, user_id, title, datetime.now(), datetime.now()))
        
        conn.commit()
        conn.close()
        
        return session_id
    
    def get_sessions(self, user_id: str, limit: int = 50) -> List[Dict]:
        """Get all sessions for a user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, title, created_at, updated_at
            FROM sessions
            WHERE user_id = ?
            ORDER BY updated_at DESC
            LIMIT ?
        ''', (user_id, limit))
        
        sessions = []
        for row in cursor.fetchall():
            sessions.append({
                'id': row[0],
                'title': row[1],
                'created_at': row[2],
                'updated_at': row[3]
            })
        
        conn.close()
        return sessions
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session and all its messages"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('DELETE FROM messages WHERE session_id = ?', (session_id,))
            cursor.execute('DELETE FROM sessions WHERE id = ?', (session_id,))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error deleting session: {e}")
            return False
        finally:
            conn.close()
    
    def update_session_title(self, session_id: str, new_title: str) -> bool:
        """Update session title"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE sessions
                SET title = ?, updated_at = ?
                WHERE id = ?
            ''', (new_title, datetime.now(), session_id))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error updating session title: {e}")
            return False
        finally:
            conn.close()
    
    def get_session_info(self, session_id: str) -> Optional[Dict]:
        """Get session information"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, user_id, title, created_at, updated_at
            FROM sessions
            WHERE id = ?
        ''', (session_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'user_id': row[1],
                'title': row[2],
                'created_at': row[3],
                'updated_at': row[4]
            }
        return None
