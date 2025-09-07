# app.py
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io
from typing import Dict, Any

st.set_page_config(layout="wide", page_title="TB District Modeller")

# -------------------------
# Model implementation
# -------------------------
def run_expanded_tb(beta: float,
                    years: int = 10,
                    pop: int = 1_000_000,
                    params: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Deterministic expanded TB model (monthly time steps).
    Returns yearly incidence array and compartments time series.
    """
    # defaults
    default = {
        "N": pop,
        "beta": beta,
        "prop_resistant": 0.025,
        "sigma": 0.10,  # annual latent->active base
        "hiv_prevalence": 0.02,
        "hiv_progression_multiplier": 5.0,
        "detection_rate": 0.70,
        "diagnostic_delay_months": 2.0,
        "private_sector_fraction": 0.40,
        "private_notify_frac": 0.50,
        "treatment_initiation_rate": 0.95,
        "treatment_success_s": 0.89,
        "treatment_success_r": 0.87,
        "treatment_duration_months_s": 6,
        "treatment_duration_months_r": 9,
        "relapse_rate": 0.02,
        "natural_death_rate": 0.007,
        "tb_death_rate_s": 0.05,
        "tb_death_rate_r": 0.12,
        "tpt_coverage": 0.05,
        "tpt_efficacy": 0.65,
        "contact_rate_multiplier": 1.0,
        "vaccine_coverage": 0.0,
        "vaccine_efficacy": 0.0,
        "malnut_fraction": 0.20,
        "malnut_multiplier": 1.5,
        "ltfu_rate": 0.05,
        "stockout_frac": 0.0
    }
    if params is None:
        params = default.copy()
    else:
        for k, v in default.items():
            params.setdefault(k, v)
    p = params.copy()
    p["beta"] = beta
    months = int(years * 12)

    # Monthly conversion
    beta_m = p["beta"] / 12.0 * p["contact_rate_multiplier"]
    sigma_m = p["sigma"] / 12.0
    detection_month = 1 - (1 - p["detection_rate"]) ** (1 / 12)
    # account for diagnostic delay by dividing detection by delay factor (simple approx)
    detection_month = detection_month / max(1.0, p["diagnostic_delay_months"])
    tinit_m = 1 - (1 - p["treatment_initiation_rate"]) ** (1 / 12)
    relapse_m = 1 - (1 - p["relapse_rate"]) ** (1 / 12)
    natdeath_m = 1 - (1 - p["natural_death_rate"]) ** (1 / 12)
    tbdeath_s_m = 1 - (1 - p["tb_death_rate_s"]) ** (1 / 12)
    tbdeath_r_m = 1 - (1 - p["tb_death_rate_r"]) ** (1 / 12)

    fail_to_resistant = 0.10

    # Initialization: heuristic using a baseline incidence of 195/100k to set latent pool size,
    # but beta will be calibrated externally when requested.
    incidence_rate_per_year = 195 / 100000
    annual_incidence = incidence_rate_per_year * p["N"]
    L0 = annual_incidence / max(p["sigma"], 1e-9)
    Iu_s0 = max(10.0, annual_incidence / 5.0)
    Iu_r0 = max(1.0, Iu_s0 * p["prop_resistant"] / (1 - p["prop_resistant"]))
    Id_s0 = Iu_s0 * 0.2
    Id_r0 = Iu_r0 * 0.2
    Ts0 = Id_s0 * 0.5
    Tr0 = Id_r0 * 0.5
    R0 = 0.0
    V0 = p["vaccine_coverage"] * p["N"]
    S0 = p["N"] - (L0 + Iu_s0 + Iu_r0 + Id_s0 + Id_r0 + Ts0 + Tr0 + R0 + V0)
    if S0 < 0:
        S0 = max(0.0, p["N"] - (Iu_s0 + Iu_r0 + Id_s0 + Id_r0 + Ts0 + Tr0 + R0 + V0))
        L0 = p["N"] - (S0 + Iu_s0 + Iu_r0 + Id_s0 + Id_r0 + Ts0 + Tr0 + R0 + V0)

    # arrays
    S = np.zeros(months + 1); V = np.zeros(months + 1); L = np.zeros(months + 1)
    Iu_s = np.zeros(months + 1); Id_s = np.zeros(months + 1); Ts = np.zeros(months + 1)
    Iu_r = np.zeros(months + 1); Id_r = np.zeros(months + 1); Tr = np.zeros(months + 1)
    R = np.zeros(months + 1)
    new_cases_month = np.zeros(months + 1)

    S[0] = S0; V[0] = V0; L[0] = L0
    Iu_s[0] = Iu_s0; Iu_r[0] = Iu_r0; Id_s[0] = Id_s0; Id_r[0] = Id_r0
    Ts[0] = Ts0; Tr[0] = Tr0; R[0] = R0

    def effective_success(base_success):
        s = base_success * (1 - p["stockout_frac"]) * (1 - p["ltfu_rate"])
        return max(0.0, min(0.99, s))

    for m in range(months):
        Ncur = (S[m] + V[m] + L[m] + Iu_s[m] + Id_s[m] + Ts[m] +
                Iu_r[m] + Id_r[m] + Tr[m] + R[m]) + 1e-9
        infectious = Iu_s[m] + Id_s[m] + Iu_r[m] + Id_r[m]
        force = beta_m * infectious / Ncur
        effective_S = S[m] + (1 - p["vaccine_efficacy"]) * V[m]

        new_infections = force * effective_S
        new_infections_r = new_infections * p["prop_resistant"]
        new_infections_s = new_infections - new_infections_r

        hiv_frac = p["hiv_prevalence"]
        maln_frac = p["malnut_fraction"]
        sigma_eff_nonhiv = sigma_m * ((1 - maln_frac) + maln_frac * p["malnut_multiplier"])
        sigma_eff_hiv = sigma_m * p["hiv_progression_multiplier"] * ((1 - maln_frac) + maln_frac * p["malnut_multiplier"])
        progressions = sigma_eff_nonhiv * (1 - hiv_frac) * L[m] + sigma_eff_hiv * hiv_frac * L[m]
        prog_r = progressions * p["prop_resistant"]
        prog_s = progressions - prog_r

        detected_s = detection_month * Iu_s[m]
        detected_r = detection_month * Iu_r[m]
        notify_frac = (1 - p["private_sector_fraction"]) + p["private_sector_fraction"] * p["private_notify_frac"]
        notified_s = detected_s * notify_frac
        notified_r = detected_r * notify_frac
        undetected_nonnotified_s = detected_s - notified_s
        undetected_nonnotified_r = detected_r - notified_r

        start_Ts = tinit_m * notified_s
        start_Tr = tinit_m * notified_r

        deaths_Iu_s = tbdeath_s_m * Iu_s[m]
        deaths_Iu_r = tbdeath_r_m * Iu_r[m]
        deaths_Id_s = tbdeath_s_m * Id_s[m]
        deaths_Id_r = tbdeath_r_m * Id_r[m]

        comp_Ts = (1.0 / max(1.0, p["treatment_duration_months_s"])) * Ts[m]
        comp_Tr = (1.0 / max(1.0, p["treatment_duration_months_r"])) * Tr[m]
        succ_Ts = comp_Ts * effective_success(p["treatment_success_s"])
        fail_Ts = comp_Ts - succ_Ts
        succ_Tr = comp_Tr * effective_success(p["treatment_success_r"])
        fail_Tr = comp_Tr - succ_Tr

        new_resistant_from_fail = fail_Ts * fail_to_resistant
        returned_inf_from_fail_s = fail_Ts - new_resistant_from_fail
        returned_inf_from_fail_r = fail_Tr

        relapses = relapse_m * R[m]

        S[m + 1] = S[m] - new_infections - natdeath_m * S[m] + natdeath_m * Ncur * (S[m] / Ncur)
        V[m + 1] = V[m] - (-natdeath_m * V[m] + natdeath_m * Ncur * (V[m] / Ncur))
        L[m + 1] = L[m] + new_infections_s + new_infections_r + relapses - progressions - natdeath_m * L[m]
        Iu_s[m + 1] = Iu_s[m] + prog_s + undetected_nonnotified_s + returned_inf_from_fail_s - detected_s - deaths_Iu_s - natdeath_m * Iu_s[m]
        Iu_r[m + 1] = Iu_r[m] + prog_r + new_resistant_from_fail + undetected_nonnotified_r + returned_inf_from_fail_r - detected_r - deaths_Iu_r - natdeath_m * Iu_r[m]
        Id_s[m + 1] = Id_s[m] + notified_s - start_Ts - deaths_Id_s - natdeath_m * Id_s[m]
        Id_r[m + 1] = Id_r[m] + notified_r - start_Tr - deaths_Id_r - natdeath_m * Id_r[m]
        Ts[m + 1] = Ts[m] + start_Ts - comp_Ts - natdeath_m * Ts[m]
        Tr[m + 1] = Tr[m] + start_Tr - comp_Tr - natdeath_m * Tr[m]
        R[m + 1] = R[m] + succ_Ts + succ_Tr - relapses - natdeath_m * R[m]

        new_cases_month[m + 1] = progressions

        # prevent small negatives
        arrays = [S, V, L, Iu_s, Iu_r, Id_s, Id_r, Ts, Tr, R]
        for arr in arrays:
            if arr[m + 1] < 0:
                arr[m + 1] = 0.0

    incidence_yearly = []
    for y in range(years):
        start = y * 12
        end = start + 12
        annual_new = new_cases_month[start:end + 1].sum()
        incidence_yearly.append(float(annual_new))

    return {
        "incidence_yearly": np.array(incidence_yearly),
        "compartments": {
            "S": S, "V": V, "L": L,
            "Iu_s": Iu_s, "Id_s": Id_s, "Ts": Ts,
            "Iu_r": Iu_r, "Id_r": Id_r, "Tr": Tr,
            "R": R
        },
        "params": p
    }

# -------------------------
# Beta calibration helper
# -------------------------
def calibrate_beta_to_cases(target_cases_per_year: float, pop: int, params: Dict[str, Any] = None,
                            years: int = 1, tol: float = 1.0, beta_low=0.01, beta_high=200.0):
    """
    Calibrate beta so the model's Year-1 incidence (in absolute cases) ~ target_cases_per_year.
    Uses bisection. Returns calibrated beta.
    """
    # bracket check
    f_low = run_expanded_tb(beta_low, years=years, pop=pop, params=params)["incidence_yearly"][0] - target_cases_per_year
    f_high = run_expanded_tb(beta_high, years=years, pop=pop, params=params)["incidence_yearly"][0] - target_cases_per_year
    if f_low * f_high > 0:
        # expand upper bound iteratively
        for factor in [500, 1000]:
            beta_high = beta_high * factor
            f_high = run_expanded_tb(beta_high, years=years, pop=pop, params=params)["incidence_yearly"][0] - target_cases_per_year
            if f_low * f_high <= 0:
                break
        else:
            raise ValueError("Unable to bracket root for beta; try different bounds or check target.")

    for _ in range(40):
        mid = 0.5 * (beta_low + beta_high)
        val = run_expanded_tb(mid, years=years, pop=pop, params=params)["incidence_yearly"][0] - target_cases_per_year
        if abs(val) <= tol:
            return mid
        if val * f_low <= 0:
            beta_high = mid
            f_high = val
        else:
            beta_low = mid
            f_low = val
    return mid

# -------------------------
# Recommendation heuristics
# -------------------------
def generate_recommendations(p: Dict[str, Any], perc5: float, inc1: float, inc5: float) -> list:
    rec = []
    if p.get("detection_rate", 0) < 0.80:
        rec.append("Increase case detection: scale ACF, AI-CXR triage, and private-sector notification.")
    if p.get("tpt_coverage", 0) < 0.30:
        rec.append("Scale up TPT to contacts and high-risk groups (target ≥30% annual coverage).")
    if p.get("treatment_success_s", 0) < 0.90 or p.get("treatment_success_r", 0) < 0.90:
        rec.append("Strengthen treatment support: adherence counselling, rollout of shorter regimens, reduce LTFU.")
    if p.get("private_sector_fraction", 0) > 0.3 and p.get("private_notify_frac", 0) < 0.8:
        rec.append("Engage private sector with e-prescription and mandatory notification incentives.")
    if p.get("malnut_fraction", 0) > 0.2:
        rec.append("Address nutrition: Ni-kshay Poshan or district food support for TB households.")
    if p.get("hiv_prevalence", 0) > 0.05:
        rec.append("Integrate TB/HIV services: routine screening, ART optimisation, and TPT for PLHIV.")
    if p.get("stockout_frac", 0) > 0.05:
        rec.append("Strengthen supply chain to avoid stockouts.")
    if perc5 >= 30:
        rec.append(f"Projected reduction Year1→Year5 = {perc5:.1f}% — good progress; sustain scale-up.")
    else:
        rec.append(f"Projected reduction Year1→Year5 = {perc5:.1f}% — consider combining the interventions above.")
    if inc5 > inc1:
        rec.append("Warning: incidence rises by Year 5 — revisit baseline assumptions and program coverage.")
    return rec

# -------------------------
# Streamlit UI
# -------------------------
st.title("TB District Modeller (Standalone)")

with st.sidebar:
    st.header("Run options")
    years = st.slider("Projection horizon (years)", 3, 15, 5)
    calibrate_opt = st.checkbox("Calibrate beta to (notified) cases per district", value=True)
    underreporting_factor = st.number_input("Assume underreporting multiplier (if calibrating)", min_value=1.0, step=0.1, value=1.0)
    st.write("Upload a CSV with columns: district, population, notified_cases (or use manual input below).")
    st.markdown("You can download a sample CSV template from the app.")

# sample CSV template
sample_df = pd.DataFrame([{"district": "SampleDistrict", "population": 500000, "notified_cases": 975}])
csv_buf = io.StringIO()
sample_df.to_csv(csv_buf, index=False)
csv_bytes = csv_buf.getvalue().encode()

st.download_button("Download sample CSV template", data=csv_bytes, file_name="tb_district_template.csv", mime="text/csv")

uploaded = st.file_uploader("Upload CSV (optional)", type=["csv", "xlsx"])

# Manual single-district inputs
st.subheader("Single district input (use when not uploading CSV)")
col1, col2, col3 = st.columns(3)
with col1:
    district_name = st.text_input("District name", value="Example District")
    population = st.number_input("Population", min_value=1000, value=1000000, step=1000)
with col2:
    notified_cases = st.number_input("Notified cases (year)", min_value=0, value=1950, step=1)
    # user can override some important program parameters
with col3:
    detection_rate = st.slider("Detection rate (annual fraction)", 0.0, 1.0, 0.75, 0.01)
    tpt_coverage = st.slider("TPT coverage (annual fraction)", 0.0, 1.0, 0.15, 0.01)

# advanced params expander
with st.expander("Advanced parameters (edit if you know local values)"):
    colA, colB = st.columns(2)
    with colA:
        hiv_prevalence = st.number_input("HIV prevalence (fraction)", 0.0, 0.5, 0.03, 0.01)
        malnut_fraction = st.number_input("Malnutrition fraction", 0.0, 1.0, 0.25, 0.01)
        malnut_multiplier = st.number_input("Malnutrition multiplier for progression", 1.0, 5.0, 1.5, 0.1)
        private_sector_fraction = st.number_input("Private sector initial care fraction", 0.0, 1.0, 0.35, 0.05)
    with colB:
        private_notify_frac = st.number_input("Private notification fraction", 0.0, 1.0, 0.6, 0.05)
        treatment_success_s = st.number_input("Treatment success (DS-TB)", 0.5, 1.0, 0.89, 0.01)
        treatment_success_r = st.number_input("Treatment success (DR-TB)", 0.5, 1.0, 0.87, 0.01)
        stockout_frac = st.number_input("Stockout fraction (time)", 0.0, 1.0, 0.05, 0.01)

# If uploaded, read it
districts_to_run = []
if uploaded:
    try:
        if uploaded.name.endswith(".xlsx"):
            df_upload = pd.read_excel(uploaded)
        else:
            df_upload = pd.read_csv(uploaded)
        # Expect columns: district, population, notified_cases
        missing = [c for c in ["district", "population", "notified_cases"] if c not in df_upload.columns]
        if missing:
            st.warning(f"CSV missing expected columns: {missing}. You can rename columns or use the manual input.")
        else:
            st.success(f"Loaded {len(df_upload)} districts from uploaded file.")
            for _, row in df_upload.iterrows():
                districts_to_run.append({
                    "district": str(row["district"]),
                    "population": int(row["population"]),
                    "notified_cases": float(row["notified_cases"])
                })
    except Exception as e:
        st.error(f"Failed to read uploaded file: {e}")

# Also include single-district if no upload
if not uploaded:
    districts_to_run = [{
        "district": district_name,
        "population": int(population),
        "notified_cases": float(notified_cases)
    }]

# run button
run_button = st.button("Run model for districts")

results_rows = []
if run_button:
    st.info(f"Running model for {len(districts_to_run)} district(s). This may take a few seconds per district if calibrating.")
    for d in districts_to_run:
        name = d["district"]
        pop = int(d["population"])
        notified = float(d["notified_cases"])
        # Build params from UI
        local_params = {
            "N": pop,
            "detection_rate": float(detection_rate),
            "diagnostic_delay_months": 2.0,
            "private_sector_fraction": float(private_sector_fraction),
            "private_notify_frac": float(private_notify_frac),
            "tpt_coverage": float(tpt_coverage),
            "tpt_efficacy": 0.65,
            "vaccine_coverage": 0.0,
            "vaccine_efficacy": 0.0,
            "hiv_prevalence": float(hiv_prevalence),
            "hiv_progression_multiplier": 4.0,
            "malnut_fraction": float(malnut_fraction),
            "malnut_multiplier": float(malnut_multiplier),
            "ltfu_rate": 0.05,
            "stockout_frac": float(stockout_frac),
            "treatment_success_s": float(treatment_success_s),
            "treatment_success_r": float(treatment_success_r),
        }

        # Determine target incidence for calibration
        if calibrate_opt:
            # user may assume notified = incidence or apply underreporting factor
            target_cases = notified * underreporting_factor
            # calibrate beta so model's Year1 incidence equals target_cases
            try:
                with st.spinner(f"Calibrating beta for {name}..."):
                    beta_cal = calibrate_beta_to_cases(target_cases_per_year=target_cases, pop=pop, params=local_params, years=1)
                st.write(f"Calibrated beta for {name}: {beta_cal:.4f}")
            except Exception as e:
                st.error(f"Calibration failed for {name}: {e}")
                beta_cal = 4.4857421875  # fallback default
        else:
            beta_cal = 4.4857421875  # default calibrated national estimate

        # Run model with calibrated beta
        with st.spinner(f"Running model for {name}..."):
            out = run_expanded_tb(beta_cal, years=years, pop=pop, params=local_params)
        inc = out["incidence_yearly"]
        inc1 = float(inc[0]) if len(inc) >= 1 else 0.0
        inc5 = float(inc[4]) if len(inc) >= 5 else float(inc[-1])
        perc_red = 100.0 * (inc1 - inc5) / inc1 if inc1 > 0 else 0.0
        recs = generate_recommendations(local_params, perc_red, inc1, inc5)

        results_rows.append({
            "district": name,
            "population": pop,
            "notified_cases": notified,
            "beta_used": beta_cal,
            "year1_incidence": inc1,
            "year5_incidence": inc5,
            "percent_reduction_yr1_to_yr5": perc_red,
            "recommendations": " || ".join(recs)
        })

    # show results table
    results_df = pd.DataFrame(results_rows)
    st.success("Completed model runs.")
    st.dataframe(results_df)

    # Download results CSV
    csv_bytes = results_df.to_csv(index=False).encode()
    st.download_button("Download results CSV", data=csv_bytes, file_name="tb_district_results.csv", mime="text/csv")

    # Plot the first district's incidence time-series
    if len(results_rows) > 0:
        first = districts_to_run[0]["district"]
        first_out = run_expanded_tb(results_df.loc[0, "beta_used"], years=years, pop=int(results_df.loc[0, "population"]), params={
            "detection_rate": float(detection_rate),
            "diagnostic_delay_months": 2.0,
            "private_sector_fraction": float(private_sector_fraction),
            "private_notify_frac": float(private_notify_frac),
            "tpt_coverage": float(tpt_coverage),
            "tpt_efficacy": 0.65,
            "vaccine_coverage": 0.0,
            "vaccine_efficacy": 0.0,
            "hiv_prevalence": float(hiv_prevalence),
            "hiv_progression_multiplier": 4.0,
            "malnut_fraction": float(malnut_fraction),
            "malnut_multiplier": float(malnut_multiplier),
            "ltfu_rate": 0.05,
            "stockout_frac": float(stockout_frac),
            "treatment_success_s": float(treatment_success_s),
            "treatment_success_r": float(treatment_success_r),
        })
        years_axis = np.arange(1, years + 1)
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(years_axis, first_out["incidence_yearly"], marker='o')
        ax.set_xlabel("Year")
        ax.set_ylabel("New active TB cases per year")
        ax.set_title(f"Projected annual incidence for {results_df.loc[0,'district']}")
        ax.grid(True)
        st.pyplot(fig)

    # show recommendations for each district in expandable panels
    for row in results_rows:
        with st.expander(f"Recommendations — {row['district']}"):
            st.write(row["recommendations"].replace(" || ", "\n\n"))

st.markdown("---")
st.caption("Notes: This is a deterministic exploratory model for policy analysis. For operational use, calibrate inputs to Ni-kshay data and prevalence surveys, and validate with local experts.")
