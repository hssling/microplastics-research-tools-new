"""
SysRev Agent — a single‑file Streamlit app for AI‑assisted systematic reviews

Features
- Protocol & scope: capture PICO, keywords, inclusion/exclusion, outcomes
- Search: PubMed (E‑utilities) + Crossref; de‑duplication
- Screening: title/abstract screening (manual + optional LLM assist)
- Data extraction: configurable schema with LLM JSON extraction helper
- Risk of bias: RoB2 (RCT) & ROBINS‑I (obs) quick checklists
- Meta‑analysis: log risk ratio / Hedges g (random‑effects, DL)
- Reporting: PRISMA counts + diagram, forest/funnel plots, export ZIP with CSVs & figures

How to run
1) Save this file as sysrev_agent.py
2) Python 3.10+
3) pip install -U streamlit python-dotenv requests pandas numpy scipy matplotlib scikit-learn pydantic plotly tenacity openpyxl
   (Optional) graphviz + python-graphviz for prettier PRISMA
4) Put your API keys in a .env in the same folder if using LLM assist:
   OPENAI_API_KEY=sk-...
   ANTHROPIC_API_KEY=...
5) streamlit run sysrev_agent.py

Notes
- LLM calls are optional and off by default. Turn them on in the sidebar.
- PubMed / Crossref requests have public quotas; be polite.
- This is a reference implementation: validate outputs before publication.
"""

import os
import io
import json
import time
import zipfile
import math
import base64
import hashlib
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple

import requests
import pandas as pd
import numpy as np
from scipy import stats

import streamlit as st
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_exponential

# Optional plotting
import matplotlib.pyplot as plt

try:
    import graphviz
    HAS_GRAPHVIZ = True
except Exception:
    HAS_GRAPHVIZ = False

# -----------------------------
# Config & helpers
# -----------------------------

APP_VERSION = "0.1.0"

def load_env():
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except Exception:
        pass

load_env()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

@st.cache_data(show_spinner=False)
def hash_text(x: str) -> str:
    return hashlib.sha1(x.encode("utf-8")).hexdigest()[:10]

# -----------------------------
# Models
# -----------------------------

class Protocol(BaseModel):
    title: str
    question: str
    population: str
    intervention: str
    comparator: str
    outcomes: str
    study_designs: str = Field(description="e.g., RCTs, cohort, case-control")
    inclusion_criteria: str
    exclusion_criteria: str
    keywords: str

class ExtractionField(BaseModel):
    name: str
    dtype: str = Field(description="str|int|float|bool|json")
    description: str = ""

DEFAULT_FIELDS = [
    ExtractionField(name="study_id", dtype="str", description="Auto id"),
    ExtractionField(name="first_author", dtype="str"),
    ExtractionField(name="year", dtype="int"),
    ExtractionField(name="doi", dtype="str"),
    ExtractionField(name="design", dtype="str"),
    ExtractionField(name="n_intervention", dtype="int"),
    ExtractionField(name="n_control", dtype="int"),
    ExtractionField(name="event_intervention", dtype="int"),
    ExtractionField(name="event_control", dtype="int"),
    ExtractionField(name="mean_intervention", dtype="float"),
    ExtractionField(name="sd_intervention", dtype="float"),
    ExtractionField(name="mean_control", dtype="float"),
    ExtractionField(name="sd_control", dtype="float"),
    ExtractionField(name="outcome_name", dtype="str"),
]

# -----------------------------
# External APIs (PubMed, Crossref)
# -----------------------------

