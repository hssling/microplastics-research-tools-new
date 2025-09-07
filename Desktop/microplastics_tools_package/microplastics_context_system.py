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


def main():
    """Main function to create the context system"""
    # Citation data from the provided document
    citations = [
        "Abimbola I, McAfee M, Creedon L, Gharbia S. In-situ detection of microplastics in the aquatic environment: A systematic literature review. Sci Total Environ. 2024;934:173111.",
        "Aguilar-Aguilar A, de León-Martínez LD, Forgionny A, Acelas Soto NY, Mendoza SR, Zárate-Guzmán AI. A systematic review on the current situation of emerging pollutants in Mexico: A perspective on policies, regulation, detection, and elimination in water and wastewater. Sci Total Environ. 2023;905:167426.",
        "Ahmet Miraç B, Fatoş U. The effect of environmental health education on microplastic pollution awareness. Public Health Nurs. 2024;41(4):760-7.",
        "Ali-Hassanzadeh M, Arefinia N, Ghoreshi ZA, Askarpour H, Mashayekhi-Sardoo H. The effects of exposure to microplastics on female reproductive health and pregnancy outcomes: A systematic review and meta-analysis. Reprod Toxicol. 2025;135:108932.",
        "An Q, Wen C, Yan C. Meta-analysis reveals the combined effects of microplastics and heavy metal on plants. J Hazard Mater. 2024;476:135028.",
        "Anene DI, Beltran M, Tjahjono B, Schultz A, McKenzie M, Stevanovic S, et al. Microplastics and chemical additives from disposable face masks: Environmental, human health and behavioural impacts. Sci Total Environ. 2025;973:179079.",
        "Antohi VM, Ionescu RV, Zlati ML, Iticescu C, Georgescu PL, Calmuc M. Regional Regression Correlation Model of Microplastic Water Pollution Control Using Circular Economy Tools. Int J Environ Res Public Health. 2023;20(5).",
        "Araújo AM, Mota C, Ramos H, Faria MA, Carvalho M, Ferreira I. The neurotoxic threat of micro- and nanoplastics: evidence from In Vitro and In Vivo models. Arch Toxicol. 2025;99(9):3505-25.",
        "Arbabi A, Gholami M, Farzadkia M, Djalalinia S. Microplastics removal technologies from aqueous environments: a systematic review. J Environ Health Sci Eng. 2023;21(2):463-73.",
        "Arpia AA, Chen WH, Ubando AT, Naqvi SR, Culaba AB. Microplastic degradation as a sustainable concurrent approach for producing biofuel and obliterating hazardous environmental effects: A state-of-the-art review. J Hazard Mater. 2021;418:126381.",
        "Ateia M, Ersan G, Alalm MG, Boffito DC, Karanfil T. Emerging investigator series: microplastic sources, fate, toxicity, detection, and interactions with micropollutants in aquatic ecosystems - a review of reviews. Environ Sci Process Impacts. 2022;24(2):172-95.",
        "Azeem I, Shakoor N, Chaudhary S, Adeel M, Zain M, Ahmad MA, et al. Analytical challenges in detecting microplastics and nanoplastics in soil-plant systems. Plant Physiol Biochem. 2023;204:108132.",
        "Barhoumi B, Sander SG, Tolosa I. A review on per- and polyfluorinated alkyl substances (PFASs) in microplastic and food-contact materials. Environ Res. 2022;206:112595.",
        "Baspakova A, Zare A, Suleimenova R, Berdygaliev AB, Karimsakova B, Tussupkaliyeva K, et al. An updated systematic review about various effects of microplastics on cancer: A pharmacological and in-silico based analysis. Mol Aspects Med. 2025;101:101336.",
        "Baysal A, Saygin H. Co-occurence of antibiotics and micro(nano)plastics: a systematic review between 2016-2021. J Environ Sci Health A Tox Hazard Subst Environ Eng. 2022;57(7):519-39.",
        "Berlino M, Mangano MC, De Vittor C, Sarà G. Effects of microplastics on the functional traits of aquatic benthic organisms: A global-scale meta-analysis. Environ Pollut. 2021;285:117174.",
        "Bhuyan MS, Jenzri M, Pandit D, Adikari D, Alam MW, Kunda M. Microplastics occurrence in sea cucumbers and impacts on sea cucumbers & human health: A systematic review. Sci Total Environ. 2024;951:175792.",
        "Cai T, Boeri L, Miacola C, Palumbo F, Albo G, Ditonno P, et al. Can nutraceuticals counteract the detrimental effects of the environment on male fertility? A parallel systematic review and expert opinion. Minerva Endocrinol (Torino). 2025;50(1):84-96.",
        "Camerano Spelta Rapini C, Di Berardino C, Peserico A, Capacchietti G, Barboni B. Can Mammalian Reproductive Health Withstand Massive Exposure to Polystyrene Micro- and Nanoplastic Derivatives? A Systematic Review. Int J Mol Sci. 2024;25(22).",
        "Caminiti C, Diodati F, Puntoni M, Balan D, Maglietta G. Surveys of Knowledge and Awareness of Plastic Pollution and Risk Reduction Behavior in the General Population: A Systematic Review. Int J Environ Res Public Health. 2025;22(2).",
        "Cao ND, Vo DT, Pham MD, Nguyen VT, Nguyen TB, Le LT, et al. Microplastics contamination in water supply system and treatment processes. Sci Total Environ. 2024;926:171793.",
        "Chand N, Krause S, Prajapati SK. The potential of microplastics acting as vector for triclosan in aquatic environments. Aquat Toxicol. 2025;284:107381.",
        "Chartres N, Cooper CB, Bland G, Pelch KE, Gandhi SA, BakenRa A, et al. Effects of Microplastic Exposure on Human Digestive, Reproductive, and Respiratory Health: A Rapid Systematic Review. Environ Sci Technol. 2024;58(52):22843-64.",
        "Chen J, Qi R, Cheng Y, Wang L, Cao X. Effects of micro/nanoplastics on oxidative damage and serum biochemical parameters in rats and mice: a meta-analysis. Environ Geochem Health. 2024;46(6):197.",
        "Chen L, Zhou S, Zhang Q, Su B, Yin Q, Zou M. Global occurrence characteristics, drivers, and environmental risk assessment of microplastics in lakes: A meta-analysis. Environ Pollut. 2024;344:123321.",
        "Chengappa SK, Rao A, K SA, Jodalli PS, Shenoy Kudpi R. Microplastic content of over-the-counter toothpastes - a systematic review. F1000Res. 2023;12:390.",
        "Cho YM, Choi KH. The current status of studies of human exposure assessment of microplastics and their health effects: a rapid systematic review. Environ Anal Health Toxicol. 2021;36(1):e2021004-0.",
        "Clance LR, Ziegler SL, Fodrie FJ. Contaminants disrupt aquatic food webs via decreased consumer efficiency. Sci Total Environ. 2023;859(Pt 2):160245.",
        "Clérigo F, Ferreira S, Ladeira C, Marques-Ramos A, Almeida-Silva M, Mendes LA. Cytotoxicity Assessment of Nanoplastics and Plasticizers Exposure in In Vitro Lung Cell Culture Systems-A Systematic Review. Toxics. 2022;10(7).",
        "Cristaldi A, Fiore M, Zuccarello P, Oliveri Conti G, Grasso A, Nicolosi I, et al. Efficiency of Wastewater Treatment Plants (WWTPs) for Microplastic Removal: A Systematic Review. Int J Environ Res Public Health. 2020;17(21).",
        "da Silva MRF, Souza KS, Motteran F, de Araújo LCA, Singh R, Bhadouria R, et al. Exploring biodegradative efficiency: a systematic review on the main microplastic-degrading bacteria. Front Microbiol. 2024;15:1360844.",
        "Danopoulos E, Jenner LC, Twiddy M, Rotchell JM. Microplastic Contamination of Seafood Intended for Human Consumption: A Systematic Review and Meta-Analysis. Environ Health Perspect. 2020;128(12):126002.",
        "Dasmahapatra AK, Chatterjee J, Tchounwou PB. A systematic review of the effects of nanoplastics on fish. Front Toxicol. 2025;7:1530209.",
        "De Stefano AA, Horodynski M, Galluccio G. Can Clear Aligners Release Microplastics That Impact the Patient's Overall Health? A Systematic Review. Materials (Basel). 2025;18(11).",
        "Díaz-Fuster L, Sáez-Espinosa P, Moya I, Peinado I, Gómez-Torres MJ. Updating the Role of JUNO and Factors Involved in Its Function during Fertilization. Cells Tissues Organs. 2025:1-16.",
        "Dorairajan G, Ravi S, Chinnakili P. The Effect of Preinduction Cervical Ripening With Synthetic Hygroscopic Dilators on Maternal Outcomes of Women With Previous Caesarean Pregnancy: A Single-Group Clinical Trial. J Pregnancy. 2024;2024:8835464.",
        "Doshi M, Rabari V, Patel A, Yadav VK, Sahoo DK, Trivedi J. A systematic review on microplastic contamination in marine Crustacea and Mollusca of Asia: Current scenario, concentration, characterization, polymeric risk assessment, and future Prospectives. Water Environ Res. 2024;96(5):e11029.",
        "Du Z, Yu X, Li X, Zhang L, Lin Y, He Y, et al. Mechanism of microplastics in respiratory disease from 2020 to 2024: visualization and bibliometric analysis. Front Med (Lausanne). 2025;12:1586772.",
        "Eberhard T, Casillas G, Zarus GM, Barr DB. Systematic review of microplastics and nanoplastics in indoor and outdoor air: identifying a framework and data needs for quantifying human inhalation exposures. J Expo Sci Environ Epidemiol. 2024;34(2):185-96.",
        "Egbuna C, Amadi CN, Patrick-Iwuanyanwu KC, Ezzat SM, Awuchi CG, Ugonwa PO, et al. Emerging pollutants in Nigeria: A systematic review. Environ Toxicol Pharmacol. 2021;85:103638.",
        "Fehrenbach GW, Murphy E, Tanoeiro JR, Pogue R, Major I. Monitoring water contamination through shellfish: A systematic review of biomarkers, species selection, and host response. Ecotoxicol Environ Saf. 2025;295:118120.",
        "Feng Q, An C, Chen Z, Lee K, Wang Z. Identification of the driving factors of microplastic load and morphology in estuaries for improving monitoring and management strategies: A global meta-analysis. Environ Pollut. 2023;333:122014.",
        "Feng Y, Tu C, Li R, Wu D, Yang J, Xia Y, et al. A systematic review of the impacts of exposure to micro- and nano-plastics on human tissue accumulation and health. Eco Environ Health. 2023;2(4):195-207.",
        "Feng Y, Tu C, Li R, Wu D, Yang J, Xia Y, et al. Corrigendum to \"A systematic review of the impacts of exposure to micro- and nano-plastics on human tissue accumulation and health\" [Eco-Environ. Health (2023)195-207]. Eco Environ Health. 2025;4(1):100137.",
        "Ferreira ROG, Nag R, Gowen A, Xu JL. Deciphering the cytotoxicity of micro- and nanoplastics in Caco-2 cells through meta-analysis and machine learning. Environ Pollut. 2024;362:124971.",
        "Gautam K, Pandey N, Yadav D, Parthasarathi R, Turner A, Anbumani S, et al. Ecotoxicological impacts of landfill sites: Towards risk assessment, mitigation policies and the role of artificial intelligence. Sci Total Environ. 2024;927:171804.",
        "Ge Y, Yang S, Zhang T, Wan X, Zhu Y, Yang F, et al. The hepatotoxicity assessment of micro/nanoplastics: A preliminary study to apply the adverse outcome pathways. Sci Total Environ. 2023;902:165659.",
        "Gopinath PM, Parvathi VD, Yoghalakshmi N, Kumar SM, Athulya PA, Mukherjee A, et al. Plastic particles in medicine: A systematic review of exposure and effects to human health. Chemosphere. 2022;303(Pt 3):135227.",
        "Gurumoorthi K, Luis AJ. Recent trends on microplastics abundance and risk assessment in coastal Antarctica: Regional meta-analysis. Environ Pollut. 2023;324:121385.",
        "Heo SJ, Moon N, Kim JH. A systematic review and quality assessment of estimated daily intake of microplastics through food. Rev Environ Health. 2025;40(2):371-92.",
        "Huang F, Hu J, Chen L, Wang Z, Sun S, Zhang W, et al. Microplastics may increase the environmental risks of Cd via promoting Cd uptake by plants: A meta-analysis.