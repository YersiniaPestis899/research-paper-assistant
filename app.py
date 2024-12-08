import streamlit as st
import os
from dotenv import load_dotenv
from research_paper_assistant.paper_sources import ArxivSource, BiorxivSource, PubmedSource
from research_paper_assistant.chat_session import ChatSession
from research_paper_assistant.bedrock_client import BedrockClient

# Load environment variables
load_dotenv()

# Set page config for Japanese support
st.set_page_config(page_title="研究論文アシスタント", layout="wide")

# Initialize Bedrock client with retry logic
bedrock = BedrockClient(max_retries=3, retry_delay=1.0)

def init_session_state():
    """Initialize session state variables"""
    if 'chat_sessions' not in st.session_state:
        st.session_state.chat_sessions = {}
    if 'papers' not in st.session_state:
        st.session_state.papers = []
    if 'summaries' not in st.session_state:
        st.session_state.summaries = {}
    if 'expanded_papers' not in st.session_state:
        st.session_state.expanded_papers = set()
    if 'paper_contents' not in st.session_state:
        st.session_state.paper_contents = {}

def get_paper_source(source_name: str):
    """Get paper source instance based on name"""
    sources = {
        'arXiv': ArxivSource(),
        'bioRxiv': BiorxivSource(),
        'PubMed': PubmedSource()
    }
    return sources.get(source_name)

def fetch_paper_content(paper):
    """Fetch and store paper content if not already cached"""
    paper_id = paper['id']
    if paper_id not in st.session_state.paper_contents:
        source_type = paper.get('source')
        paper_source = get_paper_source(source_type)
        
        if paper_source and hasattr(paper_source, 'get_full_text'):
            with st.spinner("論文本文を取得中..."):
                try:
                    content = paper_source.get_full_text(paper)
                    if content:
                        st.session_state.paper_contents[paper_id] = content
                        return content
                except Exception as e:
                    st.error(f"論文本文の取得に失敗しました: {str(e)}")
    return st.session_state.paper_contents.get(paper_id)

def ask_claude(prompt: str, chat_session: ChatSession = None):
    """Ask Claude with context and return response with citations"""
    if chat_session:
        context = chat_session.get_context_for_prompt()
        paper = chat_session.paper
        paper_content = st.session_state.paper_contents.get(paper['id'])
        
        if paper_content:
            full_prompt = f"{context}\n\n論文本文:\n{paper_content}\n\n新しい質問: {prompt}\n\n上記の質問に対して、論文の内容を引用しながら回答してください。可能な限り、本文から具体的な箇所を引用してください。"
        else:
            full_prompt = f"{context}\n\n新しい質問: {prompt}\n\n上記の質問に対して、論文の内容を引用しながら回答してください。"
    else:
        full_prompt = prompt

    return bedrock.invoke_model(full_prompt)

def get_japanese_summary(paper):
    """Get Japanese summary for a paper"""
    paper_id = paper['id']
    if paper_id not in st.session_state.summaries:
        # Get full text if available
        paper_content = fetch_paper_content(paper)
        
        if paper_content:
            prompt = f"""以下の論文の要約を日本語で提供してください。専門用語は適切に説明し、研究の意義が一般の読者にも伝わるようにしてください：

タイトル: {paper['title']}
著者: {paper['authors']}
原文要約: {paper['summary']}
分野: {paper['primary_category']}

論文本文:
{paper_content[:2000]}  # 最初の2000文字のみ使用

上記の内容を踏まえて、以下の点に焦点を当てて要約してください：
1. 研究の背景と目的
2. 主な手法と結果
3. 研究の意義と今後の展望"""
        else:
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
    """Render chat interface for a specific paper"""
    if paper_id not in st.session_state.chat_sessions:
        paper = next(p for p in st.session_state.papers if p['id'] == paper_id)
        st.session_state.chat_sessions[paper_id] = ChatSession(paper)
        # Fetch paper content when initializing chat session
        fetch_paper_content(paper)
    
    chat_session = st.session_state.chat_sessions[paper_id]
    
    # Display content status
    if paper_id in st.session_state.paper_contents:
        st.info("📄 論文本文を利用可能です。より詳細な回答が得られます。")
    
    # Display chat history
    for msg in chat_session.messages:
        with st.chat_message(msg.role):
            st.markdown(chat_session.format_message_for_display(msg))
    
    # Chat input with unique key
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
    
    # Source selection
    source = st.selectbox(
        "論文ソースを選択",
        ["arXiv", "bioRxiv", "PubMed"]
    )
    
    # Language selection
    language = st.selectbox(
        "言語を選択",
        ["日本語", "English"]
    )
    
    # Search section
    with st.form("search_form"):
        query = st.text_input("研究トピックまたはキーワードを入力してください")
        
        col1, col2 = st.columns(2)
        with col1:
            max_results = st.slider("表示する論文数", 1, 10, 5)
        with col2:
            sort_order = st.selectbox(
                "並び順",
                ["関連度順", "最新順"]
            )
            
        submitted = st.form_submit_button("検索")
        
        if submitted and query:
            with st.spinner("論文を検索中..."):
                paper_source = get_paper_source(source)
                if paper_source:
                    papers = paper_source.search(query, max_results)
                    if papers:
                        st.session_state.papers = papers
                        # Clear previous session data when new search is performed
                        st.session_state.summaries = {}
                        st.session_state.expanded_papers = set()
                        st.session_state.paper_contents = {}
                        st.session_state.chat_sessions = {}
                    else:
                        st.warning("論文が見つかりませんでした")
    
    # Display results in tabs
    if 'papers' in st.session_state and st.session_state.papers:
        tabs = st.tabs([f"論文 {i+1}: {paper['title'][:50]}..." for i, paper in enumerate(st.session_state.papers)])
        
        for i, (tab, paper) in enumerate(zip(tabs, st.session_state.papers)):
            with tab:
                st.markdown(f"## {paper['title']}")
                st.write(f"**著者:** {paper['authors']}")
                st.write(f"**公開日:** {paper['published']}")
                st.write(f"**分野:** {paper['primary_category']}")
                st.write(f"**ソース:** {paper['source']}")
                
                # Summary display
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
                
                # Chat interface for each paper
                st.markdown("### 論文について質問する")
                render_chat_interface(paper['id'], i)

if __name__ == "__main__":
    main()