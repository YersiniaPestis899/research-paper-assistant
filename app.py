import os
from flask import Flask, render_template, request, jsonify
import arxiv
import boto3
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Initialize AWS Bedrock client
bedrock = boto3.client(
    service_name='bedrock-runtime',
    region_name=os.getenv('AWS_DEFAULT_REGION')
)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    query = request.form.get('query')
    if not query:
        return jsonify({'error': 'No query provided'}), 400
    
    # Search arXiv
    search = arxiv.Search(
        query=query,
        max_results=5,
        sort_by=arxiv.SortCriterion.Relevance
    )
    
    results = []
    for paper in search.results():
        results.append({
            'title': paper.title,
            'authors': [author.name for author in paper.authors],
            'summary': paper.summary,
            'pdf_url': paper.pdf_url,
            'published': paper.published.strftime('%Y-%m-%d'),
            'arxiv_id': paper.entry_id.split('abs/')[-1]
        })
    
    return jsonify(results)

@app.route('/analyze', methods=['POST'])
def analyze_paper():
    paper_data = request.json
    
    # Prepare prompt for Claude
    prompt = f"""Analyze the following research paper and provide insights:
    Title: {paper_data['title']}
    Authors: {', '.join(paper_data['authors'])}
    Abstract: {paper_data['summary']}
    
    Please provide:
    1. Key findings and contributions
    2. Research methodology analysis
    3. Potential applications and implications
    4. Suggestions for future research
    5. Related research areas to explore"""
    
    # Call Claude through AWS Bedrock
    response = bedrock.invoke_model(
        modelId='anthropic.claude-3.sonnet-20240229-v1:0',
        body={
            'prompt': prompt,
            'max_tokens': 1000,
            'temperature': 0.7
        }
    )
    
    analysis = response['body']['completion']
    
    return jsonify({
        'analysis': analysis
    })

if __name__ == '__main__':
    app.run(debug=True)
