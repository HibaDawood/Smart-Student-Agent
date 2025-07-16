import os
import chainlit as cl
import google.generativeai as genai
from dotenv import load_dotenv
from typing import Optional, Dict, List
import sqlite3
import json
from datetime import datetime
import uuid

load_dotenv()

gemini_api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=gemini_api_key)

model = genai.GenerativeModel(model_name="gemini-2.0-flash")

# Database setup
def init_database():
    """Initialize the SQLite database for storing chat sessions and messages"""
    conn = sqlite3.connect('chat_history.db')
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

def create_new_session(user_id: str, title: str = None) -> str:
    """Create a new chat session"""
    session_id = str(uuid.uuid4())
    if not title:
        title = f"New Chat"
    
    conn = sqlite3.connect('chat_history.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO sessions (id, user_id, title, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (session_id, user_id, title, datetime.now(), datetime.now()))
    
    conn.commit()
    conn.close()
    
    return session_id

def get_user_sessions(user_id: str) -> List[Dict]:
    """Get all sessions for a user"""
    conn = sqlite3.connect('chat_history.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, title, created_at, updated_at
        FROM sessions
        WHERE user_id = ?
        ORDER BY updated_at DESC
    ''', (user_id,))
    
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

def get_latest_session(user_id: str) -> Optional[str]:
    """Get the most recent session for a user"""
    conn = sqlite3.connect('chat_history.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id FROM sessions
        WHERE user_id = ?
        ORDER BY updated_at DESC
        LIMIT 1
    ''', (user_id,))
    
    result = cursor.fetchone()
    conn.close()
    
    return result[0] if result else None

def get_session_messages(session_id: str) -> List[Dict]:
    """Get all messages for a session"""
    conn = sqlite3.connect('chat_history.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT role, content, timestamp
        FROM messages
        WHERE session_id = ?
        ORDER BY timestamp ASC
    ''', (session_id,))
    
    messages = []
    for row in cursor.fetchall():
        messages.append({
            'role': row[0],
            'content': row[1],
            'timestamp': row[2]
        })
    
    conn.close()
    return messages

def save_message(session_id: str, role: str, content: str):
    """Save a message to the database"""
    conn = sqlite3.connect('chat_history.db')
    cursor = conn.cursor()
    
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
    conn.close()

def delete_session(session_id: str):
    """Delete a session and all its messages"""
    conn = sqlite3.connect('chat_history.db')
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM messages WHERE session_id = ?', (session_id,))
    cursor.execute('DELETE FROM sessions WHERE id = ?', (session_id,))
    
    conn.commit()
    conn.close()

def update_session_title(session_id: str, new_title: str):
    """Update session title based on first message"""
    conn = sqlite3.connect('chat_history.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE sessions
        SET title = ?, updated_at = ?
        WHERE id = ?
    ''', (new_title, datetime.now(), session_id))
    
    conn.commit()
    conn.close()

def generate_session_title(first_message: str) -> str:
    """Generate a title from the first message"""
    # Take first 40 characters and clean it up
    title = first_message[:40].strip()
    if len(first_message) > 40:
        title += "..."
    return title

# Initialize database on startup
init_database()

@cl.oauth_callback
def oauth_callback(
    provider_id: str,
    token: str,
    raw_user_data: Dict[str, str],
    default_user: cl.user,
) -> Optional[cl.user]:
    """Handle the OAuth callback from Github"""
    print(f"Provider: {provider_id}")
    print(f"User data: {raw_user_data}")
    return default_user

@cl.on_chat_start
async def handle_chat_start():
    """Handle chat start - load most recent session or create new one"""
    user = cl.user_session.get("user")
    user_id = user.identifier if user else "anonymous"
    
    # Try to load the most recent session
    latest_session_id = get_latest_session(user_id)
    
    if latest_session_id:
        # Load existing session
        session_id = latest_session_id
        cl.user_session.set("current_session_id", session_id)
        cl.user_session.set("user_id", user_id)
        
        # Load and display existing messages
        messages = get_session_messages(session_id)
        
        if messages:
            # Display all previous messages
            for msg in messages:
                if msg['role'] == 'user':
                    await cl.Message(
                        content=msg['content'],
                        author="You"
                    ).send()
                else:
                    await cl.Message(
                        content=msg['content'],
                        author="Assistant"
                    ).send()
            
            message_count = len([m for m in messages if m['role'] == 'user'])
            cl.user_session.set("message_count", message_count)
        else:
            # Session exists but no messages
            welcome_msg = "Hello! How can I help you today?"
            await cl.Message(content=welcome_msg).send()
            save_message(session_id, "assistant", welcome_msg)
            cl.user_session.set("message_count", 0)
    else:
        # No existing sessions, create new one
        session_id = create_new_session(user_id)
        cl.user_session.set("current_session_id", session_id)
        cl.user_session.set("user_id", user_id)
        cl.user_session.set("message_count", 0)
        
        # Send welcome message
        welcome_msg = "Hello! How can I help you today?"
        await cl.Message(content=welcome_msg).send()
        save_message(session_id, "assistant", welcome_msg)

@cl.on_message
async def handle_message(message: cl.Message):
    """Handle incoming messages"""
    user_input = message.content.strip()
    session_id = cl.user_session.get("current_session_id")
    user_id = cl.user_session.get("user_id", "anonymous")
    message_count = cl.user_session.get("message_count", 0)
    
    if not session_id:
        session_id = create_new_session(user_id)
        cl.user_session.set("current_session_id", session_id)
    
    # Save user message
    save_message(session_id, "user", user_input)
    
    # Update session title with first user message
    if message_count == 0:
        title = generate_session_title(user_input)
        update_session_title(session_id, title)
    
    cl.user_session.set("message_count", message_count + 1)
    
    # Get conversation history from database
    messages = get_session_messages(session_id)
    
    # Format history for Gemini
    formatted_history = []
    for msg in messages:
        role = "user" if msg["role"] == "user" else "model"
        formatted_history.append({
            "role": role, 
            "parts": [{"text": msg["content"]}]
        })
    
    try:
        # Generate response
        response = model.generate_content(formatted_history)
        response_text = response.text if hasattr(response, "text") else "Sorry, I couldn't generate a response."
        
        # Save assistant response
        save_message(session_id, "assistant", response_text)
        
        # Send response
        await cl.Message(content=response_text).send()
        
    except Exception as e:
        error_msg = f"Sorry, there was an error: {str(e)}"
        await cl.Message(content=error_msg).send()
        save_message(session_id, "assistant", error_msg)

if __name__ == "__main__":
    cl.run()
