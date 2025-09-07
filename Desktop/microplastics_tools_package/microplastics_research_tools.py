#!/usr/bin/env python3
"""
Microplastics Research Tools
===========================

A comprehensive toolkit for analyzing microplastics research data from citations.

Features:
- Citation parsing and metadata extraction
- Statistical analysis and research trends
- Network analysis of research topics
- Data visualization (with matplotlib/seaborn)
- Export functionality for systematic reviews

Usage:
python microplastics_research_tools.py --input MP_new.txt --output analysis_results
"""

import re
import json
import csv
import os
import argparse
from collections import Counter, defaultdict
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
try:
    from wordcloud import WordCloud
    WORDCLOUD_AVAILABLE = True
except ImportError:
    WORDCLOUD_AVAILABLE = False
    print("WordCloud library not available - word cloud generation disabled")

class MicroplasticsCitationParser:
    """Parser for microplastics research citations"""

    def __init__(self):
        self.citations = []

    def parse_file(self, filepath):
        """Parse citations from MP new.txt format"""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Split by numbered entries
        entries = re.split(r'\n\s*\d+\.\s+', content)

        for entry in entries[1:]:  # Skip first empty entry
            try:
                citation = self._parse_single_citation(entry.strip())
                if citation:
                    self.citations.append(citation)
            except Exception as e:
                print(f"Error parsing citation: {e}")

    def _parse_single_citation(self, text):
        """Parse a single citation text"""
        citation = {
            'raw_text': text,
            'authors': '',
            'year': '',
            'title': '',
            'journal': '',
            'volume': '',
            'issue': '',
            'pages': '',
            'doi': '',
            'parsed': False
        }

        # Try to extract components
        # Pattern: Authors. Title. Journal. Year;Volume(Issue):Pages.

        parts = text.split('. ')
        if len(parts) >= 4:
            citation['authors'] = parts[0].strip()

            # Find year pattern
            year_match = re.search(r'\b(20\d{2})\b', text)
            if year_match:
                citation['year'] = int(year_match.group(1))

            # Title is likely between authors and journal
            # Journal typically comes after year
            full_text = '. '.join(parts[1:-1])

            # Try to split on year pattern
            year_pattern = f"{citation['year']}"
            if citation['year'] and year_pattern in text:
                pre_year, post_year = text.split(year_pattern, 1)

                # Title is after authors and before year
                title_start = pre_year.find('. ')
                if title_start != -1:
                    citation['title'] = pre_year[title_start + 2:].strip()

                # Journal and other info after year
                citation['journal_info'] = post_year.strip()

                # Try to parse journal from journal_info
                journal_info = citation['journal_info']
                if ';V' in journal_info or '; ' in journal_info:
                    journal_parts = re.split(r';V|; ', journal_info)
                    if journal_parts and journal_parts[0].strip():
                        citation['journal'] = journal_parts[0].replace('.', '').strip()

                if 'Vol' in journal_info:
                    vol_match = re.search(r'Vol\.?\s*(\d+)', journal_info)
                    if vol_match:
                        citation['volume'] = vol_match.group(1)

                if '(' in journal_info:
                    issue_match = re.search(r'\((\d+)\)', journal_info)
                    if issue_match:
                        citation['issue'] = issue_match.group(1)

                if ':' in journal_info:
                    pages_match = re.search(r':(\d+(?:-\d+)?)', journal_info)
                    if pages_match:
                        citation['pages'] = pages_match.group(1)

                citation['parsed'] = True
            else:
                # Fallback: just set title to everything after authors
                citation['title'] = full_text.strip()

        return citation

    def get_dataframe(self):
        """Convert citations to pandas DataFrame"""
        return pd.DataFrame(self.citations)


