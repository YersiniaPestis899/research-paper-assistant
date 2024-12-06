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
        # bioRxiv APIは直接キーワード検索をサポートしていないため
        # 最新の論文を取得して、タイトルとアブストラクトでフィルタリング
        response = requests.get(f"{self.base_url}/2024-01-01/2024-12-31/0/200")
        if response.status_code != 200:
            return []
            
        data = response.json()
        if 'collection' not in data:
            return []
        
        # フィルタリング関数の定義
        def matches_query(text: str, q: str) -> bool:
            if self.number_converter.contains_number(q):
                return self.number_converter.is_number_match(text, q)
            else:
                return q.lower() in text.lower()
        
        # キーワードでフィルタリング
        filtered_papers = []
        for paper in data['collection']:
            title = paper.get('title', '')
            abstract = paper.get('abstract', '')
            
            if matches_query(title, query) or matches_query(abstract, query):
                filtered_papers.append(paper)
                if len(filtered_papers) >= max_results:
                    break
        
        # 結果を整形
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