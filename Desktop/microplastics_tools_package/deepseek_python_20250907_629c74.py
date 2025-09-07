"""
Microplastics Research Context System for VS Code
================================================

This script creates a comprehensive searchable context system for microplastics research articles.
It generates:
1. Structured JSON database of all articles
2. Search utilities for quick article lookup
3. VS Code workspace settings for enhanced search
4. Automated categorization and tagging system

Usage:
python create_microplastics_context.py
"""

import json
import re
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import csv

class MicroplasticsContextBuilder:
    def __init__(self):
        self.articles = []
        self.categories = {
            'study_types': set(),
            'research_focus': set(),
            'journals': set(),
            'years': set(),
            'environments': set(),
            'organisms': set()
        }
        
    def parse_citation(self, citation: str, index: int) -> Dict:
        """Parse citation string into structured data"""
        
        # Extract basic information using regex patterns
        author_match = re.match(r'^([^.]+)', citation)
        first_author = author_match.group(1).strip() if author_match else ""
        
        # Extract year
        year_match = re.search(r'\b(20\d{2})\b', citation)
        year = int(year_match.group(1)) if year_match else None
        
        # Extract journal - typically between the last period and year
        journal_pattern = r'\.([^.]+)\.\s*\d{4}'
        journal_match = re.search(journal_pattern, citation)
        journal = journal_match.group(1).strip() if journal_match else ""
        
        # Extract title - between first period and journal
        title_match = re.search(r'^\s*[^.]+\.\s*([^.]+?)\.', citation)
        title = title_match.group(1).strip() if title_match else ""
        
        # Categorize study type based on title keywords
        study_type = self._classify_study_type(title)
        research_focus = self._classify_research_focus(title + " " + journal)
        environment = self._classify_environment(title)
        organisms = self._classify_organisms(title)
        
        article = {
            'id': index,
            'first_author': first_author,
            'year': year,
            'title': title,
            'journal': journal,
            'full_citation': citation.strip(),
            'study_type': study_type,
            'research_focus': research_focus,
            'environment': environment,
            'organisms': organisms,
            'keywords': self._extract_keywords(title + " " + journal),
            'date_added': datetime.now().isoformat()
        }
        
        # Add to categories for later reference
        self._update_categories(article)
        
        return article
    
    def _classify_study_type(self, title: str) -> str:
        """Classify study type based on title keywords"""
        title_lower = title.lower()
        
        if 'systematic review' in title_lower and 'meta-analysis' in title_lower:
            return 'Systematic Review & Meta-analysis'
        elif 'systematic review' in title_lower:
            return 'Systematic Review'
        elif 'meta-analysis' in title_lower:
            return 'Meta-analysis'
        elif 'review' in title_lower:
            return 'Review'
        elif any(word in title_lower for word in ['in vitro', 'cell culture', 'cytotoxicity']):
            return 'In Vitro'
        elif any(word in title_lower for word in ['in vivo', 'animal', 'rat', 'mice', 'mouse']):
            return 'In Vivo'
        elif 'randomized' in title_lower or 'controlled trial' in title_lower:
            return 'Randomized Controlled Trial'
        elif 'cross-sectional' in title_lower:
            return 'Cross-sectional'
        elif 'cohort' in title_lower:
            return 'Cohort'
        else:
            return 'Experimental/Observational'
    
    def _classify_research_focus(self, text: str) -> List[str]:
        """Classify research focus based on content"""
        text_lower = text.lower()
        focus_areas = []
        
        focus_keywords = {
            'Human Health': ['human health', 'human exposure', 'human consumption', 'digestive', 'respiratory', 'reproductive health'],
            'Reproductive Health': ['reproductive', 'pregnancy', 'fertility', 'fetal', 'maternal'],
            'Toxicity': ['toxic', 'cytotoxic', 'genotoxic', 'hepatotoxic', 'neurotoxic'],
            'Environmental Distribution': ['occurrence', 'distribution', 'environmental', 'contamination'],
            'Detection Methods': ['detection', 'analytical', 'identification', 'quantification', 'instrumentation'],
            'Ecological Effects': ['ecological', 'ecosystem', 'benthic', 'aquatic organisms', 'marine organisms'],
            'Remediation': ['removal', 'degradation', 'treatment', 'bioremediation'],
            'Risk Assessment': ['risk assessment', 'risk evaluation', 'safety'],
            'Sources': ['sources', 'emission', 'release'],
            'Cancer': ['cancer', 'carcinogenic', 'oncology'],
            'Marine Biology': ['marine', 'seafood', 'fish', 'shellfish', 'sea cucumber'],
            'Soil Science': ['soil', 'terrestrial', 'plant'],
            'Food Safety': ['food', 'diet', 'intake', 'consumption']
        }
        
        for focus, keywords in focus_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                focus_areas.append(focus)
        
        return focus_areas if focus_areas else ['General']
    
    def _classify_environment(self, title: str) -> List[str]:
        """Classify environment based on title"""
        title_lower = title.lower()
        environments = []
        
        env_keywords = {
            'Aquatic': ['aquatic', 'water', 'freshwater'],
            'Marine': ['marine', 'sea', 'ocean', 'coastal'],
            'Terrestrial': ['terrestrial', 'soil', 'land'],
            'Food System': ['food', 'diet', 'kitchen', 'consumption'],
            'Air': ['air', 'airborne', 'respiratory'],
            'Drinking Water': ['drinking water', 'water supply'],
            'Laboratory': ['in vitro', 'laboratory', 'simulation']
        }
        
        for env, keywords in env_keywords.items():
            if any(keyword in title_lower for keyword in keywords):
                environments.append(env)
        
        return environments if environments else ['Not Specified']
    
    def _classify_organisms(self, title: str) -> List[str]:
        """Classify organisms based on title"""
        title_lower = title.lower()
        organisms = []
        
        organism_keywords = {
            'Humans': ['human', 'maternal', 'women', 'children', 'patient'],
            'Fish': ['fish', 'aquatic organisms'],
            'Marine Animals': ['marine', 'seafood', 'sea cucumber', 'shellfish', 'crustacea', 'mollusca'],
            'Mammals': ['mammal', 'marine mammals'],
            'Plants': ['plant', 'terrestrial'],
            'Microorganisms': ['microbial', 'bacteria', 'biofilm'],
            'Laboratory Animals': ['rat', 'mice', 'mouse', 'animal'],
            'Cell Lines': ['cell', 'in vitro', 'caco-2']
        }
        
        for organism, keywords in organism_keywords.items():
            if any(keyword in title_lower for keyword in keywords):
                organisms.append(organism)
        
        return organisms if organisms else ['Not Specified']
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract relevant keywords from text"""
        text_lower = text.lower()
        
        # Key terms in microplastics research
        key_terms = [
            'microplastics', 'nanoplastics', 'micro-plastics', 'nano-plastics',
            'polystyrene', 'polyethylene', 'pet', 'pvc', 'polymer',
            'contamination', 'pollution', 'exposure', 'toxicity',
            'bioaccumulation', 'ingestion', 'inhalation',
            'systematic review', 'meta-analysis', 'risk assessment',
            'detection', 'quantification', 'ftir', 'raman',
            'aquatic', 'marine', 'terrestrial', 'soil',
            'human health', 'reproductive', 'respiratory', 'digestive',
            'fish', 'seafood', 'drinking water', 'food safety'
        ]
        
        found_keywords = [term for term in key_terms if term in text_lower]
        return list(set(found_keywords))  # Remove duplicates
    
    def _update_categories(self, article: Dict):
        """Update category sets for later reference"""
        self.categories['study_types'].add(article['study_type'])
        self.categories['research_focus'].update(article['research_focus'])
        self.categories['journals'].add(article['journal'])
        if article['year']:
            self.categories['years'].add(article['year'])
        self.categories['environments'].update(article['environment'])
        self.categories['organisms'].update(article['organisms'])
    
    def build_database(self, citations: List[str]) -> Dict:
        """Build complete database from citations"""
        print("Building microplastics research database...")
        
        for i, citation in enumerate(citations, 1):
            if citation.strip():  # Skip empty lines
                article = self.parse_citation(citation, i)
                self.articles.append(article)
        
        # Convert sets to sorted lists for JSON serialization
        categories_clean = {
            key: sorted(list(values)) for key, values in self.categories.items()
        }
        
        database = {
            'metadata': {
                'total_articles': len(self.articles),
                'created_date': datetime.now().isoformat(),
                'version': '1.0',
                'description': 'Microplastics systematic review article database'
            },
            'categories': categories_clean,
            'articles': self.articles,
            'statistics': self._generate_statistics()
        }
        
        print(f"Database created with {len(self.articles)} articles")
        return database
    
    def _generate_statistics(self) -> Dict:
        """Generate statistics about the database"""
        stats = {
            'total_articles': len(self.articles),
            'year_range': {
                'earliest': min(article['year'] for article in self.articles if article['year']),
                'latest': max(article['year'] for article in self.articles if article['year'])
            },
            'study_type_counts': {},
            'journal_counts': {},
            'research_focus_counts': {}
        }
        
        # Count study types
        for article in self.articles:
            study_type = article['study_type']
            stats['study_type_counts'][study_type] = stats['study_type_counts'].get(study_type, 0) + 1
        
        # Count journals (top 10)
        journal_counts = {}
        for article in self.articles:
            journal = article['journal']
            journal_counts[journal] = journal_counts.get(journal, 0) + 1
        
        stats['journal_counts'] = dict(sorted(journal_counts.items(), key=lambda x: x[1], reverse=True)[:10])
        
        # Count research focus areas
        focus_counts = {}
        for article in self.articles:
            for focus in article['research_focus']:
                focus_counts[focus] = focus_counts.get(focus, 0) + 1
        
        stats['research_focus_counts'] = dict(sorted(focus_counts.items(), key=lambda x: x[1], reverse=True))
        
        return stats


class SearchUtilities:
    def __init__(self, database: Dict):
        self.database = database
        self.articles = database['articles']
    
    def search_by_keyword(self, keyword: str) -> List[Dict]:
        """Search articles by keyword"""
        keyword_lower = keyword.lower()
        results = []
        
        for article in self.articles:
            if (keyword_lower in article['title'].lower() or
                keyword_lower in article['first_author'].lower() or
                keyword_lower in article['journal'].lower() or
                keyword_lower in ' '.join(article['keywords']).lower() or
                any(keyword_lower in focus.lower() for focus in article['research_focus'])):
                results.append(article)
        
        return results
    
    def filter_by_criteria(self, **criteria) -> List[Dict]:
        """Filter articles by multiple criteria"""
        results = self.articles
        
        for key, value in criteria.items():
            if key == 'year_range':
                start, end = value
                results = [a for a in results if a['year'] and start <= a['year'] <= end]
            elif key == 'study_type':
                results = [a for a in results if a['study_type'] == value]
            elif key == 'research_focus':
                results = [a for a in results if value in a['research_focus']]
            elif key == 'environment':
                results = [a for a in results if value in a['environment']]
            elif key == 'journal':
                results = [a for a in results if a['journal'] == value]
        
        return results
    
    def generate_search_index(self) -> Dict:
        """Generate search index for faster lookups"""
        index = {
            'by_author': {},
            'by_year': {},
            'by_journal': {},
            'by_keyword': {},
            'by_study_type': {},
            'by_research_focus': {}
        }
        
        for article in self.articles:
            # Index by author
            author = article['first_author']
            if author not in index['by_author']:
                index['by_author'][author] = []
            index['by_author'][author].append(article['id'])
            
            # Index by year
            year = article['year']
            if year:
                if year not in index['by_year']:
                    index['by_year'][year] = []
                index['by_year'][year].append(article['id'])
            
            # Index by journal
            journal = article['journal']
            if journal not in index['by_journal']:
                index['by_journal'][journal] = []
            index['by_journal'][journal].append(article['id'])
            
            # Index by keywords
            for keyword in article['keywords']:
                if keyword not in index['by_keyword']:
                    index['by_keyword'][keyword] = []
                index['by_keyword'][keyword].append(article['id'])
            
            # Index by study type
            study_type = article['study_type']
            if study_type not in index['by_study_type']:
                index['by_study_type'][study_type] = []
            index['by_study_type'][study_type].append(article['id'])
            
            # Index by research focus
            for focus in article['research_focus']:
                if focus not in index['by_research_focus']:
                    index['by_research_focus'][focus] = []
                index['by_research_focus'][focus].append(article['id'])
        
        return index


def create_vscode_workspace():
    """Create VS Code workspace settings for enhanced search"""
    workspace_settings = {
        "folders": [
            {
                "name": "Microplastics Research",
                "path": "."
            }
        ],
        "settings": {
            "search.exclude": {
                "**/node_modules": True,
                "**/bower_components": True,
                "**/.git": True,
                "**/.DS_Store": True,
                "**/tmp": True
            },
            "search.useRipgrep": True,
            "search.smartCase": True,
            "files.associations": {
                "*.mpdb": "json",
                "*.mpindex": "json"
            },
            "files.watcherExclude": {
                "**/.git/objects/**": True,
                "**/.git/subtree-cache/**": True,
                "**/node_modules/**": True
            }
        },
        "extensions": {
            "recommendations": [
                "ms-python.python",
                "ms-vscode.vscode-json",
                "mechatroner.rainbow-csv",
                "janisdd.vscode-edit-csv"
            ]
        }
    }
    
    return workspace_settings


def read_citations_from_file(file_path: str) -> List[str]:
    """Read citations from the MP new.txt file"""
    citations = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                # Remove numbering and whitespace
                line = re.sub(r'^\d+\.\s*', '', line.strip())
                if line:  # Only add non-empty lines
                    citations.append(line)
    except Exception as e:
        print(f"Error reading file: {e}")
    
    return citations


def export_to_csv(database: Dict, filename: str):
    """Export database to CSV format for use with the app"""
    articles = database['articles']
    
    # Define the field names for CSV export
    fieldnames = [
        'ID', 'First_Author', 'Year', 'Title', 'Journal', 'Study_Type', 
        'Research_Focus', 'Environment', 'Organisms', 'Keywords', 'Full_Citation'
    ]
    
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for article in articles:
                writer.writerow({
                    'ID': article['id'],
                    'First_Author': article['first_author'],
                    'Year': article['year'],
                    'Title': article['title'],
                    'Journal': article['journal'],
                    'Study_Type': article['study_type'],
                    'Research_Focus': '; '.join(article['research_focus']),
                    'Environment': '; '.join(article['environment']),
                    'Organisms': '; '.join(article['organisms']),
                    'Keywords': '; '.join(article['keywords']),
                    'Full_Citation': article['full_citation']
                })
        
        print(f"CSV file exported successfully: {filename}")
    except Exception as e:
        print(f"Error exporting to CSV: {e}")


def main():
    """Main function to create the context system"""
    # Read citations from the MP new.txt file
    citations = read_citations_from_file('C:/Users/hssli/Downloads/MP new.txt')
    
    if not citations:
        print("No citations found. Please check the file path and format.")
        return
    
    # Build the database
    builder = MicroplasticsContextBuilder()
    database = builder.build_database(citations)
    
    # Create output directory if it doesn't exist
    os.makedirs('output', exist_ok=True)
    
    # Save the database as JSON
    with open('output/microplastics_database.json', 'w', encoding='utf-8') as f:
        json.dump(database, f, indent=2, ensure_ascii=False)
    
    # Generate search index
    search_utils = SearchUtilities(database)
    search_index = search_utils.generate_search_index()
    
    with open('output/search_index.json', 'w', encoding='utf-8') as f:
        json.dump(search_index, f, indent=2, ensure_ascii=False)
    
    # Create VS Code workspace settings
    workspace_settings = create_vscode_workspace()
    with open('output/microplastics.code-workspace', 'w', encoding='utf-8') as f:
        json.dump(workspace_settings, f, indent=2)
    
    # Export to CSV for use with the app
    export_to_csv(database, 'output/microplastics_articles.csv')
    
    # Print some statistics
    print(f"\nDatabase Statistics:")
    print(f"Total articles: {database['metadata']['total_articles']}")
    print(f"Year range: {database['statistics']['year_range']['earliest']} - {database['statistics']['year_range']['latest']}")
    print(f"Study types: {', '.join(database['categories']['study_types'])}")
    
    print("\nTop research focus areas:")
    for focus, count in list(database['statistics']['research_focus_counts'].items())[:5]:
        print(f"  {focus}: {count} articles")
    
    print("\nFiles created:")
    print("  - output/microplastics_database.json (Complete article database)")
    print("  - output/search_index.json (Search index for quick lookups)")
    print("  - output/microplastics.code-workspace (VS Code workspace settings)")
    print("  - output/microplastics_articles.csv (CSV for use with the extraction app)")
    
    print("\nYou can now:")
    print("1. Open the VS Code workspace: output/microplastics.code-workspace")
    print("2. Load the CSV file into your extraction app: output/microplastics_articles.csv")
    print("3. Use the JSON files for advanced search and analysis")


if __name__ == "__main__":
    main()