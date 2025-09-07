import openai
from typing import List, Dict, Any, Tuple
import json
from datetime import datetime

class QualityAssessmentModule:
    def __init__(self, api_key: str):
        self.client = openai.OpenAI(api_key=api_key)

    def assess_study_quality(self, study: Dict[str, Any], tool: str = "NOS") -> Dict[str, Any]:
        """
        Assess quality of a single study using specified tool
        """
        if tool.upper() == "NOS":
            return self._assess_nos(study)
        elif tool.upper() == "ROB2":
            return self._assess_rob2(study)
        elif tool.upper() == "AXIS":
            return self._assess_axis(study)
        else:
            return {"error": f"Unknown quality assessment tool: {tool}"}

    def _assess_nos(self, study: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess study using Newcastle-Ottawa Scale (NOS)
        """
        text_content = self._get_study_text(study)

        prompt = f"""
        Assess the quality of this study using the Newcastle-Ottawa Scale (NOS) for cohort studies.

        STUDY INFORMATION:
        Title: {study.get('title', '')}
        Authors: {', '.join(study.get('authors', []))}
        Abstract: {study.get('abstract', '')}

        FULL TEXT (if available):
        {text_content[:2000]}

        Evaluate the study based on NOS criteria:

        SELECTION (up to 4 stars):
        1. Representativeness of the exposed cohort
        2. Selection of the non-exposed cohort
        3. Ascertainment of exposure
        4. Demonstration that outcome of interest was not present at start of study

        COMPARABILITY (up to 2 stars):
        1. Comparability of cohorts on the basis of the design or analysis

        OUTCOME (up to 3 stars):
        1. Assessment of outcome
        2. Was follow-up long enough for outcomes to occur
        3. Adequacy of follow up of cohorts

        Provide a detailed assessment with scores for each category and overall rating.
        Return as JSON with structure:
        {{
            "tool": "NOS",
            "selection_score": 0-4,
            "comparability_score": 0-2,
            "outcome_score": 0-3,
            "total_score": 0-9,
            "overall_rating": "Poor/Fair/Good",
            "detailed_assessment": "...",
            "risk_of_bias": "Low/High/Unclear"
        }}
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert in quality assessment of research studies using standardized tools like NOS, ROB2, and AXIS."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.2
            )

            result_text = response.choices[0].message.content

            try:
                assessment = json.loads(result_text)
            except json.JSONDecodeError:
                assessment = self._parse_assessment_text(result_text)

            assessment.update({
                "study_id": study.get('pmid', study.get('doi', 'unknown')),
                "tool": "NOS",
                "assessed_at": datetime.utcnow().isoformat()
            })

            return assessment

        except Exception as e:
            return {
                "error": f"NOS assessment failed: {str(e)}",
                "study_id": study.get('pmid', study.get('doi', 'unknown')),
                "tool": "NOS"
            }

    def _assess_rob2(self, study: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess study using ROB2 (Risk of Bias 2) tool for randomized trials
        """
        text_content = self._get_study_text(study)

        prompt = f"""
        Assess the risk of bias in this randomized controlled trial using the ROB2 tool.

        STUDY INFORMATION:
        Title: {study.get('title', '')}
        Abstract: {study.get('abstract', '')}

        FULL TEXT (if available):
        {text_content[:2000]}

        Evaluate the following domains:

        1. Bias arising from the randomization process
        2. Bias due to deviations from intended interventions
        3. Bias due to missing outcome data
        4. Bias in measurement of the outcome
        5. Bias in selection of the reported result

        For each domain, rate as: Low risk, Some concerns, High risk

        Provide overall risk of bias rating.
        Return as JSON.
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert in assessing risk of bias in randomized controlled trials using ROB2."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=600,
                temperature=0.2
            )

            result_text = response.choices[0].message.content

            try:
                assessment = json.loads(result_text)
            except json.JSONDecodeError:
                assessment = self._parse_assessment_text(result_text)

            assessment.update({
                "study_id": study.get('pmid', study.get('doi', 'unknown')),
                "tool": "ROB2",
                "assessed_at": datetime.utcnow().isoformat()
            })

            return assessment

        except Exception as e:
            return {
                "error": f"ROB2 assessment failed: {str(e)}",
                "study_id": study.get('pmid', study.get('doi', 'unknown')),
                "tool": "ROB2"
            }

    def _assess_axis(self, study: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess study using AXIS tool for cross-sectional studies
        """
        text_content = self._get_study_text(study)

        prompt = f"""
        Assess the quality of this cross-sectional study using the AXIS tool.

        STUDY INFORMATION:
        Title: {study.get('title', '')}
        Abstract: {study.get('abstract', '')}

        FULL TEXT (if available):
        {text_content[:2000]}

        Evaluate the following criteria:

        1. Were the aims/objectives of the study clear?
        2. Was the study design appropriate for the stated aim(s)?
        3. Was the sample size justified?
        4. Was the target/reference population clearly defined?
        5. Was the sample frame taken from an appropriate population base?
        6. Was the selection process likely to select a representative sample?
        7. Were measures undertaken to address non-response?
        8. Were the exposure measures (e.g. risk factors) clearly defined?
        9. Were the outcome measures (e.g. disease status) clearly defined?
        10. Were the methods used for exposure/outcome measurement valid/reliable?
        11. Were the methods used for exposure/outcome measurement likely to have produced a risk of bias?
        12. Was the statistical analysis appropriate for the study design?
        13. Was the statistical analysis performed using appropriate methods?
        14. Were the basic data adequately described?
        15. Does the response rate justify the findings?
        16. Were the conclusions supported by the results?
        17. Were the limitations of the study discussed?
        18. Were the sources of funding and conflicts of interest stated?
        19. Was the research ethics approval stated?
        20. Was the submission based on a research question that was of sufficient importance to justify publication?

        Rate each item as Yes/No/Unclear and provide overall quality rating.
        Return as JSON.
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert in assessing quality of cross-sectional studies using the AXIS tool."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.2
            )

            result_text = response.choices[0].message.content

            try:
                assessment = json.loads(result_text)
            except json.JSONDecodeError:
                assessment = self._parse_assessment_text(result_text)

            assessment.update({
                "study_id": study.get('pmid', study.get('doi', 'unknown')),
                "tool": "AXIS",
                "assessed_at": datetime.utcnow().isoformat()
            })

            return assessment

        except Exception as e:
            return {
                "error": f"AXIS assessment failed: {str(e)}",
                "study_id": study.get('pmid', study.get('doi', 'unknown')),
                "tool": "AXIS"
            }

    def _get_study_text(self, study: Dict[str, Any]) -> str:
        """
        Get text content from study
        """
        # Try to get from full_text_path if available
        pdf_path = study.get('full_text_path')
        if pdf_path:
            try:
                import pdfplumber
                text = ""
                with pdfplumber.open(pdf_path) as pdf:
                    for page in pdf.pages[:5]:  # First 5 pages
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                return text
            except Exception as e:
                print(f"Error extracting text from PDF {pdf_path}: {e}")

        # Fall back to abstract
        abstract = study.get('abstract', '')
        if abstract:
            return f"Title: {study.get('title', '')}\n\nAbstract: {abstract}"

        return ""

    def _parse_assessment_text(self, text: str) -> Dict[str, Any]:
        """
        Parse assessment text into structured format
        """
        # Simple parsing - extract key information
        assessment = {}

        if 'total_score' in text.lower() or 'score' in text.lower():
            assessment['total_score'] = self._extract_number(text)

        if 'low risk' in text.lower():
            assessment['overall_rating'] = 'Low risk'
            assessment['risk_of_bias'] = 'Low'
        elif 'high risk' in text.lower():
            assessment['overall_rating'] = 'High risk'
            assessment['risk_of_bias'] = 'High'
        elif 'some concerns' in text.lower():
            assessment['overall_rating'] = 'Some concerns'
            assessment['risk_of_bias'] = 'Unclear'

        assessment['detailed_assessment'] = text[:500]  # Truncate for storage

        return assessment

    def _extract_number(self, text: str) -> int:
        """
        Extract first number from text
        """
        import re
        numbers = re.findall(r'\d+', text)
        return int(numbers[0]) if numbers else 0

    def batch_assess_quality(self, studies: List[Dict[str, Any]], tool: str = "NOS") -> List[Dict[str, Any]]:
        """
        Assess quality for multiple studies
        """
        assessments = []

        for study in studies:
            assessment = self.assess_study_quality(study, tool)
            assessments.append(assessment)

        return assessments

    def get_quality_summary(self, assessments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate summary statistics for quality assessments
        """
        summary = {
            'total_studies': len(assessments),
            'tool': assessments[0].get('tool', 'Unknown') if assessments else 'Unknown',
            'low_risk_count': 0,
            'high_risk_count': 0,
            'unclear_count': 0,
            'average_score': 0
        }

        scores = []

        for assessment in assessments:
            risk = assessment.get('risk_of_bias', assessment.get('overall_rating', ''))

            if 'low' in risk.lower():
                summary['low_risk_count'] += 1
            elif 'high' in risk.lower():
                summary['high_risk_count'] += 1
            else:
                summary['unclear_count'] += 1

            score = assessment.get('total_score', assessment.get('score', 0))
            if isinstance(score, (int, float)):
                scores.append(score)

        if scores:
            summary['average_score'] = sum(scores) / len(scores)

        return summary

    def export_assessments(self, assessments: List[Dict[str, Any]], filename: str):
        """
        Export quality assessments to CSV
        """
        import csv

        if not assessments:
            return

        # Get all unique keys
        all_keys = set()
        for assessment in assessments:
            all_keys.update(assessment.keys())

        fieldnames = sorted(list(all_keys))

        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for assessment in assessments:
                writer.writerow(assessment)
