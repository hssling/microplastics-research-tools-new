"""
Microplastics Research Context System for VS Code
================================================

Enhanced with data analysis and visualization tools for microplastics research.

Additional features:
1. Statistical analysis of article metadata
2. Trend analysis over time
3. Co-occurrence analysis of research topics
4. Network visualization of research relationships
5. Export capabilities for further analysis
6. Interactive dashboards for exploration

Usage:
python create_microplastics_context.py
"""

import json
import re
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
import csv
import pandas as pd
import numpy as np
from collections import Counter
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
import networkx as nx
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.cluster import KMeans
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Add the previous class definitions here (MicroplasticsContextBuilder, SearchUtilities, etc.)

class DataAnalyzer:
    def __init__(self, database: Dict):
        self.database = database
        self.df = pd.DataFrame(database['articles'])
        
    def basic_statistics(self) -> Dict:
        """Generate basic statistics about the dataset"""
        stats = {
            'total_articles': len(self.df),
            'years_covered': f"{self.df['year'].min()} - {self.df['year'].max()}",
            'num_journals': self.df['journal'].nunique(),
            'num_authors': self.df['first_author'].nunique(),
            'articles_per_year': self.df['year'].value_counts().to_dict(),
            'top_journals': self.df['journal'].value_counts().head(10).to_dict(),
            'top_authors': self.df['first_author'].value_counts().head(10).to_dict()
        }
        return stats
    
    def research_trends_analysis(self) -> Dict:
        """Analyze research trends over time"""
        # Expand research focus lists into individual rows
        research_focus_expanded = []
        for idx, row in self.df.iterrows():
            for focus in row['research_focus']:
                research_focus_expanded.append({
                    'year': row['year'],
                    'research_focus': focus
                })
        
        focus_df = pd.DataFrame(research_focus_expanded)
        
        # Calculate trends
        trends = {}
        for focus in focus_df['research_focus'].unique():
            focus_trend = focus_df[focus_df['research_focus'] == focus]['year'].value_counts().sort_index()
            trends[focus] = focus_trend.to_dict()
        
        return trends
    
    def co_occurrence_analysis(self) -> Dict:
        """Analyze co-occurrence of research topics"""
        # Create co-occurrence matrix for research focus areas
        focus_areas = list(set([focus for sublist in self.df['research_focus'] for focus in sublist]))
        co_occurrence = pd.DataFrame(0, index=focus_areas, columns=focus_areas)
        
        for _, row in self.df.iterrows():
            focuses = row['research_focus']
            for i, focus1 in enumerate(focuses):
                for focus2 in focuses[i+1:]:
                    co_occurrence.loc[focus1, focus2] += 1
                    co_occurrence.loc[focus2, focus1] += 1
        
        return co_occurrence.to_dict()
    
    def generate_wordcloud(self, output_path: str):
        """Generate a word cloud from article titles and keywords"""
        text = ' '.join(self.df['title'].tolist() + 
                       [' '.join(keywords) for keywords in self.df['keywords']])
        
        wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text)
        
        plt.figure(figsize=(10, 5))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.title('Microplastics Research Word Cloud')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
    
    def create_timeline_visualization(self, output_path: str):
        """Create a timeline visualization of research trends"""
        # Prepare data for timeline
        timeline_data = []
        for _, row in self.df.iterrows():
            for focus in row['research_focus']:
                timeline_data.append({
                    'year': row['year'],
                    'research_focus': focus,
                    'journal': row['journal']
                })
        
        timeline_df = pd.DataFrame(timeline_data)
        
        # Create visualization
        plt.figure(figsize=(12, 8))
        
        # Count articles by year and research focus
        focus_counts = timeline_df.groupby(['year', 'research_focus']).size().unstack(fill_value=0)
        
        # Plot stacked area chart
        focus_counts.plot(kind='area', stacked=True, colormap='tab20', alpha=0.7)
        plt.title('Microplastics Research Trends Over Time')
        plt.xlabel('Year')
        plt.ylabel('Number of Publications')
        plt.legend(title='Research Focus', bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        plt.savefig(output_path, dpi=300)
        plt.close()
    
    def create_network_graph(self, output_path: str):
        """Create a network graph of research relationships"""
        G = nx.Graph()
        
        # Add nodes for research focus areas
        focus_areas = list(set([focus for sublist in self.df['research_focus'] for focus in sublist]))
        for focus in focus_areas:
            G.add_node(focus, type='research_focus')
        
        # Add nodes for journals
        journals = self.df['journal'].unique()
        for journal in journals:
            G.add_node(journal, type='journal')
        
        # Add edges based on co-occurrence
        for _, row in self.df.iterrows():
            journal = row['journal']
            focuses = row['research_focus']
            
            for focus in focuses:
                if G.has_edge(journal, focus):
                    G[journal][focus]['weight'] += 1
                else:
                    G.add_edge(journal, focus, weight=1)
        
        # Create visualization
        plt.figure(figsize=(15, 10))
        
        # Node colors by type
        node_colors = []
        for node in G.nodes():
            if G.nodes[node]['type'] == 'research_focus':
                node_colors.append('lightblue')
            else:
                node_colors.append('lightcoral')
        
        # Node sizes by degree
        node_sizes = [G.degree(node) * 50 for node in G.nodes()]
        
        # Edge widths by weight
        edge_widths = [G[u][v]['weight'] / 5 for u, v in G.edges()]
        
        # Layout
        pos = nx.spring_layout(G, k=3, iterations=50)
        
        # Draw network
        nx.draw_networkx_nodes(G, pos, node_size=node_sizes, node_color=node_colors, alpha=0.7)
        nx.draw_networkx_edges(G, pos, width=edge_widths, alpha=0.5)
        nx.draw_networkx_labels(G, pos, font_size=8)
        
        plt.title('Research Network: Journals and Research Focus Areas')
        plt.axis('off')
        plt.tight_layout()
        plt.savefig(output_path, dpi=300)
        plt.close()
        
        return G
    
    def topic_modeling(self, num_topics: int = 5) -> Dict:
        """Perform topic modeling on article titles"""
        # Preprocess text
        vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        X = vectorizer.fit_transform(self.df['title'])
        
        # Apply LDA
        lda = LatentDirichletAllocation(n_components=num_topics, random_state=42)
        lda.fit(X)
        
        # Extract topics
        feature_names = vectorizer.get_feature_names_out()
        topics = {}
        
        for topic_idx, topic in enumerate(lda.components_):
            top_words = [feature_names[i] for i in topic.argsort()[:-11:-1]]
            topics[f"Topic {topic_idx + 1}"] = top_words
        
        # Assign topics to documents
        topic_results = lda.transform(X)
        self.df['dominant_topic'] = topic_results.argmax(axis=1) + 1
        
        return topics
    
    def create_interactive_dashboard(self, output_path: str):
        """Create an interactive HTML dashboard"""
        # Research focus distribution
        focus_counts = Counter([focus for sublist in self.df['research_focus'] for focus in sublist])
        focus_df = pd.DataFrame.from_dict(focus_counts, orient='index', columns=['count']).reset_index()
        focus_df = focus_df.rename(columns={'index': 'research_focus'})
        
        # Yearly publication trend
        yearly_counts = self.df['year'].value_counts().sort_index().reset_index()
        yearly_counts.columns = ['year', 'count']
        
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Research Focus Distribution', 'Publications Over Time', 
                           'Top Journals', 'Topic Distribution'),
            specs=[[{"type": "bar"}, {"type": "scatter"}],
                   [{"type": "bar"}, {"type": "pie"}]]
        )
        
        # Research focus bar chart
        fig.add_trace(
            go.Bar(x=focus_df['research_focus'], y=focus_df['count'], name="Research Focus"),
            row=1, col=1
        )
        
        # Yearly trend line chart
        fig.add_trace(
            go.Scatter(x=yearly_counts['year'], y=yearly_counts['count'], mode='lines+markers', name="Publications"),
            row=1, col=2
        )
        
        # Top journals bar chart
        journal_counts = self.df['journal'].value_counts().head(10).reset_index()
        journal_counts.columns = ['journal', 'count']
        fig.add_trace(
            go.Bar(x=journal_counts['journal'], y=journal_counts['count'], name="Journals"),
            row=2, col=1
        )
        
        # Topic distribution pie chart (if topics available)
        if 'dominant_topic' in self.df.columns:
            topic_counts = self.df['dominant_topic'].value_counts().reset_index()
            topic_counts.columns = ['topic', 'count']
            fig.add_trace(
                go.Pie(labels=topic_counts['topic'], values=topic_counts['count'], name="Topics"),
                row=2, col=2
            )
        
        # Update layout
        fig.update_layout(height=800, showlegend=False, title_text="Microplastics Research Dashboard")
        fig.write_html(output_path)
    
    def export_analysis_results(self, output_dir: str):
        """Export all analysis results to files"""
        os.makedirs(output_dir, exist_ok=True)
        
        # Basic statistics
        stats = self.basic_statistics()
        with open(f"{output_dir}/basic_statistics.json", 'w') as f:
            json.dump(stats, f, indent=2)
        
        # Research trends
        trends = self.research_trends_analysis()
        with open(f"{output_dir}/research_trends.json", 'w') as f:
            json.dump(trends, f, indent=2)
        
        # Co-occurrence matrix
        co_occurrence = self.co_occurrence_analysis()
        co_occurrence_df = pd.DataFrame(co_occurrence)
        co_occurrence_df.to_csv(f"{output_dir}/co_occurrence_matrix.csv")
        
        # Visualizations
        self.generate_wordcloud(f"{output_dir}/wordcloud.png")
        self.create_timeline_visualization(f"{output_dir}/timeline.png")
        self.create_network_graph(f"{output_dir}/network_graph.png")
        
        # Topic modeling
        topics = self.topic_modeling()
        with open(f"{output_dir}/topics.json", 'w') as f:
            json.dump(topics, f, indent=2)
        
        # Interactive dashboard
        self.create_interactive_dashboard(f"{output_dir}/dashboard.html")
        
        # Export enhanced dataframe
        self.df.to_csv(f"{output_dir}/enhanced_articles.csv", index=False)
        
        print(f"All analysis results exported to {output_dir}/")


