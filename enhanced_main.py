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

# Database functions (same as before)
def init_database():
    """Initialize the SQLite database for storing chat sessions and messages"""
    conn = sqlite3.connect('chat_history.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            title TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
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
    conn = sqlite3.connect('chat_history.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO messages (session_id, role, content, timestamp)
        VALUES (?, ?, ?, ?)
    ''', (session_id, role, content, datetime.now()))
    
    cursor.execute('''
        UPDATE sessions
        SET updated_at = ?
        WHERE id = ?
    ''', (datetime.now(), session_id))
    
    conn.commit()
    conn.close()

def delete_session(session_id: str):
    conn = sqlite3.connect('chat_history.db')
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM messages WHERE session_id = ?', (session_id,))
    cursor.execute('DELETE FROM sessions WHERE id = ?', (session_id,))
    
    conn.commit()
    conn.close()

def update_session_title(session_id: str, new_title: str):
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
    title = first_message[:40].strip()
    if len(first_message) > 40:
        title += "..."
    return title

# Initialize database
init_database()

@cl.on_chat_start
async def handle_chat_start():
    """Handle chat start with clean interface"""
    user = cl.user_session.get("user")
    user_id = user.identifier if user else "anonymous"
    
    # Load most recent session
    latest_session_id = get_latest_session(user_id)
    
    if latest_session_id:
        session_id = latest_session_id
        cl.user_session.set("current_session_id", session_id)
        cl.user_session.set("user_id", user_id)
        
        messages = get_session_messages(session_id)
        
        if messages:
            # Restore chat history
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
            welcome_msg = "Hello! How can I help you today?"
            await cl.Message(content=welcome_msg).send()
            save_message(session_id, "assistant", welcome_msg)
            cl.user_session.set("message_count", 0)
    else:
        # Create new session
        session_id = create_new_session(user_id)
        cl.user_session.set("current_session_id", session_id)
        cl.user_session.set("user_id", user_id)
        cl.user_session.set("message_count", 0)
        
        welcome_msg = "Hello! How can I help you today?"
        await cl.Message(content=welcome_msg).send()
        save_message(session_id, "assistant", welcome_msg)
    
    # Show simple session info
    await show_session_info()

async def show_session_info():
    """Show session information in a clean way"""
    user_id = cl.user_session.get("user_id", "anonymous")
    sessions = get_user_sessions(user_id)
    current_session_id = cl.user_session.get("current_session_id")
    
    # Find current session title
    current_title = "New Chat"
    for session in sessions:
        if session['id'] == current_session_id:
            current_title = session['title']
            break
    
    info_text = f"💬 **Current Chat:** {current_title}\n"
    info_text += f"📊 **Total Chats:** {len(sessions)}\n\n"
    
    if len(sessions) > 1:
        info_text += "**Recent Chats:**\n"
        for i, session in enumerate(sessions[:5], 1):
            if session['id'] != current_session_id:
                created_date = datetime.fromisoformat(session['created_at']).strftime('%m/%d')
                info_text += f"{i}. {session['title']} _{created_date}_\n"
    
    info_text += "\n💡 **Tip:** Your chat history is automatically saved!"
    
    await cl.Message(content=info_text).send()

@cl.on_message
async def handle_message(message: cl.Message):
    """Handle messages with clean interface"""
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
    
    # Get conversation history
    messages = get_session_messages(session_id)
    
    # Format for Gemini
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
        
        # Save and send response
        save_message(session_id, "assistant", response_text)
        await cl.Message(content=response_text).send()
        
    except Exception as e:
        error_msg = f"Sorry, there was an error: {str(e)}"
        await cl.Message(content=error_msg).send()
        save_message(session_id, "assistant", error_msg)

if __name__ == "__main__":
    cl.run()
