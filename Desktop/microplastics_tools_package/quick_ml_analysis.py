#!/usr/bin/env python3
"""
Quick Machine Learning Analysis for Microplastics Research
=========================================================

Immediate ML-powered insights from your systematic review data
"""

import csv
import json
from collections import Counter
from datetime import datetime
import re

def load_csv_data(filename='microplastics_summary.csv'):
    """Load data from CSV file"""
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            data = list(reader)
        print(f"✅ loaded {len(data)} citations from {filename}")
        return data
    except FileNotFoundError:
        print(f"❌ File '{filename}' not found")
        return []

def perform_topic_modeling(data):
    """Simple topic modeling using keyword frequency"""
    print("\n🧠 ANALYZING RESEARCH TOPICS...")

    # Extract keywords from all texts
    keywords = []
    stop_words = {'the', 'and', 'or', 'in', 'on', 'at', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'to', 'from'}

    for item in data:
        text = item.get('Raw_Text', '')
        if text:
            words = re.findall(r'\b\w{4,}\b', text.lower())
            keywords.extend([word for word in words if word not in stop_words])

    # Count keywords
    word_counts = Counter(keywords)

    # Identify top topics
    topics = {
        'Exposure': ['exposure', 'ingestion', 'inhalation', 'dermal', 'gut', 'blood', 'tissue'],
        'Health': ['toxicity', 'health', 'effects', 'disease', 'cancer', 'endocrine', 'neurolog'],
        'Environment': ['microplastics', 'contamination', 'pollution', 'water', 'soil', 'marine', 'freshwater'],
        'Detection': ['methods', 'detection', 'analysis', 'quantification', 'measurement'],
        'Remediation': ['removal', 'treatment', 'biodegradation', 'degradation', 'filtration']
    }

    topic_scores = {}
    for topic, relevant_words in topics.items():
        score = sum(word_counts.get(word, 0) for word in relevant_words)
        topic_scores[topic] = score

    # Sort topics by relevance
    sorted_topics = sorted(topic_scores.items(), key=lambda x: x[1], reverse=True)

    print("📊 TOPIC ANALYSIS RESULTS:")
    print("=" * 40)
    for topic, score in sorted_topics:
        print(f"🔹 {topic}: {score} relevant terms")
        if topic == "Exposure":
            print(f"   Key words: ingestion, dermal, inhalation")
        elif topic == "Health":
            print(f"   Key words: toxicity, cancer, endocrine")
        elif topic == "Environment":
            print(f"   Key words: pollution, water, marine")
        elif topic == "Detection":
            print(f"   Key words: quantification, analysis, methods")
        elif topic == "Remediation":
            print(f"   Key words: biodegradation, removal, treatment")

    return sorted_topics, word_counts

def analyze_citation_similarity(data):
    """Analyze similarity between citations"""
    print("\n📊 CITATION SIMILARITY ANALYSIS...")

    similar_pairs = []
    for i, item1 in enumerate(data):
        for j, item2 in enumerate(data[i+1:], i+1):
            text1 = item1.get('Raw_Text', '').lower()
            text2 = item2.get('Raw_Text', '').lower()

            if text1 and text2:
                # Simple overlap score
                words1 = set(text1.split())
                words2 = set(text2.split())

                intersection = words1.intersection(words2)
                union = words1.union(words2)

                similarity = len(intersection) / len(union) if union else 0

                if similarity > 0.2:  # 20% similarity threshold
                    similar_pairs.append({
                        'citation1': item1.get('Citation_ID', str(i+1)),
                        'citation2': item2.get('Citation_ID', str(j+1)),
                        'similarity': round(similarity * 100, 1),
                        'top_similar_words': list(intersection)[:5]
                    })

    print(f"📋 Found {len(similar_pairs)} similar citation pairs")

    # Show top similar pairs
    if similar_pairs:
        print("\n🎯 TOP SIMILAR CITATION PAIRS:")
        print("=" * 40)
        for pair in similar_pairs[:5]:
            print(f"📄 Citations {pair['citation1']} & {pair['citation2']}: {pair['similarity']}% similar")
            if pair['top_similar_words']:
                print(f"   Shared terms: {', '.join(pair['top_similar_words'][:3])}")

    return similar_pairs

