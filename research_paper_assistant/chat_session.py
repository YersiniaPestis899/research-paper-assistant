from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class Message:
    role: str  # 'user' または 'assistant'
    content: str

class ChatSession:
    def __init__(self, paper: Dict):
        self.paper = paper
        self.messages: List[Message] = []

    def add_message(self, role: str, content: str):
        """新しいメッセージを会話に追加"""
        self.messages.append(Message(role=role, content=content))

    def get_context_for_prompt(self) -> str:
        """プロンプト用のコンテキストを生成"""
        context = f"""論文情報：
タイトル: {self.paper['title']}
著者: {self.paper['authors']}
要約: {self.paper['summary']}

これまでの会話:"""

        for msg in self.messages:
            context += f"\n{msg.role}: {msg.content}"

        return context

    def format_message_for_display(self, message: Message) -> str:
        """メッセージを表示用にフォーマット"""
        return message.content