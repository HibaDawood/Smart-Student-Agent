import chainlit as cl
from typing import List, Dict
from datetime import datetime

class SidebarManager:
    """Manage sidebar with chat sessions"""
    
    @staticmethod
    async def create_sidebar(sessions: List[Dict], current_session_id: str):
        """Create sidebar with session list"""
        
        # Create sidebar content
        sidebar_html = """
        <div style="padding: 20px; background: #f8f9fa; border-radius: 10px; margin: 10px 0;">
            <h3 style="color: #333; margin-bottom: 15px;">💬 Chat Sessions</h3>
            
            <button onclick="newChat()" style="
                width: 100%; 
                padding: 10px; 
                background: #007acc; 
                color: white; 
                border: none; 
                border-radius: 5px; 
                cursor: pointer; 
                margin-bottom: 15px;
                font-size: 14px;
            ">
                🆕 New Chat
            </button>
            
            <div style="max-height: 400px; overflow-y: auto;">
        """
        
        if sessions:
            for i, session in enumerate(sessions[:15]):
                created_date = datetime.fromisoformat(session['created_at']).strftime('%m/%d')
                is_current = session['id'] == current_session_id
                
                bg_color = "#e3f2fd" if is_current else "#ffffff"
                border = "2px solid #007acc" if is_current else "1px solid #ddd"
                
                sidebar_html += f"""
                <div style="
                    background: {bg_color}; 
                    border: {border}; 
                    border-radius: 8px; 
                    padding: 10px; 
                    margin-bottom: 8px;
                    cursor: pointer;
                " onclick="loadChat('{session['id']}')">
                    <div style="font-weight: bold; color: #333; font-size: 13px;">
                        {session['title'][:30]}{'...' if len(session['title']) > 30 else ''}
                    </div>
                    <div style="color: #666; font-size: 11px; margin-top: 4px;">
                        📅 {created_date}
                        <span onclick="deleteChat('{session['id']}')" style="
                            float: right; 
                            color: #ff4444; 
                            cursor: pointer;
                            padding: 2px 6px;
                            border-radius: 3px;
                        " title="Delete chat">🗑️</span>
                    </div>
                </div>
                """
        else:
            sidebar_html += "<p style='color: #666; text-align: center;'>No chat history yet</p>"
        
        sidebar_html += """
            </div>
        </div>
        
        <script>
            function newChat() {
                // Send message to create new chat
                window.parent.postMessage({type: 'new_chat'}, '*');
            }
            
            function loadChat(sessionId) {
                // Send message to load chat
                window.parent.postMessage({type: 'load_chat', sessionId: sessionId}, '*');
            }
            
            function deleteChat(sessionId) {
                event.stopPropagation();
                if(confirm('Are you sure you want to delete this chat?')) {
                    window.parent.postMessage({type: 'delete_chat', sessionId: sessionId}, '*');
                }
            }
        </script>
        """
        
        return sidebar_html

    @staticmethod
    async def send_sidebar(content: str):
        """Send sidebar content to UI"""
        await cl.Message(
            content="",
            elements=[
                cl.Html(
                    name="sidebar",
                    content=content,
                    display="side"
                )
            ]
        ).send()