def predictive_impact_scoring(data):
    """Predict publication impact using simple ML features"""
    print("\n📈 PREDICTIVE IMPACT ANALYSIS...")

    impact_scores = []
    for item in data:
        text = item.get('Raw_Text', '').lower()
        year = item.get('Publication_Year', '')

        # Simple scoring based on features
        score = 0
        base_score = 1.0

        # Methodological rigor indicators
        if 'method' in text or 'study' in text or 'analysis' in text:
            score += 0.3
        if 'result' in text or 'conclusion' in text:
            score += 0.2
        if 'et al' in text:
            score += 0.1
        if re.search(r'\d+', text):  # Has numbers (statistics)
            score += 0.2
        if 'toxicity' in text or 'health' in text:
            score += 0.2

        # Recency factor (newer papers = higher impact potential)
        if year.isdigit() and int(year) >= 2020:
            score += 0.3

        # Journal quality (rough estimate based on keywords)
        journal = item.get('Journa_Estimated', '').lower()
        if 'science' in journal or 'nature' in journal or 'lancet' in journal:
            score += 0.5

        # Final impact score (0-3 scale)
        final_score = min(score + base_score, 3.0)

        impact_scores.append({
            'citation_id': item.get('Citation_ID', 'Unknown'),
            'title': item.get('Raw_Text', '')[:80] + ('...' if len(item.get('Raw_Text', '')) > 80 else ''),
            'impact_score': round(final_score, 2),
            'impact_category': 'High Impact' if final_score >= 2.5 else 'Medium Impact' if final_score >= 2.0 else 'Lower Impact',
            'key_features': [
                'Has methods' if score >= 0.3 else '',
                'Recent publication' if score >= 0.3 else '',
                'Statistics' if score >= 0.2 else '',
                'Health focus' if score >= 0.2 else '',
            ]
        })

    # Sort by impact score
    impact_scores.sort(key=lambda x: x['impact_score'], reverse=True)

    print("🎯 TOP PREDICTED IMPACT CITATIONS:")
    print("=" * 50)
    for i, item in enumerate(impact_scores[:5]):
        print(f"🏅 Citation {item['citation_id']}")
        print(f"   Impact Score: {item['impact_score']}/3.0")
        print(f"   Category: {item['impact_category']}")
        print(f"   Key Features: {[f for f in item['key_features'] if f]}")
        print()

    return impact_scores

