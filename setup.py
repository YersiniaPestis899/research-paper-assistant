from setuptools import setup, find_packages

setup(
    name="research_paper_assistant",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "streamlit>=1.24.0",
        "arxiv",
        "requests",
        "python-dotenv",
        "boto3",
        "markdown",
        "pandas",
        "python-dateutil"
    ],
)