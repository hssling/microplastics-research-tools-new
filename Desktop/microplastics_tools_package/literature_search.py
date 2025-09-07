import requests
from typing import List, Dict, Any
import time
from urllib.parse import urlencode
import json

class LiteratureSearch:
    def __init__(self, email: str = "user@example.com"):
        self.email = email
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
        self.api_key = None  # Optional: get from NCBI for higher rate limits

    def search_pubmed(self, query: str, max_results: int = 100) -> List[Dict[str, Any]]:
        """
        Search PubMed using E-utilities API
        """
        # Step 1: Search for PMIDs
        search_url = f"{self.base_url}esearch.fcgi"
        params = {
            'db': 'pubmed',
            'term': query,
            'retmax': max_results,
            'retmode': 'json',
            'email': self.email
        }

        if self.api_key:
            params['api_key'] = self.api_key

        response = requests.get(search_url, params=params)
        response.raise_for_status()

        search_data = response.json()
        pmids = search_data['esearchresult']['idlist']

        if not pmids:
            return []

        # Step 2: Fetch article details
        fetch_url = f"{self.base_url}efetch.fcgi"
        fetch_params = {
            'db': 'pubmed',
            'id': ','.join(pmids),
            'retmode': 'xml',
            'email': self.email
        }

        if self.api_key:
            fetch_params['api_key'] = self.api_key

        # Respect rate limits
        time.sleep(0.3)

        fetch_response = requests.get(fetch_url, params=fetch_params)
        fetch_response.raise_for_status()

        # Parse XML to extract article info
        articles = self._parse_pubmed_xml(fetch_response.text)

        return articles

    def _parse_pubmed_xml(self, xml_content: str) -> List[Dict[str, Any]]:
        """
        Parse PubMed XML response to extract article information
        """
        # Simple XML parsing - in production, use xml.etree or lxml
        articles = []

        # Split by PubmedArticle tags
        articles_xml = xml_content.split('<PubmedArticle>')[1:]

        for article_xml in articles_xml:
            try:
                article = {}

                # Extract PMID
                if '<PMID' in article_xml:
                    pmid_start = article_xml.find('<PMID') + 6
                    pmid_end = article_xml.find('</PMID>', pmid_start)
                    article['pmid'] = article_xml[pmid_start:pmid_end]

                # Extract title
                if '<ArticleTitle>' in article_xml:
                    title_start = article_xml.find('<ArticleTitle>') + 14
                    title_end = article_xml.find('</ArticleTitle>', title_start)
                    article['title'] = article_xml[title_start:title_end]

                # Extract abstract
                if '<AbstractText>' in article_xml:
                    abstract_start = article_xml.find('<AbstractText>') + 14
                    abstract_end = article_xml.find('</AbstractText>', abstract_start)
                    article['abstract'] = article_xml[abstract_start:abstract_end]

                # Extract authors
                authors = []
                author_sections = article_xml.split('<Author>')
                for author_sec in author_sections[1:]:
                    if '<LastName>' in author_sec:
                        last_start = author_sec.find('<LastName>') + 10
                        last_end = author_sec.find('</LastName>', last_start)
                        last_name = author_sec[last_start:last_end]

                        first_start = author_sec.find('<ForeName>') + 9
                        first_end = author_sec.find('</ForeName>', first_start)
                        first_name = author_sec[first_start:first_end]

                        authors.append(f"{first_name} {last_name}")

                article['authors'] = authors

                # Extract journal
                if '<Title>' in article_xml:
                    journal_start = article_xml.find('<Title>') + 7
                    journal_end = article_xml.find('</Title>', journal_start)
                    article['journal'] = article_xml[journal_start:journal_end]

                # Extract year
                if '<PubDate>' in article_xml:
                    year_start = article_xml.find('<Year>') + 6
                    year_end = article_xml.find('</Year>', year_start)
                    article['year'] = int(article_xml[year_start:year_end])

                # Extract DOI
                if '<ELocationID' in article_xml and 'doi' in article_xml:
                    doi_start = article_xml.find('>doi:', article_xml.find('<ELocationID')) + 5
                    doi_end = article_xml.find('</ELocationID>', doi_start)
                    article['doi'] = article_xml[doi_start:doi_end]

                articles.append(article)

            except Exception as e:
                print(f"Error parsing article: {e}")
                continue

        return articles

    def search_cochrane(self, query: str, max_results: int = 50) -> List[Dict[str, Any]]:
        """
        Search Cochrane Library (simplified - would need API access)
        """
        # Note: Cochrane Library requires subscription/API access
        # This is a placeholder for the actual implementation
        print("Cochrane search requires API access - placeholder implementation")
        return []

    def search_multiple_databases(self, query: str, databases: List[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Search multiple databases simultaneously
        """
        if databases is None:
            databases = ['pubmed']

        results = {}

        for db in databases:
            if db == 'pubmed':
                results['pubmed'] = self.search_pubmed(query)
            elif db == 'cochrane':
                results['cochrane'] = self.search_cochrane(query)
            # Add other databases as needed

        return results

    def deduplicate_results(self, results: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        Remove duplicate articles based on title/DOI
        """
        seen_titles = set()
        seen_dois = set()
        deduplicated = []

        for db_results in results.values():
            for article in db_results:
                title = article.get('title', '').lower().strip()
                doi = article.get('doi', '').lower().strip()

                if title and title not in seen_titles:
                    seen_titles.add(title)
                    deduplicated.append(article)
                elif doi and doi not in seen_dois:
                    seen_dois.add(doi)
                    deduplicated.append(article)

        return deduplicated

    def export_search_results(self, results: List[Dict[str, Any]], filename: str):
        """
        Export search results to CSV
        """
        import csv

        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['title', 'authors', 'journal', 'year', 'abstract', 'doi', 'pmid']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for article in results:
                writer.writerow({
                    'title': article.get('title', ''),
                    'authors': '; '.join(article.get('authors', [])),
                    'journal': article.get('journal', ''),
                    'year': article.get('year', ''),
                    'abstract': article.get('abstract', ''),
                    'doi': article.get('doi', ''),
                    'pmid': article.get('pmid', '')
                })
