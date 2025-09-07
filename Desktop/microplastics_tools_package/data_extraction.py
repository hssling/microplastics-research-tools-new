import openai
from typing import List, Dict, Any, Tuple
import json
import re
from datetime import datetime
import pdfplumber
import pytesseract
from PIL import Image
import io

class DataExtractionModule:
    def __init__(self, api_key: str):
        self.client = openai.OpenAI(api_key=api_key)

    def extract_data_from_articles(self, articles: List[Dict[str, Any]],
                                 extraction_template: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract data from articles using AI and NLP
        """
        extracted_data = []

        for article in articles:
            try:
                data = self._extract_from_single_article(article, extraction_template)
                extracted_data.append(data)
            except Exception as e:
                print(f"Error extracting data from article {article.get('pmid', 'unknown')}: {e}")
                # Add empty extraction record
                extracted_data.append({
                    'article_id': article.get('pmid', article.get('doi', 'unknown')),
                    'extraction_status': 'error',
                    'error_message': str(e),
                    'extracted_at': datetime.utcnow().isoformat()
                })

        return extracted_data

    def _extract_from_single_article(self, article: Dict[str, Any],
                                   extraction_template: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract data from a single article
        """
        text_content = self._get_article_text(article)

        if not text_content:
            return {
                'article_id': article.get('pmid', article.get('doi', 'unknown')),
                'extraction_status': 'no_text',
                'extracted_at': datetime.utcnow().isoformat()
            }

        # Use AI to extract structured data
        extracted_data = self._ai_extract_data(text_content, extraction_template)

        result = {
            'article_id': article.get('pmid', article.get('doi', 'unknown')),
            'extraction_status': 'success',
            'extracted_data': extracted_data,
            'extraction_method': 'ai_nlp',
            'extracted_at': datetime.utcnow().isoformat()
        }

        return result

    def _get_article_text(self, article: Dict[str, Any]) -> str:
        """
        Get text content from article (PDF or text)
        """
        # Try to get from full_text_path if available
        pdf_path = article.get('full_text_path')
        if pdf_path:
            try:
                return self._extract_text_from_pdf(pdf_path)
            except Exception as e:
                print(f"Error extracting text from PDF {pdf_path}: {e}")

        # Fall back to abstract
        abstract = article.get('abstract', '')
        if abstract:
            return f"Title: {article.get('title', '')}\n\nAbstract: {abstract}"

        return ""

    def _extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extract text from PDF using pdfplumber
        """
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"

        return text

    def _extract_text_from_image_pdf(self, pdf_path: str) -> str:
        """
        Extract text from image-based PDF using OCR
        """
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                # Extract images from page
                images = page.images
                for img in images:
                    # Use OCR on image
                    img_text = pytesseract.image_to_string(Image.open(io.BytesIO(img['stream'])))
                    text += img_text + "\n"

        return text

    def _ai_extract_data(self, text: str, extraction_template: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use AI to extract structured data from text
        """
        prompt = f"""
        Extract the following data from the research article text:

        EXTRACTION TEMPLATE:
        {json.dumps(extraction_template, indent=2)}

        ARTICLE TEXT:
        {text[:4000]}  # Limit text length for API

        Please extract the requested data and return it as a JSON object.
        For numerical data, extract the actual numbers.
        For categorical data, use the exact categories specified.
        If data is not available, use null.
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert data extractor for systematic reviews. Extract data accurately and consistently from research articles."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.1
            )

            result_text = response.choices[0].message.content

            try:
                extracted_data = json.loads(result_text)
            except json.JSONDecodeError:
                # Try to extract JSON from response
                json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
                if json_match:
                    extracted_data = json.loads(json_match.group())
                else:
                    extracted_data = {"error": "Could not parse AI response as JSON"}

            return extracted_data

        except Exception as e:
            return {"error": f"AI extraction failed: {str(e)}"}

    def validate_extracted_data(self, extracted_data: Dict[str, Any],
                              validation_rules: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate extracted data against rules
        """
        validation_results = {
            'is_valid': True,
            'errors': [],
            'warnings': []
        }

        for field, rules in validation_rules.items():
            if field in extracted_data:
                value = extracted_data[field]

                # Check required fields
                if rules.get('required', False) and (value is None or value == ""):
                    validation_results['errors'].append(f"Required field '{field}' is missing")
                    validation_results['is_valid'] = False

                # Check data type
                expected_type = rules.get('type')
                if expected_type and value is not None:
                    if expected_type == 'number' and not isinstance(value, (int, float)):
                        try:
                            float(value)  # Try to convert
                        except:
                            validation_results['errors'].append(f"Field '{field}' should be a number")
                            validation_results['is_valid'] = False

                # Check range for numbers
                if expected_type == 'number' and value is not None:
                    min_val = rules.get('min')
                    max_val = rules.get('max')
                    if min_val is not None and value < min_val:
                        validation_results['warnings'].append(f"Field '{field}' value {value} is below minimum {min_val}")
                    if max_val is not None and value > max_val:
                        validation_results['warnings'].append(f"Field '{field}' value {value} is above maximum {max_val}")

                # Check categorical values
                allowed_values = rules.get('allowed_values')
                if allowed_values and value is not None and value not in allowed_values:
                    validation_results['warnings'].append(f"Field '{field}' value '{value}' not in allowed values: {allowed_values}")

        return validation_results

    def export_extraction_results(self, extracted_data: List[Dict[str, Any]], filename: str):
        """
        Export extraction results to CSV
        """
        import csv

        if not extracted_data:
            return

        # Get all unique keys from extracted data
        all_keys = set()
        for item in extracted_data:
            if 'extracted_data' in item:
                all_keys.update(item['extracted_data'].keys())

        fieldnames = ['article_id', 'extraction_status'] + sorted(list(all_keys))

        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for item in extracted_data:
                row = {
                    'article_id': item.get('article_id', ''),
                    'extraction_status': item.get('extraction_status', '')
                }

                if 'extracted_data' in item and isinstance(item['extracted_data'], dict):
                    row.update(item['extracted_data'])

                writer.writerow(row)

    def create_extraction_template(self, research_question: str, study_type: str = "RCT") -> Dict[str, Any]:
        """
        Create a data extraction template based on research question and study type
        """
        prompt = f"""
        Create a data extraction template for a systematic review with the following details:

        Research Question: {research_question}
        Study Type: {study_type}

        Please create a comprehensive extraction template that includes:
        1. Study characteristics (design, participants, setting)
        2. Intervention details
        3. Outcome measures
        4. Results data
        5. Risk of bias information

        Return the template as a JSON object with field names as keys and extraction instructions as values.
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert in systematic review methodology. Create comprehensive data extraction templates."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.2
            )

            template_text = response.choices[0].message.content

            try:
                template = json.loads(template_text)
            except json.JSONDecodeError:
                template = {"error": "Could not parse template"}

            return template

        except Exception as e:
            return {"error": f"Template creation failed: {str(e)}"}