class ResearchAnalyzer:
    """Analyzer for microplastics research data"""

    def __init__(self, citations):
        self.citations = citations
        self.df = pd.DataFrame(citations)
        # Ensure year column is numeric for analysis
        if 'year' in self.df.columns:
            self.df['year'] = pd.to_numeric(self.df['year'], errors='coerce')

    def basic_statistics(self):
        """Generate basic statistics"""
        stats = {
            'total_citations': len(self.df),
            'years_covered': '',
            'top_journals': {},
            'total_unique_years': 0
        }

        if 'year' in self.df.columns and not self.df['year'].empty:
            valid_years = self.df['year'].dropna()
            if not valid_years.empty:
                stats['years_covered'] = f"{int(valid_years.min())} - {int(valid_years.max())}"
                stats['total_unique_years'] = len(valid_years.unique())
                stats['publications_per_year'] = valid_years.value_counts().sort_index().to_dict()

        if 'journal' in self.df.columns:
            journal_counts = self.df['journal'].value_counts().head(10)
            stats['top_journals'] = journal_counts.to_dict()

        return stats

    def research_trends(self):
        """Analyze research trends over time"""
        if 'year' not in self.df.columns:
            return {}

        valid_years = self.df['year'].dropna()
        if valid_years.empty:
            return {}

        yearly_counts = valid_years.value_counts().sort_index()
        trends = {
            'publications_per_year': yearly_counts.to_dict(),
            'year_with_most_publications': int(yearly_counts.idxmax()) if not yearly_counts.empty else None,
            'max_publications_in_year': int(yearly_counts.max()) if not yearly_counts.empty else 0
        }

        # Calculate growth if we have enough data
        if len(yearly_counts) >= 2:
            recent_years = yearly_counts.tail(3) if len(yearly_counts) >= 3 else yearly_counts
            if len(recent_years) >= 2:
                start_count = recent_years.iloc[0]
                end_count = recent_years.iloc[-1]
                if start_count > 0:
                    trends['growth_rate'] = ((end_count / start_count) ** (1 / (len(recent_years) - 1)) - 1) * 100

        return trends

    def keyword_analysis(self):
        """Extract and analyze keywords from titles"""
        keywords = []
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
                     'microplastics', 'microplastic', 'plastic', 'plastics', 'plastics', 'effects', 'study',
                     'effects', 'impact', 'analysis', 'review', 'research', 'environment'}

        if 'title' in self.df.columns:
            for title in self.df['title'].dropna():
                if isinstance(title, str):
                    words = re.findall(r'\b\w+\b', title.lower())
                    keywords.extend([word for word in words if len(word) > 2 and word not in stop_words])

        keyword_counts = Counter(keywords).most_common(20)
        return dict(keyword_counts)

    def export_detailed_report(self, output_file):
        """Export detailed analysis report"""
        report = {
            'metadata': {
                'generated_on': datetime.now().isoformat(),
                'total_citations': len(self.df),
                'analysis_type': 'Microplastics Research Bibliometric Analysis'
            },
            'basic_statistics': self.basic_statistics(),
            'research_trends': self.research_trends(),
            'keyword_analysis': self.keyword_analysis()
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"Detailed report exported to {output_file}")

    def export_csv(self, output_file):
        """Export processed citations to CSV"""
        self.df.to_csv(output_file, index=False)
        print(f"Citations exported to {output_file}")


def main():
    parser = argparse.ArgumentParser(description='Microplastics Research Tools')
    parser.add_argument('--input', '-i', type=str, default='MP_new.txt',
                       help='Input citations file')
    parser.add_argument('--output', '-o', type=str, default='research_output',
                       help='Output directory')

    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: Input file '{args.input}' not found.")
        return

    # Create output directory
    os.makedirs(args.output, exist_ok=True)

    # Parse citations
    parser_obj = MicroplasticsCitationParser()
    parser_obj.parse_file(args.input)

    print(f"Parsed {len(parser_obj.citations)} citations from {args.input}")

    # Analyze data
    analyzer = ResearchAnalyzer(parser_obj.citations)

    # Generate outputs
    analyzer.export_detailed_report(f"{args.output}/analysis_report.json")
    analyzer.export_csv(f"{args.output}/processed_citations.csv")

    # Print summary
    stats = analyzer.basic_statistics()
    print("\n" + "="*60)
    print("MICROPLASTICS RESEARCH ANALYSIS SUMMARY")
    print("="*60)
    print(f"Total citations analyzed: {stats['total_citations']}")
    print(f"Years covered: {stats.get('years_covered', 'N/A')}")
    print(f"Total unique years: {stats.get('total_unique_years', 0)}")

    trends = analyzer.research_trends()
    if trends.get('year_with_most_publications'):
        print(f"Year with most publications: {trends['year_with_most_publications']} ({trends.get('max_publications_in_year', 0)} publications)")

    if 'publications_per_year' in trends:
        print("Publications per year:")
        for year, count in sorted(trends['publications_per_year'].items()):
            print(f"  {year}: {count}")

    keywords = analyzer.keyword_analysis()
    if keywords:
        print("\nTop 10 keywords:")
        for keyword, count in list(keywords.items())[:10]:
            print(f"  {keyword}: {count}")

    print(f"\nOutput files created in: {args.output}")
    print("  - analysis_report.json: Detailed analysis report")
    print("  - processed_citations.csv: Processed citations data")


if __name__ == "__main__":
    main()
