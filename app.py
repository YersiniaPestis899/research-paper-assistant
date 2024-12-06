import streamlit as st
import os
from dotenv import load_dotenv
from research_paper_assistant.paper_sources import ArxivSource, BiorxivSource, PubmedSource
from research_paper_assistant.chat_session import ChatSession
from research_paper_assistant.bedrock_client import BedrockClient

load_dotenv()
st.set_page_config(page_title="研究論文アシスタント", layout="wide")
bedrock = BedrockClient(max_retries=3, retry_delay=1.0)

def init_session_state():
    if 'chat_sessions' not in st.session_state:
        st.session_state.chat_sessions = {}
    if 'papers' not in st.session_state:
        st.session_state.papers = []
    if 'summaries' not in st.session_state:
        st.session_state.summaries = {}
    if 'expanded_papers' not in st.session_state:
        st.session_state.expanded_papers = set()

def get_paper_source(source_name: str):
    sources = {
        'arXiv': ArxivSource(),
        'bioRxiv': BiorxivSource(),
        'PubMed': PubmedSource()
    }
    return sources.get(source_name)

def ask_claude(prompt: str, chat_session: ChatSession = None):
    if chat_session:
        context = chat_session.get_context_for_prompt()
        full_prompt = f"{context}\n\n新しい質問: {prompt}\n\n上記の質問に対して、論文の内容を引用しながら回答してください。"
    else:
        full_prompt = prompt
    return bedrock.invoke_model(full_prompt)

def get_japanese_summary(paper):
    paper_id = paper['id']
    if paper_id not in st.session_state.summaries:
        prompt = f"""以下の論文の要約を日本語で提供してください。専門用語は適切に説明し、研究の意義が一般の読者にも伝わるようにしてください：

タイトル: {paper['title']}
著者: {paper['authors']}
原文要約: {paper['summary']}
分野: {paper['primary_category']}"""
        
        with st.spinner("要約を翻訳・解説中..."):
            summary = ask_claude(prompt)
            if summary:
                st.session_state.summaries[paper_id] = summary
                return summary
            return paper['summary']
    return st.session_state.summaries[paper_id]

def render_chat_interface(paper_id: str, index: int):
    if paper_id not in st.session_state.chat_sessions:
        paper = next(p for p in st.session_state.papers if p['id'] == paper_id)
        st.session_state.chat_sessions[paper_id] = ChatSession(paper)
    
    chat_session = st.session_state.chat_sessions[paper_id]
    
    for msg in chat_session.messages:
        with st.chat_message(msg.role):
            st.markdown(chat_session.format_message_for_display(msg))
    
    if prompt := st.chat_input("論文について質問してください", key=f"chat_input_{paper_id}_{index}"):
        with st.chat_message("user"):
            st.markdown(prompt)
        chat_session.add_message("user", prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("回答を生成中..."):
                response = ask_claude(prompt, chat_session)
                if response:
                    st.markdown(response)
                    chat_session.add_message("assistant", response)

def main():
    init_session_state()
    
    st.title("研究論文アシスタント")
    st.write("arXiv、bioRxiv、PubMedの論文を検索し、AIを使用して分析・質問ができます")
    
    source = st.selectbox("論文ソースを選択", ["arXiv", "bioRxiv", "PubMed"])
    language = st.selectbox("言語を選択", ["日本語", "English"])
    
    with st.form("search_form"):
        query = st.text_input("研究トピックまたはキーワードを入力してください")
        
        col1, col2 = st.columns(2)
        with col1:
            max_results = st.slider("表示する論文数", 1, 10, 5)
        with col2:
            sort_order = st.selectbox("並び順", ["関連度順", "最新順"])
            
        submitted = st.form_submit_button("検索")
        
        if submitted and query:
            with st.spinner("論文を検索中..."):
                paper_source = get_paper_source(source)
                if paper_source:
                    papers = paper_source.search(query, max_results)
                    if papers:
                        st.session_state.papers = papers
                        st.session_state.summaries = {}
                        st.session_state.expanded_papers = set()
                    else:
                        st.warning("論文が見つかりませんでした")
    
    if 'papers' in st.session_state and st.session_state.papers:
        tabs = st.tabs([f"論文 {i+1}: {paper['title'][:50]}..." for i, paper in enumerate(st.session_state.papers)])
        
        for i, (tab, paper) in enumerate(zip(tabs, st.session_state.papers)):
            with tab:
                st.markdown(f"## {paper['title']}")
                st.write(f"**著者:** {paper['authors']}")
                st.write(f"**公開日:** {paper['published']}")
                st.write(f"**分野:** {paper['primary_category']}")
                st.write(f"**ソース:** {paper['source']}")
                
                if st.button("要約を表示/非表示", key=f"summary_button_{paper['id']}"):
                    if paper['id'] in st.session_state.expanded_papers:
                        st.session_state.expanded_papers.remove(paper['id'])
                    else:
                        st.session_state.expanded_papers.add(paper['id'])
                
                if paper['id'] in st.session_state.expanded_papers:
                    with st.container():
                        if language == "日本語":
                            st.write(get_japanese_summary(paper))
                        else:
                            st.write(paper['summary'])
                
                col1, col2 = st.columns(2)
                with col1:
                    st.link_button("PDFを表示", paper['pdf_url'])
                
                st.markdown("### 論文について質問する")
                render_chat_interface(paper['id'], i)

if __name__ == "__main__":
    main()