from datetime import datetime
from typing import List, Dict
import sqlite3

class MessageManager:
    def __init__(self, db_path: str = "chat_history.db"):
        self.db_path = db_path
    
    def save_message(self, session_id: str, role: str, content: str) -> bool:
        """Save a message to the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO messages (session_id, role, content, timestamp)
                VALUES (?, ?, ?, ?)
            ''', (session_id, role, content, datetime.now()))
            
            # Update session's updated_at timestamp
            cursor.execute('''
                UPDATE sessions
                SET updated_at = ?
                WHERE id = ?
            ''', (datetime.now(), session_id))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error saving message: {e}")
            return False
        finally:
            conn.close()
    
    def get_messages(self, session_id: str, limit: int = 1000) -> List[Dict]:
        """Get all messages for a session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT role, content, timestamp
            FROM messages
            WHERE session_id = ?
            ORDER BY timestamp ASC
            LIMIT ?
        ''', (session_id, limit))
        
        messages = []
        for row in cursor.fetchall():
            messages.append({
                'role': row[0],
                'content': row[1],
                'timestamp': row[2]
            })
        
        conn.close()
        return messages
    
    def delete_messages(self, session_id: str) -> bool:
        """Delete all messages for a session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('DELETE FROM messages WHERE session_id = ?', (session_id,))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error deleting messages: {e}")
            return False
        finally:
            conn.close()
    
    def get_message_count(self, session_id: str) -> int:
        """Get the number of messages in a session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM messages WHERE session_id = ?', (session_id,))
        count = cursor.fetchone()[0]
        
        conn.close()
        return count
    
    def search_messages(self, user_id: str, query: str, limit: int = 50) -> List[Dict]:
        """Search messages across all user sessions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT m.session_id, s.title, m.role, m.content, m.timestamp
            FROM messages m
            JOIN sessions s ON m.session_id = s.id
            WHERE s.user_id = ? AND m.content LIKE ?
            ORDER BY m.timestamp DESC
            LIMIT ?
        ''', (user_id, f'%{query}%', limit))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'session_id': row[0],
                'session_title': row[1],
                'role': row[2],
                'content': row[3],
                'timestamp': row[4]
            })
        
        conn.close()
        return results