PUBMED_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
CROSSREF_BASE = "https://api.crossref.org/works"

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
def pubmed_search(query: str, retmax: int = 200) -> List[str]:
    url = f"{PUBMED_BASE}/esearch.fcgi"
    params = {
        "db": "pubmed",
        "term": query,
        "retmode": "json",
        "retmax": retmax,
        "sort": "relevance",
    }
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    ids = r.json().get("esearchresult", {}).get("idlist", [])
    return ids

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
def pubmed_fetch_summaries(pmids: List[str]) -> List[Dict[str, Any]]:
    if not pmids:
        return []
    url = f"{PUBMED_BASE}/esummary.fcgi"
    params = {"db": "pubmed", "id": ",".join(pmids), "retmode": "json"}
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()["result"]
    recs = []
    for pid in pmids:
        item = data.get(pid)
        if item:
            recs.append({
                "pmid": pid,
                "title": item.get("title"),
                "journal": item.get("fulljournalname"),
                "year": int(item.get("pubdate", "0")[:4] or 0),
                "authors": "; ".join([a.get("name") for a in item.get("authors", [])]),
                "doi": next((x.get("doi") for x in item.get("articleids", []) if x.get("idtype") == "doi"), None),
            })
    return recs

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
def crossref_search(query: str, rows: int = 100) -> List[Dict[str, Any]]:
    params = {"query": query, "rows": rows}
    r = requests.get(CROSSREF_BASE, params=params, timeout=30)
    r.raise_for_status()
    items = r.json().get("message", {}).get("items", [])
    results = []
    for it in items:
        results.append({
            "title": (it.get("title") or [""])[0],
            "doi": it.get("DOI"),
            "year": (it.get("issued", {}).get("'date-parts'" or "date-parts", [[None]])[0][0]) or None,
            "authors": "; ".join([f"{a.get('family','')} {a.get('given','')}".strip() for a in it.get("author", [])]),
            "journal": (it.get("container-title") or [""])[0],
            "url": it.get("URL"),
        })
    return results

# -----------------------------
# LLM helpers (optional)
# -----------------------------

def call_openai_json(prompt: str, model: str = "gpt-4o-mini") -> Dict[str, Any]:
    if not OPENAI_API_KEY:
        return {"error": "No OPENAI_API_KEY set"}
    try:
        import openai
        openai.api_key = OPENAI_API_KEY
        resp = openai.ChatCompletion.create(
            model=model,
            messages=[{"role": "system", "content": "You are a careful evidence synthesis assistant. Return strict JSON only."},
                     {"role": "user", "content": prompt}],
            temperature=0
        )
        content = resp["choices"][0]["message"]["content"]
        return json.loads(content)
    except Exception as e:
        return {"error": str(e)}

# -----------------------------
# Screening logic
# -----------------------------

INCLUDE_LABELS = ["include", "exclude", "maybe"]

def simple_rule_screen(title: str, abstract: str, inc: str, exc: str) -> str:
    t = f"{title} {abstract}".lower()
    if any(x.strip() and x.lower() in t for x in exc.split(",")):
        return "exclude"
    if any(x.strip() and x.lower() in t for x in inc.split(",")):
        return "include"
    return "maybe"

# -----------------------------
# Meta‑analysis utilities
# -----------------------------

def hedges_g(mean_t, sd_t, n_t, mean_c, sd_c, n_c):
    # unbiased standardized mean difference
    sd_pooled = math.sqrt(((n_t - 1) * sd_t ** 2 + (n_c - 1) * sd_c ** 2) / (n_t + n_c - 2))
    d = (mean_t - mean_c) / (sd_pooled + 1e-12)
    J = 1 - (3 / (4 * (n_t + n_c) - 9))
    g = J * d
    var_g = ((n_t + n_c) / (n_t * n_c)) + (g**2 / (2 * (n_t + n_c - 2)))
    return g, var_g

def log_rr(e_t, n_t, e_c, n_c):
    # add 0.5 continuity if needed
    if min(e_t, n_t - e_t, e_c, n_c - e_c) == 0:
        e_t += 0.5; e_c += 0.5; n_t += 1; n_c += 1
    rr = (e_t / (n_t - e_t)) / (e_c / (n_c - e_c))
    lrr = math.log(rr)
    var = 1/e_t + 1/e_c + 1/(n_t - e_t) + 1/(n_c - e_c)
    return lrr, var

