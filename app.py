import streamlit as st
import arxiv
import boto3
import os
from dotenv import load_dotenv
import json
import pandas as pd

# Load environment variables
load_dotenv()

# Initialize AWS Bedrock client
bedrock = boto3.client(
    service_name='bedrock-runtime',
    region_name=os.getenv('AWS_DEFAULT_REGION'),
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
)

def search_papers(query, max_results=5):
    """Search papers on arXiv"""
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance
    )
    
    results = []
    for paper in search.results():
        results.append({
            'title': paper.title,
            'authors': ', '.join([author.name for author in paper.authors]),
            'summary': paper.summary,
            'pdf_url': paper.pdf_url,
            'published': paper.published.strftime('%Y-%m-%d'),
            'arxiv_id': paper.entry_id.split('abs/')[-1]
        })
    
    return results

def analyze_paper(paper):
    """Analyze paper using Claude"""
    prompt = f"""Analyze the following research paper and provide insights:
    Title: {paper['title']}
    Authors: {paper['authors']}
    Abstract: {paper['summary']}
    
    Please provide:
    1. Key findings and contributions
    2. Research methodology analysis
    3. Potential applications and implications
    4. Suggestions for future research
    5. Related research areas to explore
    
    Format your response in clear sections with headers."""
    
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
        st.error(f"Error analyzing paper: {str(e)}")
        return None

def main():
    st.set_page_config(page_title="Research Paper Assistant", layout="wide")
    
    st.title("Research Paper Assistant")
    st.write("Search and analyze research papers from arXiv using AI")
    
    # Search section
    with st.form("search_form"):
        query = st.text_input("Enter your research topic or keywords")
        max_results = st.slider("Maximum number of papers", 1, 10, 5)
        submitted = st.form_submit_button("Search")
        
        if submitted and query:
            with st.spinner("Searching papers..."):
                papers = search_papers(query, max_results)
                if papers:
                    st.session_state.papers = papers
                else:
                    st.warning("No papers found")
    
    # Display results
    if 'papers' in st.session_state:
        for i, paper in enumerate(st.session_state.papers):
            with st.expander(f"{i+1}. {paper['title']}", expanded=True):
                st.write(f"**Authors:** {paper['authors']}")
                st.write(f"**Published:** {paper['published']}")
                st.write(f"**Summary:**")
                st.write(paper['summary'])
                
                col1, col2 = st.columns(2)
                with col1:
                    st.link_button("View PDF", paper['pdf_url'])
                with col2:
                    if st.button("Analyze", key=f"analyze_{i}"):
                        with st.spinner("Analyzing paper..."):
                            analysis = analyze_paper(paper)
                            if analysis:
                                st.markdown("## Analysis Results")
                                st.markdown(analysis)

if __name__ == "__main__":
    main()