class AdvancedSearch:
    def __init__(self, database: Dict):
        self.database = database
        self.df = pd.DataFrame(database['articles'])
        
    def semantic_search(self, query: str, top_n: int = 10) -> List[Dict]:
        """Perform semantic search based on TF-IDF similarity"""
        from sklearn.metrics.pairwise import cosine_similarity
        
        # Combine title and keywords for better representation
        documents = [f"{row['title']} {' '.join(row['keywords'])}" for _, row in self.df.iterrows()]
        
        # Vectorize documents
        vectorizer = TfidfVectorizer(stop_words='english')
        doc_vectors = vectorizer.fit_transform(documents)
        query_vector = vectorizer.transform([query])
        
        # Calculate similarities
        similarities = cosine_similarity(query_vector, doc_vectors).flatten()
        
        # Get top results
        top_indices = similarities.argsort()[-top_n:][::-1]
        results = []
        
        for idx in top_indices:
            article = self.df.iloc[idx].to_dict()
            article['similarity_score'] = float(similarities[idx])
            results.append(article)
        
        return results
    
    def filter_by_multiple_criteria(self, filters: Dict) -> List[Dict]:
        """Filter articles by multiple criteria with flexible matching"""
        filtered_df = self.df.copy()
        
        for key, value in filters.items():
            if key == 'year_range':
                start, end = value
                filtered_df = filtered_df[(filtered_df['year'] >= start) & (filtered_df['year'] <= end)]
            elif key == 'research_focus':
                filtered_df = filtered_df[filtered_df['research_focus'].apply(lambda x: value in x)]
            elif key == 'environment':
                filtered_df = filtered_df[filtered_df['environment'].apply(lambda x: value in x)]
            elif key == 'journal':
                filtered_df = filtered_df[filtered_df['journal'] == value]
            elif key == 'keywords':
                filtered_df = filtered_df[filtered_df['keywords'].apply(lambda x: any(kw in x for kw in value))]
        
        return filtered_df.to_dict('records')
    
    def find_similar_articles(self, article_id: int, top_n: int = 5) -> List[Dict]:
        """Find articles similar to a given article"""
        from sklearn.metrics.pairwise import cosine_similarity
        from sklearn.feature_extraction.text import TfidfVectorizer
        
        # Get the target article
        target_article = self.df[self.df['id'] == article_id].iloc[0]
        
        # Prepare documents
        documents = [f"{row['title']} {' '.join(row['keywords'])}" for _, row in self.df.iterrows()]
        
        # Vectorize
        vectorizer = TfidfVectorizer(stop_words='english')
        doc_vectors = vectorizer.fit_transform(documents)
        
        # Find target index
        target_idx = self.df[self.df['id'] == article_id].index[0]
        
        # Calculate similarities
        similarities = cosine_similarity(doc_vectors[target_idx], doc_vectors).flatten()
        
        # Get top similar articles (excluding the target itself)
        similar_indices = similarities.argsort()[-(top_n+1):-1][::-1]
        results = []
        
        for idx in similar_indices:
            article = self.df.iloc[idx].to_dict()
            article['similarity_score'] = float(similarities[idx])
            results.append(article)
        
        return results


