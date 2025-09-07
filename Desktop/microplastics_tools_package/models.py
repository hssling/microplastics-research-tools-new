"""
AI Model Manager - Support for Multiple AI Models including DeepSeek, Claude, Gemini, and Free Models
"""
import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, Float, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

class AIModelManager:
    """Multi-model AI manager supporting various providers"""

    SUPPORTED_MODELS = {
        # OpenAI models
        'gpt-4-turbo': {'provider': 'openai', 'name': 'gpt-4-turbo-preview'},
        'gpt-4': {'provider': 'openai', 'name': 'gpt-4'},
        'gpt-3.5-turbo': {'provider': 'openai', 'name': 'gpt-3.5-turbo'},

        # Anthropic Claude models
        'claude-3-opus': {'provider': 'anthropic', 'name': 'claude-3-opus-20240229'},
        'claude-3-sonnet': {'provider': 'anthropic', 'name': 'claude-3-sonnet-20240229'},
        'claude-haiku': {'provider': 'anthropic', 'name': 'claude-3-haiku-20240307'},

        # Google Gemini models
        'gemini-pro': {'provider': 'google', 'name': 'gemini-pro'},
        'gemini-pro-vision': {'provider': 'google', 'name': 'gemini-pro-vision'},

        # DeepSeek models (free/open alternatives)
        'deepseek-chat': {'provider': 'deepseek', 'name': 'deepseek-chat'},
        'deepseek-coder': {'provider': 'deepseek', 'name': 'deepseek-coder'},

        # Local/Community models (Ollama)
        'llama-2-7b': {'provider': 'ollama', 'name': 'llama2'},
        'codellama': {'provider': 'ollama', 'name': 'codellama'},
    }

    def __init__(self, default_model: str = 'gpt-4-turbo'):
        self.default_model = default_model
        self.api_keys = self._load_api_keys()
        self.current_model = default_model

    def _load_api_keys(self) -> Dict[str, str]:
        """Load API keys from environment variables"""
        keys = {}

        # OpenAI
        keys['openai'] = os.getenv('OPENAI_API_KEY', '')

        # Anthropic
        keys['anthropic'] = os.getenv('ANTHROPIC_API_KEY', '')

        # Google
        keys['google'] = os.getenv('GOOGLE_API_KEY', '')

        # DeepSeek
        keys['deepseek'] = os.getenv('DEEPSEEK_API_KEY', '')

        # Local Ollama (no API key needed)
        keys['ollama'] = 'local'

        return keys

    def _is_ollama_running(self) -> bool:
        """Quick check to see if Ollama daemon is reachable"""
        try:
            import requests
            r = requests.get("http://localhost:11434/api/tags", timeout=0.8)
            return r.status_code == 200
        except Exception:
            return False

    def set_model(self, model_name: str) -> bool:
        """Set the current model"""
        if model_name in self.SUPPORTED_MODELS:
            self.current_model = model_name
            return True
        return False

    def get_available_models(self) -> List[str]:
        """Get list of available models based on API keys and runtime availability"""
        available = []
        ollama_ok = self._is_ollama_running()
        for model, config in self.SUPPORTED_MODELS.items():
            provider = config['provider']
            if provider == 'ollama':
                if ollama_ok:
                    available.append(model)
            else:
                if self.api_keys.get(provider):
                    available.append(model)
        return available

    def call_model(self, messages: List[Dict[str, str]], model: str = None, **kwargs) -> str:
        """Call the specified model with messages"""
        if model is None:
            model = self.current_model

        if model not in self.SUPPORTED_MODELS:
            raise ValueError(f"Unsupported model: {model}")

        config = self.SUPPORTED_MODELS[model]
        provider = config['provider']

        if not self.api_keys.get(provider) and provider != 'ollama':
            raise ValueError(f"API key not set for {provider}. Please set {provider.upper()}_API_KEY environment variable.")

        try:
            if provider == 'openai':
                return self._call_openai(messages, config, **kwargs)
            elif provider == 'anthropic':
                return self._call_anthropic(messages, config, **kwargs)
            elif provider == 'google':
                return self._call_google(messages, config, **kwargs)
            elif provider == 'deepseek':
                return self._call_deepseek(messages, config, **kwargs)
            elif provider == 'ollama':
                return self._call_ollama(messages, config, **kwargs)
            else:
                raise ValueError(f"No implementation for provider: {provider}")
        except Exception as e:
            raise Exception(f"Model call failed for {model}: {str(e)}")

    def _call_openai(self, messages: List[Dict[str, str]], config: Dict, **kwargs) -> str:
        """Call OpenAI models"""
        try:
            import openai
            client = openai.OpenAI(api_key=self.api_keys['openai'])
            model_name = config['name']

            response = client.chat.completions.create(
                model=model_name,
                messages=messages,
                max_tokens=kwargs.get('max_tokens', 4096),
                temperature=kwargs.get('temperature', 0.7)
            )
            return response.choices[0].message.content
        except ImportError:
            raise ImportError("OpenAI package not installed. Install with: pip install openai")

    def _call_anthropic(self, messages: List[Dict[str, str]], config: Dict, **kwargs) -> str:
        """Call Anthropic Claude models"""
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.api_keys['anthropic'])
            model_name = config['name']

            response = client.messages.create(
                model=model_name,
                max_tokens=kwargs.get('max_tokens', 4096),
                temperature=kwargs.get('temperature', 0.7),
                messages=messages
            )
            return response.content[0].text
        except ImportError:
            raise ImportError("Anthropic package not installed. Install with: pip install anthropic")

    def _call_google(self, messages: List[Dict[str, str]], config: Dict, **kwargs) -> str:
        """Call Google Gemini models"""
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_keys['google'])
            model = genai.GenerativeModel(config['name'])

            # Convert messages to Gemini format
            prompt = ""
            for msg in messages:
                if msg['role'] == 'system':
                    prompt += f"System: {msg['content']}\n"
                elif msg['role'] == 'user':
                    prompt += f"User: {msg['content']}\n"
                elif msg['role'] == 'assistant':
                    prompt += f"Assistant: {msg['content']}\n"

            response = model.generate_content(prompt)
            return response.text
        except ImportError:
            raise ImportError("Google Generative AI package not installed. Install with: pip install google-generativeai")

    def _call_deepseek(self, messages: List[Dict[str, str]], config: Dict, **kwargs) -> str:
        """Call DeepSeek models"""
        import requests

        # DeepSeek typically uses OpenAI-compatible API
        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_keys['deepseek']}",
            "Content-Type": "application/json"
        }

        data = {
            "model": config['name'],
            "messages": messages,
            "max_tokens": kwargs.get('max_tokens', 4096),
            "temperature": kwargs.get('temperature', 0.7)
        }

        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            raise Exception(f"DeepSeek API error: {response.text}")

    def _call_ollama(self, messages: List[Dict[str, str]], config: Dict, **kwargs) -> str:
        """Call local Ollama models"""
        import requests

        url = "http://localhost:11434/api/chat"

        # Convert messages to Ollama format
        ollama_messages = []
        for msg in messages:
            if msg['role'] == 'system':
                ollama_messages.append({"role": "system", "content": msg['content']})
            elif msg['role'] in ['user', 'assistant']:
                ollama_messages.append({"role": msg['role'], "content": msg['content']})

        data = {
            "model": config['name'],
            "messages": ollama_messages,
            "stream": False
        }

        response = requests.post(url, json=data)
        if response.status_code == 200:
            result = response.json()
            return result['message']['content']
        else:
            raise Exception(f"Ollama API error: {response.text}")

