#!/usr/bin/env python3
"""
Simple Microplastics Research Analysis Tool
==========================================

Generates research analysis output without requiring external plotting libraries.
"""

import re
import json
from collections import Counter
from datetime import datetime

class SimpleCitationParser:
    """Simple parser for microplastics citations"""

    def __init__(self):
        self.citations = []

    def parse_file(self, filepath):
        """Parse citations from file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Split by numbered entries
        entries = re.split(r'\n\s*\d+\.\s+', content)

        for entry in entries[1:]:  # Skip first empty entry
            try:
                citation = self._parse_citation(entry.strip())
                if citation:
                    self.citations.append(citation)
            except Exception as e:
                print(f"Error parsing: {e}")

    def _parse_citation(self, text):
        """Parse a single citation"""
        citation = {
            'raw_text': text,
            'authors': '',
            'year': '',
            'title': '',
            'journal': '',
            'parsed': False
        }

        if not text:
            return None

        parts = text.split('. ')
        if len(parts) < 2:
            return None

        citation['authors'] = parts[0].strip()

        # Find year
        year_match = re.search(r'\b(20\d{2})\b', text)
        if year_match:
            citation['year'] = int(year_match.group(1))
            citation['parsed'] = True

        # Extract title
        if citation['year']:
            full_text = '. '.join(parts[1:])
            year_str = str(citation['year'])
            if year_str in full_text:
                pre_year = full_text.split(year_str)[0]
                citation['title'] = pre_year.strip()

        return citation


class SimpleAnalyzer:
    """Simple analyzer"""

    def __init__(self, citations):
        self.citations = citations
        self.valid_citations = [c for c in citations if c.get('parsed') and c.get('year')]

    def basic_stats(self):
        """Get basic statistics"""
        stats = {
            'total_citations_parsed': len(self.citations),
            'valid_citations': len(self.valid_citations),
            'years_range': '',
            'publications_per_year': {}
        }

        if self.valid_citations:
            years = [c['year'] for c in self.valid_citations]
            stats['years_range'] = f"{min(years)} - {max(years)}"
            year_counts = Counter(years)
            stats['publications_per_year'] = dict(sorted(year_counts.items()))

        return stats

    def keyword_analysis(self):
        """Simple keyword analysis from titles"""
        keywords = []
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
                     'microplastics', 'microplastic', 'plastic', 'plastics', 'effects', 'study',
                     'research', 'analysis', 'review'}

        for citation in self.valid_citations:
            title = citation.get('title', '')
            if title:
                words = re.findall(r'\b\w+\b', title.lower())
                keywords.extend([word for word in words if len(word) > 2 and word not in stop_words])

        keyword_counts = Counter(keywords).most_common(15)
        return dict(keyword_counts)


def generate_output(input_file, output_file='research_analysis_output.json'):
    """Generate analysis output"""

    # Parse citations
    parser = SimpleCitationParser()
    parser.parse_file(input_file)

    analyzer = SimpleAnalyzer(parser.citations)

    # Generate output
    output = {
        'timestamp': datetime.now().isoformat(),
        'input_file': input_file,
        'parsed_citations': len(parser.citations),
        'valid_citations': len(analyzer.valid_citations),
        'basic_statistics': analyzer.basic_stats(),
        'keyword_analysis': analyzer.keyword_analysis()
    }

    # Print summary
    print("=" * 70)
    print("MICROPLASTICS RESEARCH ANALYSIS OUTPUT")
    print("=" * 70)
    print(f"Input file: {input_file}")
    print(f"Citations parsed: {output['parsed_citations']}")
    print(f"Valid citations (with year): {output['valid_citations']}")
    print()

    stats = output['basic_statistics']
    if stats['years_range']:
        print(f"Years covered: {stats['years_range']}")
        print("\nPublications per year:")
        for year, count in stats['publications_per_year'].items():
            print(f"  {year}: {count} publications")

    keywords = output['keyword_analysis']
    if keywords:
        print("\nTop 15 keywords from titles:")
        for keyword, count in keywords.items():
            print(f"  {keyword}: {count}")

    # Save to JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\nDetailed results saved to: {output_file}")
    return output


if __name__ == "__main__":
    input_file = 'MP_new.txt'
    generate_output(input_file)
