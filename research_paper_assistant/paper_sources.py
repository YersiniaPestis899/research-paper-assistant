import arxiv
import requests
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from dateutil import parser
from .number_converter import NumberConverter
import re
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
import time
import json
import os
from pathlib import Path

class PaperSource:
    def search(self, query: str, max_results: int) -> List[Dict]:
        raise NotImplementedError
        
    def get_full_text(self, paper: Dict) -> Optional[str]:
        raise NotImplementedError

    def _get_cache_dir(self) -> Path:
        """Get or create cache directory"""
        cache_dir = Path.home() / '.paper_assistant_cache'
        cache_dir.mkdir(exist_ok=True)
        return cache_dir

    def _get_cached_content(self, key: str) -> Optional[str]:
        """Get content from cache if available"""
        cache_file = self._get_cache_dir() / f"{key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 24時間以内のキャッシュのみ使用
                    if time.time() - data['timestamp'] < 86400:
                        return data['content']
            except Exception:
                pass
        return None

    def _cache_content(self, key: str, content: str):
        """Cache content with timestamp"""
        cache_file = self._get_cache_dir() / f"{key}.json"
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'content': content,
                    'timestamp': time.time()
                }, f, ensure_ascii=False)
        except Exception as e:
            print(f"Cache write error: {e}")

    def _extract_text_from_xml(self, soup: BeautifulSoup) -> str:
        """XMLから本文を抽出する共通メソッド"""
        sections = []
        
        # タイトルを追加
        title = soup.find('article-title')
        if title:
            sections.append(f"Title: {title.text}")
        
        # アブストラクトを追加
        abstract = soup.find('abstract')
        if abstract:
            sections.append("\nAbstract:")
            sections.append(abstract.get_text(strip=True))
        
        # 本文セクションを取得
        body = soup.find('body')
        if body:
            sections.extend(self._process_section(body))
        
        return '\n\n'.join(filter(None, sections))

    def _process_section(self, element: BeautifulSoup) -> List[str]:
        """XMLセクションを再帰的に処理"""
        sections = []
        
        # セクションタイトルの処理
        title = element.find('title', recursive=False)
        if title:
            sections.append(f"\nSection: {title.text.strip()}")
        
        # 段落の処理
        for p in element.find_all('p', recursive=False):
            text = p.get_text(separator=' ', strip=True)
            if text:
                sections.append(text)
        
        # サブセクションの再帰的処理
        for subsec in element.find_all('sec', recursive=False):
            sections.extend(self._process_section(subsec))
        
        return sections

class ArxivSource(PaperSource):
    def __init__(self):
        self.number_converter = NumberConverter()

    def prepare_query(self, query: str) -> str:
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

    def get_full_text(self, paper: Dict) -> Optional[str]:
        return None  # arXivは本文取得を実装しない