def main():
    """Main function to create the enhanced context system"""
    # Read citations from the MP new.txt file
    citations = read_citations_from_file('MP new.txt')
    
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
    
    # Perform advanced data analysis
    analyzer = DataAnalyzer(database)
    
    # Basic statistics
    stats = analyzer.basic_statistics()
    print("\n=== BASIC STATISTICS ===")
    print(f"Total articles: {stats['total_articles']}")
    print(f"Years covered: {stats['years_covered']}")
    print(f"Number of journals: {stats['num_journals']}")
    print(f"Number of authors: {stats['num_authors']}")
    
    # Export all analysis results
    analyzer.export_analysis_results('output/analysis')
    
    # Demonstrate advanced search
    advanced_search = AdvancedSearch(database)
    
    print("\n=== SAMPLE SEMANTIC SEARCH ===")
    query = "microplastics toxicity human health"
    results = advanced_search.semantic_search(query, top_n=3)
    for i, result in enumerate(results):
        print(f"{i+1}. {result['title']} (Score: {result['similarity_score']:.3f})")
    
    print("\n=== SAMPLE FILTERING ===")
    filters = {
        'year_range': (2023, 2025),
        'research_focus': 'Human Health'
    }
    filtered_results = advanced_search.filter_by_multiple_criteria(filters)
    print(f"Found {len(filtered_results)} articles published between 2023-2025 on Human Health")
    
    if filtered_results:
        sample_result = filtered_results[0]
        print(f"Sample: {sample_result['title']} ({sample_result['year']})")
    
    # Find similar articles if we have at least one article
    if len(database['articles']) > 0:
        print("\n=== SAMPLE SIMILAR ARTICLES ===")
        similar_articles = advanced_search.find_similar_articles(1, top_n=3)
        for i, article in enumerate(similar_articles):
            print(f"{i+1}. {article['title']} (Score: {article['similarity_score']:.3f})")
    
    print("\nFiles created:")
    print("  - output/microplastics_database.json (Complete article database)")
    print("  - output/search_index.json (Search index for quick lookups)")
    print("  - output/microplastics.code-workspace (VS Code workspace settings)")
    print("  - output/microplastics_articles.csv (CSV for use with the extraction app)")
    print("  - output/analysis/ (Directory with all analysis results and visualizations)")
    
    print("\nYou can now:")
    print("1. Open the VS Code workspace: output/microplastics.code-workspace")
    print("2. Load the CSV file into your extraction app: output/microplastics_articles.csv")
    print("3. Explore the interactive dashboard: output/analysis/dashboard.html")
    print("4. Use the analysis results for your systematic review")


if __name__ == "__main__":
    main()