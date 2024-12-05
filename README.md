# Research Paper Assistant

This application helps researchers analyze and understand academic papers using arXiv API and AWS Bedrock Claude 3.5 Sonnet.

## Features

- Search for research papers on arXiv
- Generate paper summaries and key insights
- Analyze research methodology and findings
- Suggest related papers and research directions
- Extract key concepts and terminology

## Requirements

- Python 3.8+
- Flask
- Boto3 (AWS SDK)
- arxiv package
- python-dotenv

## Setup

1. Clone this repository:
```bash
git clone https://github.com/YersiniaPestis899/research-paper-assistant.git
cd research-paper-assistant
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a .env file and add your AWS credentials:
```bash
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=your_region
```

4. Run the application:
```bash
python app.py
```

The application will be available at `http://localhost:5000`

## Usage

1. Enter your research topic or paper title in the search box
2. Select papers you want to analyze
3. Get AI-powered insights and analysis

## License

MIT License