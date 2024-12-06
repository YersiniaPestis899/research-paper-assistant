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
        """
        words = query.lower().split()
        processed_words = []
        
        for word in words:
            if self.number_converter.contains_number(word):
                variants = self.number_converter.get_all_number_variants(word)
                processed_words.append(f"({' OR '.join(variants)})")
            else:
                word = re.escape(word)
                processed_words.append(f"(*{word}* OR *{word.capitalize()}*)")
        
        return " AND ".join(processed_words)

    def search(self, query: str, max_results: int = 5) -> List[Dict]:
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
        try:
            # 検索URL
            search_url = f"{self.base_url}/esearch.fcgi"
            search_params = {
                "db": "pubmed",
                "term": query,
                "retmax": max_results,
                "retmode": "json"
            }
            
            search_response = requests.get(search_url, params=search_params)
            if not search_response.ok:
                return []
                
            search_data = search_response.json()
            if 'esearchresult' not in search_data or 'idlist' not in search_data['esearchresult']:
                return []
                
            results = []
            for pmid in search_data['esearchresult']['idlist']:
                # 論文の詳細情報を取得
                summary_url = f"{self.base_url}/esummary.fcgi"
                summary_params = {
                    "db": "pubmed",
                    "id": pmid,
                    "retmode": "json"
                }
                
                summary_response = requests.get(summary_url, params=summary_params)
                if not summary_response.ok:
                    continue
                    
                details = summary_response.json()
                if 'result' not in details or pmid not in details['result']:
                    continue
                    
                paper = details['result'][pmid]
                
                # 著者リストの整形
                authors = []
                for author in paper.get('authors', []):
                    name = author.get('name', '')
                    if name:
                        authors.append(name)
                
                results.append({
                    'title': paper.get('title', 'No title').strip(),
                    'authors': ', '.join(authors),
                    'summary': paper.get('abstract', 'No abstract available'),
                    'pdf_url': f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                    'published': paper.get('pubdate', 'Unknown date'),
                    'id': pmid,
                    'source': 'PubMed',
                    'primary_category': 'Medicine',
                    'categories': ['Medicine'],
                    'raw_data': paper
                })
            
            return results
            
        except Exception as e:
            print(f"PubMed search error: {e}")
            return []