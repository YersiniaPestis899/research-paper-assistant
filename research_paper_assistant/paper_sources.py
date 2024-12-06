import arxiv
import requests
from typing import List, Dict
from datetime import datetime
from dateutil import parser
from .number_converter import NumberConverter
import re

class PaperSource:
    def search(self, query: str, max_results: int) -> List[Dict]:
        raise NotImplementedError

class ArxivSource(PaperSource):
    def __init__(self):
        self.number_converter = NumberConverter()

    def prepare_query(self, query: str) -> str:
        """
        Prepare query for case-insensitive search in arXiv
        - Convert to lowercase
        - Handle number variants
        - Add wildcards for case-insensitive search
        """
        # Split query into words
        words = query.lower().split()
        processed_words = []
        
        for word in words:
            if self.number_converter.contains_number(word):
                # For numbers, add all variants with OR
                variants = self.number_converter.get_all_number_variants(word)
                processed_words.append(f"({' OR '.join(variants)})")
            else:
                # Add both lowercase and capitalized versions
                # Use regex to properly handle special characters in arXiv search
                word = re.escape(word)
                processed_words.append(f"(*{word}* OR *{word.capitalize()}*)")
        
        return " AND ".join(processed_words)

    def search(self, query: str, max_results: int = 5) -> List[Dict]:
        # Prepare case-insensitive query
        processed_query = self.prepare_query(query)
        
        search = arxiv.Search(
            query=processed_query,
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
                'id': paper.entry_id.split('abs/')[-1],
                'source': 'arXiv',
                'primary_category': paper.primary_category,
                'categories': paper.categories,
                'raw_data': paper
            })
        
        return results

class BiorxivSource(PaperSource):
    def __init__(self):
        self.base_url = "https://api.biorxiv.org/details/biorxiv"
        self.number_converter = NumberConverter()
        
    def search(self, query: str, max_results: int = 5) -> List[Dict]:
        response = requests.get(f"{self.base_url}/2024-01-01/2024-12-31/0/200")
        if response.status_code != 200:
            return []
            
        data = response.json()
        if 'collection' not in data:
            return []
        
        def matches_query(text: str, q: str) -> bool:
            if self.number_converter.contains_number(q):
                return self.number_converter.is_number_match(text, q)
            else:
                return q.lower() in text.lower()
        
        filtered_papers = []
        for paper in data['collection']:
            title = paper.get('title', '')
            abstract = paper.get('abstract', '')
            
            if matches_query(title, query) or matches_query(abstract, query):
                filtered_papers.append(paper)
                if len(filtered_papers) >= max_results:
                    break
        
        formatted_results = []
        for paper in filtered_papers:
            try:
                pub_date = parser.parse(paper['date']).strftime('%Y-%m-%d')
            except:
                pub_date = paper.get('date', 'Unknown date')
                
            formatted_results.append({
                'title': paper.get('title', 'No title'),
                'authors': paper.get('authors', 'No authors'),
                'summary': paper.get('abstract', 'No abstract available'),
                'pdf_url': f"https://www.biorxiv.org/content/{paper.get('doi')}v1.full.pdf",
                'published': pub_date,
                'id': paper.get('doi', ''),
                'source': 'bioRxiv',
                'primary_category': paper.get('category', 'Biology'),
                'categories': [paper.get('category', 'Biology')],
                'raw_data': paper
            })
        
        return formatted_results

class PubmedSource(PaperSource):
    def __init__(self):
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
        self.number_converter = NumberConverter()
        
    def search(self, query: str, max_results: int = 5) -> List[Dict]:
        search_url = f"{self.base_url}/esearch.fcgi"
        search_params = {
            "db": "pubmed",
            "term": query,
            "retmax": max_results,
            "sort": "relevance",
            "retmode": "json"
        }
        
        try:
            search_response = requests.get(search_url, params=search_params)
            search_data = search_response.json()
            
            if "esearchresult" not in search_data or "idlist" not in search_data["esearchresult"]:
                return []
            
            paper_ids = search_data["esearchresult"]["idlist"]
            
            summary_url = f"{self.base_url}/esummary.fcgi"
            summary_params = {
                "db": "pubmed",
                "id": ",".join(paper_ids),
                "retmode": "json"
            }
            
            summary_response = requests.get(summary_url, params=summary_params)
            summary_data = summary_response.json()
            
            results = []
            for paper_id in paper_ids:
                paper = summary_data["result"][paper_id]
                
                # Get authors
                authors_list = []
                if "authors" in paper:
                    for author in paper["authors"]:
                        if "name" in author:
                            authors_list.append(author["name"])
                
                # Get title (removing trailing period if exists)
                title = paper.get("title", "No title").rstrip('.')
                
                # Get abstract
                abstract = ""
                if "abstract" in paper:
                    abstract = paper["abstract"]
                
                results.append({
                    'title': title,
                    'authors': ", ".join(authors_list) if authors_list else "No authors available",
                    'summary': abstract,
                    'pdf_url': f"https://pubmed.ncbi.nlm.nih.gov/{paper_id}/",
                    'published': paper.get("pubdate", "Unknown date"),
                    'id': paper_id,
                    'source': 'PubMed',
                    'primary_category': "Medicine",
                    'categories': ["Medicine"],
                    'raw_data': paper
                })
            
            return results
            
        except Exception as e:
            print(f"Error searching PubMed: {e}")
            return []