def random_effects(y, v):
    # DerSimonian-Laird
    w = 1 / v
    y_fixed = np.sum(w * y) / np.sum(w)
    q = np.sum(w * (y - y_fixed)**2)
    df = len(y) - 1
    c = np.sum(w) - np.sum(w**2)/np.sum(w)
    tau2 = max(0, (q - df) / c)
    w_star = 1 / (v + tau2)
    y_re = np.sum(w_star * y) / np.sum(w_star)
    se = math.sqrt(1 / np.sum(w_star))
    ci = (y_re - 1.96*se, y_re + 1.96*se)
    i2 = max(0, (q - df) / q) * 100 if q > df else 0
    return y_re, se, ci, tau2, i2, q, df

# -----------------------------
# PRISMA figure
# -----------------------------

def prisma_graph(counts: Dict[str, int]):
    if HAS_GRAPHVIZ:
        dot = graphviz.Digraph(format='png')
        dot.attr(rankdir='TB', fontsize='10')
        dot.node('id', f"Identification\nRecords via databases: {counts.get('db',0)}\nOther sources: {counts.get('other',0)}")
        dot.node('scr', f"Screening\nRecords screened: {counts.get('screened',0)}\nRecords excluded: {counts.get('excluded',0)}")
        dot.node('elig', f"Eligibility\nFull-text assessed: {counts.get('fulltext',0)}\nFull-text excluded: {counts.get('fte',0)}")
        dot.node('incl', f"Included\nStudies included: {counts.get('included',0)}")
        dot.edges(['idscr', 'screlig', 'eligincl'])
        dot.edge('id','scr')
        dot.edge('scr','elig')
        dot.edge('elig','incl')
        return dot
    else:
        fig, ax = plt.subplots(figsize=(6,6))
        ax.axis('off')
        boxes = [
            (0.5, 0.9, f"Identification\nDB: {counts.get('db',0)} | Other: {counts.get('other',0)}"),
            (0.5, 0.6, f"Screening\nScreened: {counts.get('screened',0)}\nExcluded: {counts.get('excluded',0)}"),
            (0.5, 0.35, f"Eligibility\nFull-text: {counts.get('fulltext',0)}\nFT excluded: {counts.get('fte',0)}"),
            (0.5, 0.1, f"Included\nStudies: {counts.get('included',0)}"),
        ]
        for x,y,text in boxes:
            ax.add_patch(plt.Rectangle((x-0.35, y-0.09), 0.7, 0.18, fill=False))
            ax.text(x, y, text, ha='center', va='center')
        # arrows
        ax.annotate('', xy=(0.5,0.51), xytext=(0.5,0.81), arrowprops=dict(arrowstyle='->'))
        ax.annotate('', xy=(0.5,0.26), xytext=(0.5,0.51), arrowprops=dict(arrowstyle='->'))
        ax.annotate('', xy=(0.5,0.01), xytext=(0.5,0.26), arrowprops=dict(arrowstyle='->'))
        st.pyplot(fig)
        return None

# -----------------------------
# Streamlit UI
# -----------------------------

st.set_page_config(page_title="SysRev Agent", layout="wide")
st.title("🔎 SysRev Agent — AI‑assisted Systematic Review")
st.caption(f"v{APP_VERSION} · This tool helps you go from protocol → search → screen → extract → meta‑analyze → report.")

with st.sidebar:
    st.header("Settings")
    use_llm = st.toggle("Enable LLM assistance (optional)", value=False)
    model_name = st.text_input("LLM model (OpenAI)", value="gpt-4o-mini")
    st.divider()
    st.markdown("**Export**")
    want_zip = st.toggle("Prepare export ZIP (CSV + figures + report)", value=True)

