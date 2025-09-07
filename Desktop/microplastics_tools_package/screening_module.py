import openai
from typing import List, Dict, Any, Tuple
import json
from datetime import datetime

class ScreeningModule:
    def __init__(self, api_key: str):
        self.client = openai.OpenAI(api_key=api_key)

    def screen_articles(self, articles: List[Dict[str, Any]], inclusion_criteria: str,
                       exclusion_criteria: str) -> List[Dict[str, Any]]:
        """
        Screen articles using AI to determine inclusion/exclusion
        """
        screened_articles = []

        for article in articles:
            try:
                decision, reasoning = self._classify_article(
                    article, inclusion_criteria, exclusion_criteria
                )

                screened_article = article.copy()
                screened_article['screening_decision'] = decision
                screened_article['screening_reasoning'] = reasoning
                screened_article['screened_at'] = datetime.utcnow().isoformat()

                screened_articles.append(screened_article)

            except Exception as e:
                print(f"Error screening article {article.get('pmid', 'unknown')}: {e}")
                screened_article = article.copy()
                screened_article['screening_decision'] = 'unclear'
                screened_article['screening_reasoning'] = f"Error during screening: {str(e)}"
                screened_articles.append(screened_article)

        return screened_articles

    def _classify_article(self, article: Dict[str, Any], inclusion: str, exclusion: str) -> Tuple[str, str]:
        """
        Use AI to classify a single article
        """
        title = article.get('title', '')
        abstract = article.get('abstract', '')

        prompt = f"""
        Based on the following inclusion and exclusion criteria, determine if this article should be included in the systematic review.

        INCLUSION CRITERIA:
        {inclusion}

        EXCLUSION CRITERIA:
        {exclusion}

        ARTICLE TITLE:
        {title}

        ARTICLE ABSTRACT:
        {abstract}

        Please respond with a JSON object containing:
        - "decision": "include", "exclude", or "unclear"
        - "reasoning": brief explanation for your decision
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert systematic reviewer. Analyze articles based on inclusion/exclusion criteria and make precise decisions."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.3
            )

            result_text = response.choices[0].message.content

            try:
                result = json.loads(result_text)
                decision = result.get('decision', 'unclear')
                reasoning = result.get('reasoning', 'No reasoning provided')
            except json.JSONDecodeError:
                # Fallback parsing
                if 'include' in result_text.lower():
                    decision = 'include'
                elif 'exclude' in result_text.lower():
                    decision = 'exclude'
                else:
                    decision = 'unclear'
                reasoning = result_text

            return decision, reasoning

        except Exception as e:
            return 'unclear', f"AI classification failed: {str(e)}"

    def screen_studies(self, articles: List[Dict[str, Any]], inclusion_criteria: str,
                      exclusion_criteria: str) -> List[Dict[str, Any]]:
        """
        Alias for screen_articles - screen studies based on inclusion/exclusion criteria
        """
        return self.screen_articles(articles, inclusion_criteria, exclusion_criteria)

    def batch_screen_articles(self, articles: List[Dict[str, Any]], inclusion_criteria: str,
                             exclusion_criteria: str, batch_size: int = 10) -> List[Dict[str, Any]]:
        """
        Screen articles in batches to handle large numbers efficiently
        """
        screened_articles = []

        for i in range(0, len(articles), batch_size):
            batch = articles[i:i + batch_size]
            print(f"Screening batch {i//batch_size + 1} of {(len(articles) + batch_size - 1)//batch_size}")

            batch_screened = self.screen_articles(batch, inclusion_criteria, exclusion_criteria)
            screened_articles.extend(batch_screened)

        return screened_articles

    def get_screening_statistics(self, screened_articles: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Calculate screening statistics
        """
        stats = {
            'total': len(screened_articles),
            'included': 0,
            'excluded': 0,
            'unclear': 0
        }

        for article in screened_articles:
            decision = article.get('screening_decision', 'unclear')
            if decision in stats:
                stats[decision] += 1

        return stats

    def export_screening_results(self, screened_articles: List[Dict[str, Any]], filename: str):
        """
        Export screening results to CSV
        """
        import csv

        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['title', 'authors', 'journal', 'year', 'doi', 'screening_decision', 'screening_reasoning']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for article in screened_articles:
                writer.writerow({
                    'title': article.get('title', ''),
                    'authors': '; '.join(article.get('authors', [])),
                    'journal': article.get('journal', ''),
                    'year': article.get('year', ''),
                    'doi': article.get('doi', ''),
                    'screening_decision': article.get('screening_decision', ''),
                    'screening_reasoning': article.get('screening_reasoning', '')
                })

    def refine_criteria_based_on_screening(self, screened_articles: List[Dict[str, Any]],
                                          original_criteria: Dict[str, str]) -> Dict[str, str]:
        """
        Use AI to suggest refinements to inclusion/exclusion criteria based on screening results
        """
        unclear_articles = [a for a in screened_articles if a.get('screening_decision') == 'unclear']

        if len(unclear_articles) < 3:
            return original_criteria  # Not enough data for refinement

        # Sample some unclear articles
        sample_articles = unclear_articles[:5]

        prompt = f"""
        Based on the following articles that were classified as 'unclear' during screening,
        suggest refinements to the inclusion and exclusion criteria.

        Original Inclusion Criteria:
        {original_criteria.get('inclusion', '')}

        Original Exclusion Criteria:
        {original_criteria.get('exclusion', '')}

        Unclear Articles:
        {json.dumps([{'title': a.get('title', ''), 'abstract': a.get('abstract', '')[:200] + '...'} for a in sample_articles], indent=2)}

        Please suggest:
        1. Refined inclusion criteria
        2. Refined exclusion criteria
        3. Reasoning for the changes

        Respond in JSON format.
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert in systematic review methodology. Help refine inclusion/exclusion criteria based on screening results."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.5
            )

            result_text = response.choices[0].message.content

            try:
                suggestions = json.loads(result_text)
                return {
                    'inclusion': suggestions.get('refined_inclusion', original_criteria.get('inclusion', '')),
                    'exclusion': suggestions.get('refined_exclusion', original_criteria.get('exclusion', ''))
                }
            except json.JSONDecodeError:
                return original_criteria

        except Exception as e:
            print(f"Failed to refine criteria: {e}")
            return original_criteria