# Initialize global AI model manager
ai_manager = AIModelManager()

Base = declarative_base()

class Protocol(Base):
    __tablename__ = 'protocols'

    id = Column(Integer, primary_key=True)
    title = Column(String(500), nullable=False)
    research_question = Column(Text)
    pico_population = Column(Text)
    pico_intervention = Column(Text)
    pico_comparison = Column(Text)
    pico_outcome = Column(Text)
    inclusion_criteria = Column(Text)
    exclusion_criteria = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    studies = relationship("Study", back_populates="protocol")
    meta_analyses = relationship("MetaAnalysis", back_populates="protocol")

class Study(Base):
    __tablename__ = 'studies'

    id = Column(Integer, primary_key=True)
    protocol_id = Column(Integer, ForeignKey('protocols.id'))
    title = Column(String(1000))
    authors = Column(String(500))
    journal = Column(String(200))
    year = Column(Integer)
    doi = Column(String(100))
    abstract = Column(Text)
    full_text_path = Column(String(500))  # Path to PDF
    inclusion_status = Column(String(50))  # included, excluded, pending
    exclusion_reason = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    protocol = relationship("Protocol", back_populates="studies")
    data_extractions = relationship("DataExtraction", back_populates="study")
    quality_assessments = relationship("QualityAssessment", back_populates="study")

class DataExtraction(Base):
    __tablename__ = 'data_extractions'

    id = Column(Integer, primary_key=True)
    study_id = Column(Integer, ForeignKey('studies.id'))
    outcome_name = Column(String(200))
    outcome_type = Column(String(50))  # continuous, dichotomous, etc.
    intervention_n = Column(Integer)
    intervention_mean = Column(Float)
    intervention_sd = Column(Float)
    intervention_events = Column(Integer)
    control_n = Column(Integer)
    control_mean = Column(Float)
    control_sd = Column(Float)
    control_events = Column(Integer)
    effect_size = Column(Float)
    confidence_interval_low = Column(Float)
    confidence_interval_high = Column(Float)
    extracted_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    study = relationship("Study", back_populates="data_extractions")

class QualityAssessment(Base):
    __tablename__ = 'quality_assessments'

    id = Column(Integer, primary_key=True)
    study_id = Column(Integer, ForeignKey('studies.id'))
    tool_name = Column(String(50))  # NOS, ROB2, AXIS
    overall_score = Column(Float)
    risk_of_bias = Column(String(50))  # low, high, unclear
    details = Column(JSON)  # Store detailed assessment
    assessed_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    study = relationship("Study", back_populates="quality_assessments")

class MetaAnalysis(Base):
    __tablename__ = 'meta_analyses'

    id = Column(Integer, primary_key=True)
    protocol_id = Column(Integer, ForeignKey('protocols.id'))
    outcome_name = Column(String(200))
    model_type = Column(String(50))  # fixed, random
    effect_size = Column(Float)
    confidence_interval_low = Column(Float)
    confidence_interval_high = Column(Float)
    heterogeneity_i2 = Column(Float)
    p_value = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    protocol = relationship("Protocol", back_populates="meta_analyses")

# Create engine
engine = create_engine('sqlite:///systematic_review.db', echo=False)

# Create tables
def create_tables():
    Base.metadata.create_all(engine)

if __name__ == "__main__":
    create_tables()
