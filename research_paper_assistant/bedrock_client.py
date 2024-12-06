import boto3
import json
import time
from typing import Optional
import streamlit as st
import os

class BedrockClient:
    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0):
        self.client = boto3.client(
            service_name='bedrock-runtime',
            region_name=os.getenv('AWS_DEFAULT_REGION'),
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.last_request_time = 0
        self.min_request_interval = 0.5  # 最小リクエスト間隔（秒）

    def wait_if_needed(self):
        """リクエスト間隔を制御"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last_request)
        self.last_request_time = time.time()

    def invoke_model(self, prompt: str, max_tokens: int = 4096) -> Optional[str]:
        """Claudeモデルを呼び出し、必要に応じて再試行"""
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "top_k": 250,
            "stop_sequences": [],
            "temperature": 0.7,
            "top_p": 0.999,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
        }
        
        json_body = json.dumps(request_body).encode('utf-8')
        retries = 0
        
        while retries <= self.max_retries:
            try:
                self.wait_if_needed()
                response = self.client.invoke_model(
                    modelId=os.getenv('AWS_CLAUDE_MODEL_ID'),
                    contentType="application/json",
                    accept="application/json",
                    body=json_body
                )
                
                response_body = json.loads(response['body'].read())
                return response_body['content'][0]['text']
                
            except Exception as e:
                retries += 1
                if retries <= self.max_retries:
                    delay = self.retry_delay * (2 ** (retries - 1))  # 指数バックオフ
                    st.warning(f"リクエストが制限されました。{delay}秒後に再試行します... ({retries}/{self.max_retries})")
                    time.sleep(delay)
                else:
                    st.error(f"エラーが発生しました: {str(e)}")
                    return None
        
        return None