st.subheader("1) Protocol")
with st.expander("Define protocol & scope", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        title = st.text_input("Review title", value="Effect of X vs Y on Outcome Z in Population P")
        question = st.text_area("Research question", value="In [Population], does [Intervention] versus [Comparator] improve [Outcomes]?")
        population = st.text_input("Population")
        intervention = st.text_input("Intervention")
        comparator = st.text_input("Comparator")
        outcomes = st.text_input("Primary outcomes (comma‑sep)")
    with col2:
        study_designs = st.text_input("Study designs", value="RCT, cohort")
        inclusion = st.text_area("Inclusion keywords (comma‑sep)", value="randomized, trial, adults")
        exclusion = st.text_area("Exclusion keywords (comma‑sep)", value="animal, pediatric, case report")
        keywords = st.text_area("Search keywords (boolean ok)", value="(intervention) AND (condition) AND (randomized OR trial)")

    proto = Protocol(
        title=title, question=question, population=population, intervention=intervention,
        comparator=comparator, outcomes=outcomes, study_designs=study_designs,
        inclusion_criteria=inclusion, exclusion_criteria=exclusion, keywords=keywords
    )
    st.session_state["protocol"] = proto.dict()

st.subheader("2) Search")
with st.expander("Query databases & import results", expanded=True):
    colp, colc = st.columns(2)
    with colp:
        st.markdown("**PubMed**")
        pm_retmax = st.number_input("Max results", 50, 10000, 200, step=50)
        if st.button("Search PubMed"):
            with st.spinner("Searching PubMed..."):
                pmids = pubmed_search(proto.keywords, retmax=int(pm_retmax))
                summaries = pubmed_fetch_summaries(pmids)
                df_pm = pd.DataFrame(summaries)
                st.session_state["df_pubmed"] = df_pm
                st.success(f"Found {len(df_pm)} records from PubMed")
                st.dataframe(df_pm.head(20), use_container_width=True)
    with colc:
        st.markdown("**Crossref**")
        cr_rows = st.number_input("Max results", 50, 1000, 100, step=50, key="crrows")
        if st.button("Search Crossref"):
            with st.spinner("Searching Crossref..."):
                cr = crossref_search(proto.keywords, rows=int(cr_rows))
                df_cr = pd.DataFrame(cr)
                st.session_state["df_crossref"] = df_cr
                st.success(f"Found {len(df_cr)} records from Crossref")
                st.dataframe(df_cr.head(20), use_container_width=True)

    if st.button("Combine & de‑duplicate"):
        df_pm = st.session_state.get("df_pubmed", pd.DataFrame())
        df_cr = st.session_state.get("df_crossref", pd.DataFrame())
        df = pd.concat([df_pm, df_cr], ignore_index=True, sort=False)
        # basic normalization
        df['title'] = df['title'].fillna("").str.strip()
        df['year'] = pd.to_numeric(df.get('year'), errors='coerce').astype('Int64')
        df['doi'] = df.get('doi').fillna(df.get('url'))
        # dedup by DOI or title
        before = len(df)
        df = df.drop_duplicates(subset=['doi']).copy()
        df = df.drop_duplicates(subset=['title']).copy()
        after = len(df)
        st.session_state["df_master"] = df
        st.success(f"Combined {before} → {after} unique records")
        st.dataframe(df.head(30), use_container_width=True)

st.subheader("3) Screening")
with st.expander("Title/abstract screening", expanded=True):
    dfm = st.session_state.get("df_master")
    if dfm is None or dfm.empty:
        st.info("Import or search records first.")
    else:
        inc = proto.inclusion_criteria
        exc = proto.exclusion_criteria
        if st.button("Auto‑label (rule‑based)"):
            lab = []
            for _, r in dfm.iterrows():
                lab.append(simple_rule_screen(r.get('title',''), r.get('abstract',''), inc, exc))
            dfm['label'] = lab
            st.session_state["df_master"] = dfm
            st.success("Applied quick rule‑based labels.")
        if use_llm and st.button("LLM‑assist labels"):
            labels = []
            for _, r in dfm.iterrows():
                prompt = f"""
                Task: classify this study for inclusion in a systematic review. Return JSON {{label: include|exclude|maybe, rationale: str}}.
                Inclusion clues: {inc}
                Exclusion clues: {exc}
                Title: {r.get('title','')}
                Abstract: {r.get('abstract','')}
                """
                out = call_openai_json(prompt, model=model_name)
                labels.append(out.get('label','maybe') if isinstance(out, dict) else 'maybe')
            dfm['label'] = labels
            st.session_state["df_master"] = dfm
            st.success("LLM‑assisted labels applied.")
        st.dataframe(dfm, use_container_width=True)
        # counts for PRISMA
        n_db = int(st.session_state.get("df_pubmed", pd.DataFrame()).shape[0] or 0) + int(st.session_state.get("df_crossref", pd.DataFrame()).shape[0] or 0)
        n_screened = int(dfm.shape[0])
        n_excl = int((dfm.get('label') == 'exclude').sum()) if 'label' in dfm else 0
        st.session_state['prisma_counts'] = {
            'db': n_db, 'other': 0, 'screened': n_screened, 'excluded': n_excl,
            'fulltext': 0, 'fte': 0, 'included': int((dfm.get('label') == 'include').sum()) if 'label' in dfm else 0
        }

st.subheader("4) Data extraction")
with st.expander("Configure schema & extract", expanded=True):
    schema_json = st.text_area("Extraction schema (JSON)",
        value=json.dumps([f.dict() for f in DEFAULT_FIELDS], indent=2), height=220)
    try:
        fields = [ExtractionField(**x) for x in json.loads(schema_json)]
    except Exception as e:
        st.error(f"Invalid schema JSON: {e}")
        fields = DEFAULT_FIELDS
    dfm = st.session_state.get("df_master", pd.DataFrame())
    if dfm is None or dfm.empty:
        st.info("No records. Perform search & screening first.")
    else:
        incl_df = dfm if 'label' not in dfm else dfm[dfm['label'].isin(['include','maybe'])]
        st.markdown("**Records to extract from (filtered to include/maybe):**")
        st.dataframe(incl_df[['title','year','doi']].head(50), use_container_width=True)
        if use_llm and st.button("LLM‑assist extraction (from title/abstract)"):
            rows = []
            for _, r in incl_df.iterrows():
                schema = {f.name: f"<{f.dtype}>" for f in fields}
                prompt = f"""
                Extract the following fields from the study title and abstract. Return STRICT JSON with those keys only.
                Schema: {json.dumps(schema)}
                Title: {r.get('title','')}
                Abstract: {r.get('abstract','(none provided)')}
                If a field is unknown, put null.
                """
                out = call_openai_json(prompt, model=model_name)
                if isinstance(out, dict) and not out.get('error'):
                    out['study_id'] = out.get('study_id') or hash_text(r.get('title',''))
                    rows.append(out)
            if rows:
                dfe = pd.DataFrame(rows)
                st.session_state['df_extract'] = dfe
                st.success(f"Extracted {len(dfe)} rows via LLM.")
                st.dataframe(dfe, use_container_width=True)
        st.markdown("Or paste your extracted data (CSV → table):")
        up = st.file_uploader("Upload CSV with your extraction", type=["csv","xlsx"])
        if up:
            if up.name.endswith('.xlsx'):
                dfe = pd.read_excel(up)
            else:
                dfe = pd.read_csv(up)
            st.session_state['df_extract'] = dfe
            st.dataframe(dfe, use_container_width=True)

st.subheader("5) Meta‑analysis")
with st.expander("Compute effects & plots", expanded=True):
    dfe = st.session_state.get('df_extract', pd.DataFrame())
    if dfe is None or dfe.empty:
        st.info("No extraction data available.")
    else:
        eff_type = st.selectbox("Effect type", ["Risk ratio (binary)", "Hedges g (continuous)"])
        rows = []
        for _, r in dfe.iterrows():
            try:
                if eff_type.startswith("Risk"):
                    lrr, var = log_rr(int(r['event_intervention']), int(r['n_intervention']), int(r['event_control']), int(r['n_control']))
                    rows.append({"study": r.get('first_author', r.get('study_id','?')) + f" ({int(r.get('year',0))})", "yi": lrr, "vi": var})
                else:
                    g, var = hedges_g(float(r['mean_intervention']), float(r['sd_intervention']), int(r['n_intervention']), float(r['mean_control']), float(r['sd_control']), int(r['n_control']))
                    rows.append({"study": r.get('first_author', r.get('study_id','?')) + f" ({int(r.get('year',0))})", "yi": g, "vi": var})
            except Exception:
                continue
        if not rows:
            st.warning("Could not compute any effects from the provided rows. Check columns.")
        else:
            dfy = pd.DataFrame(rows)
            y_re, se, ci, tau2, i2, q, df = random_effects(dfy['yi'].values, dfy['vi'].values)
            st.markdown(f"**Random‑effects pooled estimate:** {y_re:.3f} (95% CI {ci[0]:.3f} to {ci[1]:.3f})  ")
            st.markdown(f"τ²={tau2:.3f}, I²={i2:.1f}%, Q={q:.2f} (df={df})")

            fig = plt.figure(figsize=(6, 0.4*len(dfy)+2))
            ax = fig.add_subplot(111)
            y_pos = np.arange(len(dfy))
            for i, row in enumerate(dfy.itertuples()):
                se_i = math.sqrt(row.vi)
                ci_lo, ci_hi = row.yi - 1.96*se_i, row.yi + 1.96*se_i
                ax.plot([ci_lo, ci_hi], [i, i], '-o')
            ax.axvline(x=y_re, linestyle='--')
            ax.set_yticks(y_pos)
            ax.set_yticklabels(dfy['study'].tolist())
            ax.set_xlabel('Effect size (log RR or g)')
            ax.set_title('Forest plot')
            st.pyplot(fig)

            # Funnel plot
            fig2 = plt.figure(figsize=(5,5))
            ax2 = fig2.add_subplot(111)
            se_arr = np.sqrt(dfy['vi'].values)
            ax2.scatter(dfy['yi'].values, se_arr)
            ax2.invert_yaxis()
            ax2.set_xlabel('Effect size')
            ax2.set_ylabel('SE')
            ax2.set_title('Funnel plot')
            st.pyplot(fig2)

st.subheader("6) Reporting")
with st.expander("PRISMA & Export", expanded=True):
    counts = st.session_state.get('prisma_counts', {k:0 for k in ['db','other','screened','excluded','fulltext','fte','included']})
    st.json(counts)
    if st.button("Render PRISMA figure"):
        dot = prisma_graph(counts)
        if dot is not None and HAS_GRAPHVIZ:
            st.graphviz_chart(dot.source)
    if want_zip and st.button("Build export ZIP"):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
            # protocol
            z.writestr('protocol.json', json.dumps(st.session_state.get('protocol', {}), indent=2))
            # search tables
            for key in ['df_pubmed','df_crossref','df_master','df_extract']:
                df = st.session_state.get(key)
                if isinstance(df, pd.DataFrame) and not df.empty:
                    z.writestr(f'{key}.csv', df.to_csv(index=False))
            # simple report
            report = [
                f"# {proto.title}",
                "\n## Question\n" + proto.question,
                "\n## PRISMA counts\n" + json.dumps(counts, indent=2),
                "\n*Generated by SysRev Agent.*"
            ]
            z.writestr('report.md', "\n".join(report))
        st.download_button("Download results ZIP", data=buf.getvalue(), file_name="sysrev_agent_export.zip", mime="application/zip")

st.divider()
st.caption("Tip: Validate AI‑assisted steps (screening, extraction) with human review. This app is a helper, not a substitute for methodological rigor.")
