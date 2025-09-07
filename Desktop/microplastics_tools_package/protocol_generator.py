import openai
from typing import Dict, Any
import json
from datetime import datetime

class ProtocolGenerator:
    def __init__(self, api_key: str, ai_manager=None):
        self.api_key = api_key
        self.ai_manager = ai_manager
        # Initialize OpenAI client if key provided
        if api_key and api_key != "free-model-nokey-required":
            self.client = openai.OpenAI(api_key=api_key)
        else:
            self.client = None

    def generate_protocol(self, research_question: str, pico: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Generate a systematic review protocol using AI
        """
        prompt = f"""
        Generate a comprehensive systematic review protocol for the following research question:
        {research_question}

        {"PICO framework details:" + json.dumps(pico) if pico else ""}

        Please provide a protocol that includes:
        1. Background and rationale
        2. Objectives
        3. Eligibility criteria (inclusion/exclusion)
        4. Search strategy
        5. Study selection process
        6. Data extraction methods
        7. Risk of bias assessment
        8. Data synthesis plan
        9. Dissemination plan

        Format the response as JSON with keys like background, objectives, inclusion_criteria, etc.
        """

        # Try OpenAI first if available with a real API key
        if self.client and self.api_key and self.api_key != "free-model-nokey-required":
            return self._generate_with_openai(prompt, research_question, pico)

        # Skip to Ollama fallback directly for free models
        print("No OpenAI key provided, attempting Ollama fallback...")
        return self._generate_with_ollama(prompt, research_question, pico)

    def _structure_protocol_text(self, text: str) -> Dict[str, Any]:
        """
        Structure plain text protocol into organized format
        """
        # Simple parsing - in a real implementation, this would be more sophisticated
        sections = text.split('\n\n')
        protocol = {}

        for section in sections:
            if 'background' in section.lower() or 'rationale' in section.lower():
                protocol['background'] = section
            elif 'objectives' in section.lower():
                protocol['objectives'] = section
            elif 'eligibility' in section.lower() or 'criteria' in section.lower():
                protocol['eligibility_criteria'] = section
            elif 'search' in section.lower():
                protocol['search_strategy'] = section
            elif 'selection' in section.lower():
                protocol['study_selection'] = section
            elif 'extraction' in section.lower():
                protocol['data_extraction'] = section
            elif 'bias' in section.lower() or 'risk' in section.lower():
                protocol['risk_assessment'] = section
            elif 'synthesis' in section.lower():
                protocol['data_synthesis'] = section
            elif 'dissemination' in section.lower():
                protocol['dissemination'] = section

        return protocol

    def _generate_with_openai(self, prompt: str, research_question: str, pico: Dict[str, str] = None) -> Dict[str, Any]:
        """Generate protocol using OpenAI"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert in systematic review methodology. Generate detailed, methodologically sound protocols."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.7
            )

            # Check if response has the expected structure
            if response and response.choices and len(response.choices) > 0:
                if hasattr(response.choices[0], 'message') and response.choices[0].message:
                    if hasattr(response.choices[0].message, 'content') and response.choices[0].message.content:
                        protocol_text = response.choices[0].message.content
                    else:
                        protocol_text = "{}"  # Empty JSON fallback
                else:
                    protocol_text = "{}"  # Empty JSON fallback
            else:
                protocol_text = "{}"  # Empty JSON fallback

            # Parse the JSON response
            try:
                protocol_data = json.loads(protocol_text)
            except json.JSONDecodeError:
                # If not valid JSON, structure it manually
                protocol_data = self._structure_protocol_text(protocol_text)

            # Add metadata
            protocol_data.update({
                "research_question": research_question,
                "pico": pico or {},
                "generated_at": datetime.utcnow().isoformat(),
                "version": "1.0"
            })

            return protocol_data

        except Exception as e:
            print(f"OpenAI API error: {str(e)}")
            # Immediately try Ollama fallback
            return self._generate_with_ollama(prompt, research_question, pico)

    def _generate_with_ollama(self, prompt: str, research_question: str, pico: Dict[str, str] = None) -> Dict[str, Any]:
        """Generate protocol using Ollama models"""
        try:
            if not self.ai_manager:
                return {
                    "error": "AI manager not available for fallback",
                    "research_question": research_question,
                    "pico": pico or {},
                    "generated_at": datetime.utcnow().isoformat(),
                    "version": "1.0"
                }

            print("Attempting Ollama fallback...")
            ollama_response = self.ai_manager.call_model(
                messages=[
                    {"role": "system", "content": "You are an expert in systematic review methodology. Generate detailed protocols in JSON format."},
                    {"role": "user", "content": prompt}
                ],
                model="llama-2-7b",
                max_tokens=2000
            )

            if ollama_response:
                try:
                    protocol_data = json.loads(ollama_response)
                except json.JSONDecodeError:
                    protocol_data = self._structure_protocol_text(ollama_response)

                # Add metadata
                protocol_data.update({
                    "research_question": research_question,
                    "pico": pico or {},
                    "generated_at": datetime.utcnow().isoformat(),
                    "version": "1.0",
                    "ai_model": "llama-2-7b"
                })

                return protocol_data
            else:
                # Fall back to deterministic offline template
                return self._generate_basic_fallback(research_question, pico)

        except Exception as e:
            print(f"Ollama fallback failed: {str(e)}")
            # Fall back to deterministic offline template
            return self._generate_basic_fallback(research_question, pico)

    def _generate_basic_fallback(self, research_question: str, pico: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Deterministic offline fallback protocol builder (no external LLMs required)
        """
        pico = pico or {}
        background = (
            f"This protocol addresses the research question: '{research_question}'. "
            "A systematic review will synthesize available evidence using transparent and reproducible methods."
        )
        objectives = (
            "To systematically identify, appraise, and synthesize evidence relevant to the research question, "
            "reporting quantitative or qualitative summaries as appropriate."
        )
        inclusion = (
            f"Studies on the target population: {pico.get('population', 'as defined by the research question')}; "
            f"intervention: {pico.get('intervention', 'relevant interventions')}; "
            f"comparator: {pico.get('comparison', 'appropriate control or usual care')}; "
            f"outcomes: {pico.get('outcome', 'prespecified outcomes of interest')}. "
            "Peer-reviewed human studies; randomized or observational designs; English language; no date restriction unless otherwise specified."
        )
        exclusion = (
            "Animal studies, case reports/series without comparative data, editorials, opinions, conference abstracts without sufficient data, "
            "non-systematic narrative reviews, and studies with irretrievable full-text or insufficient outcome reporting."
        )
        search_strategy = (
            "Databases: PubMed/MEDLINE, Embase, Cochrane Central, and Scopus. "
            "A structured query combining controlled vocabulary and keywords for the population, intervention, comparator, and outcomes will be applied. "
            "Reference lists of included studies will be screened for additional records."
        )
        selection = (
            "Two independent reviewers will screen titles/abstracts, followed by full-text assessment. "
            "Disagreements will be resolved by consensus or a third reviewer. PRISMA flow diagram will document study selection."
        )
        data_extraction = (
            "A standardized form will capture study design, setting, participants, interventions, comparators, outcomes, effect estimates, and risk of bias items. "
            "Extraction will be performed independently by two reviewers."
        )
        risk = (
            "Risk of bias will be assessed with appropriate tools (e.g., Cochrane RoB 2 for RCTs, ROBINS-I for nonrandomized studies, or NOS for observational studies). "
            "Assessments will be conducted independently and reconciled by consensus."
        )
        synthesis = (
            "Where appropriate and sufficiently homogeneous, a meta-analysis will be performed using random-effects models. "
            "Heterogeneity will be quantified using I² statistics. Subgroup and sensitivity analyses will be conducted as feasible. "
            "If meta-analysis is not appropriate, a narrative synthesis will be presented."
        )
        dissemination = (
            "Findings will be reported in accordance with PRISMA guidelines and disseminated through peer-reviewed publication and presentations."
        )

        return {
            "research_question": research_question,
            "pico": {
                "population": pico.get("population", ""),
                "intervention": pico.get("intervention", ""),
                "comparison": pico.get("comparison", ""),
                "outcome": pico.get("outcome", "")
            },
            "background": background,
            "objectives": objectives,
            "inclusion_criteria": inclusion,
            "exclusion_criteria": exclusion,
            "search_strategy": search_strategy,
            "study_selection": selection,
            "data_extraction": data_extraction,
            "risk_assessment": risk,
            "data_synthesis": synthesis,
            "dissemination": dissemination,
            "generated_at": datetime.utcnow().isoformat(),
            "version": "1.0",
            "ai_model": "offline-basic"
        }

    def refine_protocol(self, existing_protocol: Dict[str, Any], feedback: str) -> Dict[str, Any]:
        """
        Refine an existing protocol based on user feedback
        """
        prompt = f"""
        Refine the following systematic review protocol based on this feedback:
        {feedback}

        Original protocol:
        {json.dumps(existing_protocol, indent=2)}

        Provide an updated protocol as JSON.
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert in systematic review methodology. Refine protocols based on feedback while maintaining methodological rigor."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.7
            )

            # Check if response has the expected structure
            if response and response.choices and len(response.choices) > 0:
                if hasattr(response.choices[0], 'message') and response.choices[0].message:
                    if hasattr(response.choices[0].message, 'content') and response.choices[0].message.content:
                        refined_text = response.choices[0].message.content
                    else:
                        refined_text = "{}"  # Empty JSON fallback
                else:
                    refined_text = "{}"  # Empty JSON fallback
            else:
                refined_text = "{}"  # Empty JSON fallback

            try:
                refined_protocol = json.loads(refined_text)
            except json.JSONDecodeError:
                refined_protocol = self._structure_protocol_text(refined_text)

            refined_protocol['refined_at'] = datetime.utcnow().isoformat()
            refined_protocol['version'] = f"{existing_protocol.get('version', '1.0')}.1"

            return refined_protocol

        except Exception as e:
            print(f"OpenAI API error in refine_protocol: {str(e)}")
            return {
                "error": f"Failed to refine protocol: {str(e)}",
                **existing_protocol
            }
