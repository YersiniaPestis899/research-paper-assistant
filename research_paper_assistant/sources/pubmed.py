import requests
import urllib.parse
import time
from ..base import PaperSource

class PubmedSource(PaperSource):
    def __init__(self):
        self.email = "your.email@example.com"  # メールアドレスを設定
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
        
    def search(self, query: str, max_results: int = 5) -> List[Dict]:
        try:
            # 検索クエリをエスケープ
            encoded_query = urllib.parse.quote(query)
            
            # 検索URL
            url = f"{self.base_url}/esearch.fcgi?db=pubmed&term={encoded_query}&retmax={max_results}&retmode=json"
            
            response = requests.get(url)
            search_data = response.json()
            
            if 'esearchresult' not in search_data or 'idlist' not in search_data['esearchresult']:
                return []
                
            results = []
            for pmid in search_data['esearchresult']['idlist']:
                # 論文の詳細を取得
                time.sleep(0.1)  # API制限を考慮
                details_url = f"{self.base_url}/esummary.fcgi?db=pubmed&id={pmid}&retmode=json"
                details = requests.get(details_url).json()
                
                if 'result' not in details:
                    continue
                    
                paper = details['result'][pmid]
                title = paper.get('title', 'No title').strip('.')
                authors = ', '.join(a.get('name', '') for a in paper.get('authors', []) if 'name' in a)
                abstract = paper.get('abstract', 'No abstract available')
                
                results.append({
                    'title': title,
                    'authors': authors,
                    'summary': abstract,
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