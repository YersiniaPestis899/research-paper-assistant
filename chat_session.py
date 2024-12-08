from dataclasses import dataclass
from typing import List, Dict
from datetime import datetime

@dataclass
class Message:
    role: str
    content: str
    timestamp: datetime
    citations: List[Dict] = None

class ChatSession:
    def __init__(self, paper_info: Dict, max_history: int = 20):
        self.paper_info = paper_info
        self.max_history = max_history
        self.messages: List[Message] = []
        
    def add_message(self, role: str, content: str, citations: List[Dict] = None):
        """Add a new message to the chat history"""
        message = Message(
            role=role,
            content=content,
            timestamp=datetime.now(),
            citations=citations
        )
        self.messages.append(message)
        
        # Keep only the last max_history messages
        if len(self.messages) > self.max_history:
            self.messages = self.messages[-self.max_history:]
            
    def get_context_for_prompt(self) -> str:
        """Generate context for the AI prompt including paper info and chat history"""
        context = f"""論文情報:
タイトル: {self.paper_info['title']}
著者: {self.paper_info['authors']}
要約: {self.paper_info['summary']}

これまでの会話:
"""
        
        for msg in self.messages[-5:]:  # Include last 5 messages for immediate context
            prefix = "質問" if msg.role == "user" else "回答"
            context += f"\n{prefix}: {msg.content}\n"
            if msg.citations:
                context += "引用:\n"
                for cite in msg.citations:
                    context += f"- {cite['text']} ({cite['section']})\n"
                    
        return context
        
    def format_message_for_display(self, message: Message) -> str:
        """Format a message for display in the UI"""
        formatted = message.content
        if message.citations:
            formatted += "\n\n引用:\n"
            for cite in message.citations:
                formatted += f"- {cite['text']} ({cite['section']})\n"
        return formatted