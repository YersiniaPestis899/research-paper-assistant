import arxiv
import requests
from typing import List, Dict
from datetime import datetime
from dateutil import parser

class PaperSource:
    def search(self, query: str, max_results: int) -> List[Dict]:
        raise NotImplementedError

class ArxivSource(PaperSource):
    def search(self, query: str, max_results: int = 5) -> List[Dict]:
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
        
    def search(self, query: str, max_results: int = 5) -> List[Dict]:
        # bioRxiv APIは直接キーワード検索をサポートしていないため
        # 最新の論文を取得して、タイトルとアブストラクトでフィルタリング
        response = requests.get(f"{self.base_url}/2024-01-01/2024-12-31/0/200")
        if response.status_code != 200:
            return []
            
        data = response.json()
        if 'collection' not in data:
            return []
            
        # キーワードでフィルタリング
        query = query.lower()
        filtered_papers = []
        for paper in data['collection']:
            if (query in paper.get('title', '').lower() or 
                query in paper.get('abstract', '').lower()):
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