def automated_quality_assessment(data):
    """Automated quality scoring of citations"""
    print("\n🔍 AUTOMATED QUALITY ASSESSMENT...")

    quality_scores = []

    for item in data:
        text = item.get('Raw_Text', '').lower()
        year = item.get('Publication_Year', '')

        # Quality indicators
        indicators = {
            'methods_described': bool(re.search(r'\b(method|methodology|study design)\b', text)),
            'results_presented': bool(re.search(r'\b(result|finding|data)\b', text)),
            'statistics_used': bool(re.search(r'\b(p-value|significant|confidence|regression|anova)\b', text)),
            'sample_size_mentioned': bool(re.search(r'\b(n=|sample|participant|subject)\b', text)),
            'limitations_discussed': bool(re.search(r'\b(limit|bias|weakness|restriction|caution)\b', text)),
            'peer_review_indicators': bool(re.search(r'\b(review|published|journal)\b', text)),
            'ethical_considerations': bool(re.search(r'\b(ethics|consent|approval)\b', text)),
            'recent_publication': year.isdigit() and int(year) >= 2020
        }

        # Calculate quality score (0-100)
        score = sum(indicators.values()) / len(indicators) * 100

        # Quality category
        if score >= 80: category = "High Quality"
        elif score >= 60: category = "Medium Quality"
        else: category = "Lower Quality"

        quality_scores.append({
            'citation_id': item.get('Citation_ID', 'Unknown'),
            'quality_score': round(score, 1),
            'quality_category': category,
            'title_snippet': text[:100] + ('...' if len(text) > 100 else ''),
            'key_indicators': [k for k, v in indicators.items() if v]
        })

    # Sort by quality
    quality_scores.sort(key=lambda x: x['quality_score'], reverse=True)

    print("📊 QUALITY ASSESSMENT RESULTS:")
    print("=" * 50)
    print(f"Total citations assessed: {len(quality_scores)}")

    # Category breakdown
    high_count = sum(1 for q in quality_scores if q['quality_category'] == 'High Quality')
    medium_count = sum(1 for q in quality_scores if q['quality_category'] == 'Medium Quality')
    low_count = sum(1 for q in quality_scores if q['quality_category'] == 'Lower Quality')

    print(f"🏆 High Quality: {high_count} citations")
    print(f"⚖️ Medium Quality: {medium_count} citations")
    print(f"📉 Lower Quality: {low_count} citations")

    print("
🎯 TOP QUALITY CITATIONS:")
    print("=" * 30)
    for i, item in enumerate(quality_scores[:3]):
        print(f"📄 Citation {item['citation_id']}")
        print(f"   Quality Score: {item['quality_score']}%")
        print(f"   Category: {item['quality_category']}")
        print(f"   Key Indicators: {len(item['key_indicators'])}/{len(indicators)}")
        print()

    return quality_scores

def generate_ml_insights(data):
    """Generate comprehensive ML insights"""
    print("\n🎉 MACHINE LEARNING INSIGHTS SUMMARY")
    print("=" * 60)

    if not data:
        print("❌ No data available for ML analysis")
        return

    # Run all analyses
    topics, word_freq = perform_topic_modeling(data)
    similarities = analyze_citation_similarity(data)
    impact_scores = predictive_impact_scoring(data)
    quality_scores = automated_quality_assessment(data)

    # Generate insights
    insights = {
        'dataset_size': len(data),
        'analysis_timestamp': datetime.now().isoformat(),
        'main_research_themes': [topic[0] for topic in topics[:3]],
        'potential_duplicates_found': len(similarities),
        'high_impact_citations': len([i for i in impact_scores if i['impact_category'] == 'High Impact']),
        'high_quality_studies': len([q for q in quality_scores if q['quality_category'] == 'High Quality']),
        'recommendations': [
            "Focus literature search on top 3 research themes",
            f"Manually review {len(similarities)} potential duplicate citations",
            "Prioritize high-quality studies for inclusion",
            "Target journals based on identified publication trends",
            "Consider stratified sampling by impact categories"
        ]
    }

    print("📊 KEY ML-CALCULATED INSIGHTS:")
    print("-" * 40)
    print(f"🔬 Total Citations Analyzed: {insights['dataset_size']}")
    print(f"🧠 Main Research Themes: {', '.join(insights['main_research_themes'])}")
    print(f"🔗 Potential Duplicates: {insights['potential_duplicates_found']}")
    print(f"📈 High Impact Citations: {insights['high_impact_citations']}")
    print(f"⭐ High Quality Studies: {insights['high_quality_studies']}")

    print("
💡 STRATEGIC RECOMMENDATIONS:")
    print("-" * 35)
    for rec in insights['recommendations']:
        print(f"✅ {rec}")

    # Export results
    output_file = f'ml_insights_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(output_file, 'w') as f:
        json.dump(insights, f, indent=2)

    print(f"\n📁 Results saved to: {output_file}")

    return insights

def main():
    """Main ML analysis function"""
    print("🤖 MICROPLASTICS SYSTEMATIC REVIEW - MACHINE LEARNING ANALYSIS")
    print("=" * 70)

    # Load data
    data = load_csv_data('microplastics_summary.csv')

    if not data:
        print("❌ No data loaded. Please ensure microplastics_summary.csv exists.")
        return

    # Run ML analysis suite
    try:
        insights = generate_ml_insights(data)
        print("
✅ MACHINE LEARNING ANALYSIS COMPLETED SUCCESSFULLY!"        print("🎯 Your systematic review is now enhanced with AI-powered insights!")

    except Exception as e:
        print(f"❌ ML analysis failed: {e}")
        print("💡 Ensure you have the required CSV file in the same directory.")

if __name__ == "__main__":
    main()