class BiorxivSource(PaperSource):
    def __init__(self):
        self.base_url = "https://api.biorxiv.org/details/biorxiv"
        self.number_converter = NumberConverter()
        self.last_request_time = 0
        self.min_request_interval = 1.0  # 1秒間隔でリクエスト

    def _wait_for_rate_limit(self):
        """レート制限のための待機"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last_request)
        self.last_request_time = time.time()

    def search(self, query: str, max_results: int = 5) -> List[Dict]:
        self._wait_for_rate_limit()
        response = requests.get(f"{self.base_url}/2024-01-01/2024-12-31/0/200")
        if response.status_code != 200 or 'collection' not in response.json():
            return []

        def matches_query(text: str, q: str) -> bool:
            if self.number_converter.contains_number(q):
                return self.number_converter.is_number_match(text, q)
            return q.lower() in text.lower()

        filtered_papers = []
        for paper in response.json()['collection']:
            if matches_query(paper.get('title', ''), query) or matches_query(paper.get('abstract', ''), query):
                filtered_papers.append(paper)
                if len(filtered_papers) >= max_results:
                    break

        return [{
            'title': paper.get('title', 'No title'),
            'authors': paper.get('authors', 'No authors'),
            'summary': paper.get('abstract', 'No abstract available'),
            'pdf_url': f"https://www.biorxiv.org/content/{paper.get('doi')}v1.full.pdf",
            'published': parser.parse(paper['date']).strftime('%Y-%m-%d') if paper.get('date') else 'Unknown date',
            'id': paper.get('doi', ''),
            'source': 'bioRxiv',
            'primary_category': paper.get('category', 'Biology'),
            'categories': [paper.get('category', 'Biology')],
            'raw_data': paper
        } for paper in filtered_papers]

    def get_full_text(self, paper: Dict) -> Optional[str]:
        try:
            paper_id = paper['id']
            
            # キャッシュをチェック
            cached_content = self._get_cached_content(f"biorxiv_{paper_id}")
            if cached_content:
                return cached_content

            self._wait_for_rate_limit()
            
            # bioRxiv XMLを取得
            xml_url = f"https://www.biorxiv.org/content/{paper_id}.xml"
            response = requests.get(xml_url)
            if not response.ok:
                return None

            # XMLをパースして本文を抽出
            soup = BeautifulSoup(response.content, 'xml')
            content = self._extract_text_from_xml(soup)
            
            # キャッシュに保存
            if content:
                self._cache_content(f"biorxiv_{paper_id}", content)
            
            return content

        except Exception as e:
            print(f"Error getting bioRxiv full text: {e}")
            return None

class PubmedSource(PaperSource):
    def __init__(self):
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
        self.number_converter = NumberConverter()
        self.last_request_time = 0
        self.min_request_interval = 0.34  # NCBI API制限: 3リクエスト/秒

    def _wait_for_rate_limit(self):
        """レート制限のための待機"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last_request)
        self.last_request_time = time.time()

    def search(self, query: str, max_results: int = 5) -> List[Dict]:
        try:
            self._wait_for_rate_limit()
            search_params = {
                "db": "pubmed",
                "term": query,
                "retmax": max_results,
                "retmode": "json"
            }
            search_response = requests.get(f"{self.base_url}/esearch.fcgi", params=search_params)
            if not search_response.ok:
                return []

            search_data = search_response.json()
            if 'esearchresult' not in search_data or 'idlist' not in search_data['esearchresult']:
                return []

            results = []
            for pmid in search_data['esearchresult']['idlist']:
                self._wait_for_rate_limit()
                summary_params = {"db": "pubmed", "id": pmid, "retmode": "json"}
                summary_response = requests.get(f"{self.base_url}/esummary.fcgi", params=summary_params)
                if not summary_response.ok:
                    continue

                details = summary_response.json()
                if 'result' not in details or pmid not in details['result']:
                    continue

                paper = details['result'][pmid]
                authors = [author.get('name', '') for author in paper.get('authors', []) if author.get('name')]

                # PMC IDを取得
                pmc_id = self._get_pmc_id(pmid)

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
                    'raw_data': paper,
                    'pmc_id': pmc_id
                })
            return results

        except Exception as e:
            print(f"PubMed search error: {e}")
            return []

    def _get_pmc_id(self, pmid: str) -> Optional[str]:
        """Get PMC ID for a given PubMed ID"""
        try:
            self._wait_for_rate_limit()
            params = {
                "db": "pmc",
                "linkname": "pubmed_pmc",
                "id": pmid,
                "retmode": "json"
            }
            response = requests.get(f"{self.base_url}/elink.fcgi", params=params)
            if not response.ok:
                return None

            data = response.json()
            links = data.get('linksets', [{}])[0].get('linksetdbs', [])
            for link in links:
                if link.get('linkname') == 'pubmed_pmc':
                    return link.get('links', [None])[0]
            return None

        except Exception:
            return None

    def get_full_text(self, paper: Dict) -> Optional[str]:
        try:
            paper_id = paper['id']
            
            # キャッシュをチェック
            cached_content = self._get_cached_content(f"pubmed_{paper_id}")
            if cached_content:
                return cached_content

            # PMC IDを使用して本文を取得
            pmc_id = paper.get('pmc_id')
            if not pmc_id:
                pmc_id = self._get_pmc_id(paper_id)
                if not pmc_id:
                    return None

            self._wait_for_rate_limit()
            
            # PMC APIから本文を取得
            params = {
                "db": "pmc",
                "id": pmc_id,
                "rettype": "xml",
                "retmode": "xml"
            }
            response = requests.get(f"{self.base_url}/efetch.fcgi", params=params)
            if not response.ok:
                return None

            # XMLをパースして本文を抽出
            soup = BeautifulSoup(response.content, 'xml')
            content = self._extract_text_from_xml(soup)
            
            # キャッシュに保存
            if content:
                self._cache_content(f"pubmed_{paper_id}", content)
            
            return content

        except Exception as e:
            print(f"Error getting PMC full text: {e}")
            return None
