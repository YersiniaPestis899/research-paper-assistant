# Research Paper Assistant

A Streamlit-based application that helps researchers analyze academic papers using arXiv API and AWS Bedrock Claude 3.5 Sonnet.

## Features

- Search for research papers on arXiv
- Generate paper summaries and key insights using AI
- Analyze research methodology and findings
- Get suggestions for related research areas
- View papers in PDF format

## Requirements

- Python 3.8+
- Streamlit
- arXiv package
- Boto3 (AWS SDK)
- python-dotenv

## Setup

1. Clone the repository
2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a .env file with your AWS credentials:
```bash
cp .env.example .env
```
Then edit .env with your actual AWS credentials.

5. Run the application:
```bash
streamlit run app.py
```

## Usage

1. Enter your research topic or keywords in the search box
2. Adjust the maximum number of papers to display
3. Click "Search" to find relevant papers
4. For each paper, you can:
   - View the PDF
   - Generate AI-powered analysis
   - Read the summary and details

## Note

This application requires valid AWS credentials with access to AWS Bedrock service. Make sure you have the necessary permissions set up in your AWS account.