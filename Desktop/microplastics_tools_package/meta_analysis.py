import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple
import statsmodels.api as sm
from statsmodels.stats.meta_analysis import (
    combine_effects, 
    effectsize_smd, 
    effectsize_2proportions
)
import scipy.stats as stats
from datetime import datetime

class MetaAnalysisModule:
    def __init__(self):
        pass

    def perform_meta_analysis(self, extracted_data: List[Dict[str, Any]], 
                            outcome_name: str, model_type: str = "random") -> Dict[str, Any]:
        """
        Perform meta-analysis on extracted data
        """
        # Filter data for the specific outcome
        outcome_data = self._filter_outcome_data(extracted_data, outcome_name)
        
        if not outcome_data:
            return {"error": f"No data found for outcome: {outcome_name}"}

        # Determine outcome type and perform appropriate analysis
        outcome_type = self._determine_outcome_type(outcome_data)
        
        if outcome_type == "continuous":
            return self._meta_analysis_continuous(outcome_data, model_type)
        elif outcome_type == "dichotomous":
            return self._meta_analysis_dichotomous(outcome_data, model_type)
        else:
            return {"error": "Unable to determine outcome type"}

    def _filter_outcome_data(self, extracted_data: List[Dict[str, Any]], 
                           outcome_name: str) -> List[Dict[str, Any]]:
        """
        Filter extracted data for specific outcome
        """
        filtered_data = []
        
        for item in extracted_data:
            if 'extracted_data' in item:
                data = item['extracted_data']
                if isinstance(data, dict) and outcome_name in str(data):
                    # Check if this study has data for the outcome
                    study_data = {
                        'study_id': item.get('article_id', ''),
                        'outcome_data': data
                    }
                    filtered_data.append(study_data)
        
        return filtered_data

    def _determine_outcome_type(self, outcome_data: List[Dict[str, Any]]) -> str:
        """
        Determine if outcome is continuous or dichotomous
        """
        # Check for continuous data indicators
        continuous_indicators = ['mean', 'sd', 'std', 'median', 'iqr']
        dichotomous_indicators = ['events', 'n', 'proportion', 'odds']
        
        for study in outcome_data:
            data = study.get('outcome_data', {})
            data_str = str(data).lower()
            
            if any(indicator in data_str for indicator in continuous_indicators):
                return "continuous"
            elif any(indicator in data_str for indicator in dichotomous_indicators):
                return "dichotomous"
        
        return "unknown"

    def _meta_analysis_continuous(self, outcome_data: List[Dict[str, Any]], 
                                model_type: str) -> Dict[str, Any]:
        """
        Perform meta-analysis for continuous outcomes
        """
        effect_sizes = []
        variances = []
        study_labels = []
        
        for study in outcome_data:
            data = study.get('outcome_data', {})
            
            # Extract means and SDs
            try:
                intervention_mean = data.get('intervention_mean')
                control_mean = data.get('control_mean')
                intervention_sd = data.get('intervention_sd')
                control_sd = data.get('control_sd')
                intervention_n = data.get('intervention_n')
                control_n = data.get('control_n')
                
                if all([intervention_mean, control_mean, intervention_sd, 
                       control_sd, intervention_n, control_n]):
                    
                    # Calculate standardized mean difference
                    smd = (intervention_mean - control_mean) / np.sqrt(
                        ((intervention_n - 1) * intervention_sd**2 + 
                         (control_n - 1) * control_sd**2) / 
                        (intervention_n + control_n - 2)
                    )
                    
                    # Calculate variance
                    se = np.sqrt(1/intervention_n + 1/control_n)
                    variance = se**2
                    
                    effect_sizes.append(smd)
                    variances.append(variance)
                    study_labels.append(study.get('study_id', 'Unknown'))
                    
            except (TypeError, ValueError) as e:
                print(f"Error processing study {study.get('study_id')}: {e}")
                continue
        
        if not effect_sizes:
            return {"error": "No valid continuous data for meta-analysis"}
        
        return self._run_meta_analysis(effect_sizes, variances, study_labels, model_type)

    def _meta_analysis_dichotomous(self, outcome_data: List[Dict[str, Any]], 
                                 model_type: str) -> Dict[str, Any]:
        """
        Perform meta-analysis for dichotomous outcomes
        """
        effect_sizes = []
        variances = []
        study_labels = []
        
        for study in outcome_data:
            data = study.get('outcome_data', {})
            
            try:
                intervention_events = data.get('intervention_events')
                control_events = data.get('control_events')
                intervention_n = data.get('intervention_n')
                control_n = data.get('control_n')
                
                if all([intervention_events, control_events, intervention_n, control_n]):
                    
                    # Calculate log odds ratio
                    intervention_prop = intervention_events / intervention_n
                    control_prop = control_events / control_n
                    
                    # Add continuity correction if needed
                    if intervention_prop in [0, 1] or control_prop in [0, 1]:
                        intervention_prop = (intervention_events + 0.5) / (intervention_n + 1)
                        control_prop = (control_events + 0.5) / (control_n + 1)
                    
                    lor = np.log(intervention_prop / (1 - intervention_prop)) - \
                          np.log(control_prop / (1 - control_prop))
                    
                    # Calculate variance
                    se = np.sqrt(1/intervention_events + 1/(intervention_n - intervention_events) + 
                               1/control_events + 1/(control_n - control_events))
                    variance = se**2
                    
                    effect_sizes.append(lor)
                    variances.append(variance)
                    study_labels.append(study.get('study_id', 'Unknown'))
                    
            except (TypeError, ValueError, ZeroDivisionError) as e:
                print(f"Error processing study {study.get('study_id')}: {e}")
                continue
        
        if not effect_sizes:
            return {"error": "No valid dichotomous data for meta-analysis"}
        
        return self._run_meta_analysis(effect_sizes, variances, study_labels, model_type)

    def _run_meta_analysis(self, effect_sizes: List[float], variances: List[float], 
                         study_labels: List[str], model_type: str) -> Dict[str, Any]:
        """
        Run the actual meta-analysis calculation
        """
        try:
            # Convert to numpy arrays
            yi = np.array(effect_sizes)
            vi = np.array(variances)
            
            if model_type.lower() == "fixed":
                # Fixed effects model
                weights = 1 / vi
                weighted_sum = np.sum(weights * yi)
                total_weight = np.sum(weights)
                
                pooled_effect = weighted_sum / total_weight
                se = np.sqrt(1 / total_weight)
                
                # Calculate confidence intervals
                z_critical = stats.norm.ppf(0.975)
                ci_lower = pooled_effect - z_critical * se
                ci_upper = pooled_effect + z_critical * se
                
                # Q statistic for heterogeneity
                q_stat = np.sum(weights * (yi - pooled_effect)**2)
                df = len(yi) - 1
                p_value = 1 - stats.chi2.cdf(q_stat, df)
                
                i2 = max(0, (q_stat - df) / q_stat * 100) if q_stat > df else 0
                
            else:  # Random effects model
                # Use DerSimonian-Laird method
                weights = 1 / vi
                weighted_mean = np.sum(weights * yi) / np.sum(weights)
                
                # Estimate tau^2
                q_stat = np.sum(weights * (yi - weighted_mean)**2)
                df = len(yi) - 1
                
                c = np.sum(weights) - np.sum(weights**2) / np.sum(weights)
                tau2 = max(0, (q_stat - df) / c) if c > 0 else 0
                
                # Random effects weights
                random_weights = 1 / (vi + tau2)
                total_weight = np.sum(random_weights)
                
                pooled_effect = np.sum(random_weights * yi) / total_weight
                se = np.sqrt(1 / total_weight)
                
                # Confidence intervals
                z_critical = stats.norm.ppf(0.975)
                ci_lower = pooled_effect - z_critical * se
                ci_upper = pooled_effect + z_critical * se
                
                # Heterogeneity
                i2 = max(0, (q_stat - df) / q_stat * 100) if q_stat > df else 0
                p_value = 1 - stats.chi2.cdf(q_stat, df)
            
            # Calculate p-value for effect
            z_stat = pooled_effect / se
            effect_p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))
            
            result = {
                "outcome": "Unknown",  # Would be passed from caller
                "model_type": model_type,
                "num_studies": len(effect_sizes),
                "pooled_effect": float(pooled_effect),
                "standard_error": float(se),
                "confidence_interval_lower": float(ci_lower),
                "confidence_interval_upper": float(ci_upper),
                "z_statistic": float(z_stat),
                "p_value": float(effect_p_value),
                "heterogeneity_i2": float(i2),
                "heterogeneity_q": float(q_stat) if 'q_stat' in locals() else 0,
                "heterogeneity_p": float(p_value) if 'p_value' in locals() else 1.0,
                "study_effects": [
                    {
                        "study": label,
                        "effect_size": float(es),
                        "variance": float(var)
                    } for label, es, var in zip(study_labels, effect_sizes, variances)
                ],
                "analysis_date": datetime.utcnow().isoformat()
            }
            
            return result
            
        except Exception as e:
            return {"error": f"Meta-analysis calculation failed: {str(e)}"}

    def create_forest_plot_data(self, meta_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare data for forest plot visualization
        """
        if "error" in meta_result:
            return {"error": meta_result["error"]}
        
        studies = meta_result.get("study_effects", [])
        
        plot_data = {
            "studies": [],
            "pooled_effect": meta_result.get("pooled_effect", 0),
            "ci_lower": meta_result.get("confidence_interval_lower", 0),
            "ci_upper": meta_result.get("confidence_interval_upper", 0)
        }
        
        for study in studies:
            plot_data["studies"].append({
                "label": study["study"][:20] + "..." if len(study["study"]) > 20 else study["study"],
                "effect": study["effect_size"],
                "ci_lower": study["effect_size"] - 1.96 * np.sqrt(study["variance"]),
                "ci_upper": study["effect_size"] + 1.96 * np.sqrt(study["variance"])
            })
        
        return plot_data

    def perform_subgroup_analysis(self, extracted_data: List[Dict[str, Any]], 
                                outcome_name: str, subgroup_variable: str) -> Dict[str, Any]:
        """
        Perform subgroup analysis
        """
        # This would require extracting subgroup information from the data
        # Implementation depends on how subgroup data is stored
        return {"error": "Subgroup analysis not yet implemented"}

    def assess_publication_bias(self, meta_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess publication bias using funnel plot asymmetry tests
        """
        if "error" in meta_result:
            return {"error": meta_result["error"]}
        
        studies = meta_result.get("study_effects", [])
        
        if len(studies) < 10:
            return {"warning": "Fewer than 10 studies - publication bias tests unreliable"}
        
        # Egger's test (simplified)
        effect_sizes = [s["effect_size"] for s in studies]
        standard_errors = [np.sqrt(s["variance"]) for s in studies]
        
        # Regress effect size on precision (1/SE)
        X = np.array([1/se for se in standard_errors])
        y = np.array(effect_sizes)
        
        try:
            X = sm.add_constant(X)
            model = sm.OLS(y, X).fit()
            
            egger_p = model.pvalues[1] if len(model.pvalues) > 1 else 1.0
            
            return {
                "eggers_test_p": float(egger_p),
                "publication_bias_likely": egger_p < 0.1,
                "interpretation": "Significant Egger's test suggests publication bias" if egger_p < 0.1 else "No significant publication bias detected"
            }
            
        except Exception as e:
            return {"error": f"Publication bias assessment failed: {str(e)}"}

    def export_meta_results(self, meta_result: Dict[str, Any], filename: str):
        """
        Export meta-analysis results to file
        """
        if "error" in meta_result:
            with open(filename, 'w') as f:
                f.write(f"Error: {meta_result['error']}")
            return
        
        with open(filename, 'w') as f:
            f.write("Meta-Analysis Results\n")
            f.write("=" * 50 + "\n\n")
            
            f.write(f"Number of studies: {meta_result.get('num_studies', 0)}\n")
            f.write(f"Model type: {meta_result.get('model_type', 'Unknown')}\n")
            f.write(f"Pooled effect: {meta_result.get('pooled_effect', 0):.3f}\n")
            f.write(f"95% CI: [{meta_result.get('confidence_interval_lower', 0):.3f}, {meta_result.get('confidence_interval_upper', 0):.3f}]\n")
            f.write(f"P-value: {meta_result.get('p_value', 1.0):.3f}\n")
            f.write(f"I²: {meta_result.get('heterogeneity_i2', 0):.1f}%\n")
            
            f.write("\nStudy-level results:\n")
            for study in meta_result.get("study_effects", []):
                f.write(f"  {study['study']}: {study['effect_size']:.3f}\n")
