import streamlit as st
import arxiv
import boto3
import os
from dotenv import load_dotenv
import json
import pandas as pd

# Load environment variables
load_dotenv()

# Set page config for Japanese support
st.set_page_config(page_title="研究論文アシスタント", layout="wide")

# Initialize AWS Bedrock client
bedrock = boto3.client(
    service_name='bedrock-runtime',
    region_name=os.getenv('AWS_DEFAULT_REGION'),
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
)

def search_papers(query, max_results=5):
    """Search papers on arXiv with improved handling of Japanese queries"""
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance
    )
    
    results = []
    for paper in search.results():
        # 日本語の著者名が含まれている場合の処理を改善
        authors = [author.name for author in paper.authors]
        
        results.append({
            'title': paper.title,
            'authors': ', '.join(authors),
            'summary': paper.summary,
            'pdf_url': paper.pdf_url,
            'published': paper.published.strftime('%Y-%m-%d'),
            'arxiv_id': paper.entry_id.split('abs/')[-1],
            'primary_category': paper.primary_category,
            'categories': paper.categories
        })
    
    return results

def analyze_paper(paper, language="日本語"):
    """Analyze paper using Claude with language selection"""
    if language == "日本語":
        prompt = f"""以下の研究論文を分析し、日本語で洞察を提供してください：

論文タイトル: {paper['title']}
著者: {paper['authors']}
要約: {paper['summary']}
分野: {paper['primary_category']}

以下の項目について分析してください：

1. 主要な研究成果と貢献
2. 研究手法の分析
3. 潜在的な応用と影響
4. 今後の研究への提案
5. 関連する研究分野

それぞれの項目について、できるだけ具体的に説明してください。
専門用語の説明も適宜加えてください。"""
    else:
        prompt = f"""Analyze the following research paper and provide insights:

Title: {paper['title']}
Authors: {paper['authors']}
Abstract: {paper['summary']}
Field: {paper['primary_category']}

Please provide:
1. Key findings and contributions
2. Research methodology analysis
3. Potential applications and implications
4. Suggestions for future research
5. Related research areas"""
    
    try:
        response = bedrock.invoke_model(
            modelId=os.getenv('AWS_CLAUDE_MODEL_ID'),
            body={
                'prompt': prompt,
                'max_tokens': 1000,
                'temperature': 0.7
            }
        )
        
        result = json.loads(response.get('body').read().decode('utf-8'))
        return result['completion']
    except Exception as e:
        st.error(f"分析中にエラーが発生しました: {str(e)}")
        return None

def main():
    st.title("研究論文アシスタント")
    st.write("arXivの論文を検索し、AIを使用して分析します")
    
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
                papers = search_papers(query, max_results)
                if papers:
                    st.session_state.papers = papers
                else:
                    st.warning("論文が見つかりませんでした")
    
    # Display results
    if 'papers' in st.session_state:
        for i, paper in enumerate(st.session_state.papers):
            with st.expander(f"{i+1}. {paper['title']}", expanded=True):
                st.write(f"**著者:** {paper['authors']}")
                st.write(f"**公開日:** {paper['published']}")
                st.write(f"**分野:** {paper['primary_category']}")
                st.write("**要約:**")
                st.write(paper['summary'])
                
                col1, col2 = st.columns(2)
                with col1:
                    st.link_button("PDFを表示", paper['pdf_url'])
                with col2:
                    if st.button("AI分析", key=f"analyze_{i}"):
                        with st.spinner("論文を分析中..."):
                            analysis = analyze_paper(paper, language)
                            if analysis:
                                st.markdown("## 分析結果")
                                st.markdown(analysis)

if __name__ == "__main__":
    main()