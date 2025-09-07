import React, { useState, useMemo } from 'react'

// TB Model Web App
// Single-file React component. Uses Tailwind CSS utility classes.
// - Allows user to enter district name + population and tweak parameters
// - Runs an expanded deterministic compartmental model in the browser (JS translation of Python model)
// - Shows annual incidence chart (Recharts) and a simple recommendation panel
// - Provides presets for typical district profiles

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

export default function TBModelWebApp() {
  // district / identity
  const [district, setDistrict] = useState('Example District')
  const [population, setPopulation] = useState(1000000)

  // epidemiological params (clustered from expanded model)
  const defaultParams = {
    beta: 4.4857421875,
    prop_resistant: 0.025,
    sigma: 0.10,
    hiv_prevalence: 0.03,
    hiv_progression_multiplier: 4.0,
    detection_rate: 0.75,
    diagnostic_delay_months: 2.0,
    private_sector_fraction: 0.35,
    private_notify_frac: 0.6,
    treatment_initiation_rate: 0.95,
    treatment_success_s: 0.89,
    treatment_success_r: 0.87,
    treatment_duration_months_s: 6,
    treatment_duration_months_r: 9,
    relapse_rate: 0.02,
    natural_death_rate: 0.007,
    tb_death_rate_s: 0.05,
    tb_death_rate_r: 0.12,
    tpt_coverage: 0.15,
    tpt_efficacy: 0.65,
    contact_rate_multiplier: 1.0,
    vaccine_coverage: 0.0,
    vaccine_efficacy: 0.0,
    malnut_fraction: 0.25,
    malnut_multiplier: 1.5,
    ltfu_rate: 0.08,
    stockout_frac: 0.05
  }

  const [params, setParams] = useState(defaultParams)
  const [years, setYears] = useState(10)
  const [result, setResult] = useState(null)

  // presets
  const presets = {
    'Urban High-burden': { detection_rate: 0.70, tpt_coverage: 0.10, private_sector_fraction: 0.50, malnut_fraction: 0.20 },
    'Rural Low-resources': { detection_rate: 0.60, tpt_coverage: 0.05, private_sector_fraction: 0.20, malnut_fraction: 0.30, stockout_frac: 0.10 },
    'High HIV prevalence': { hiv_prevalence: 0.08, detection_rate: 0.65, tpt_coverage: 0.10 }
  }

  function applyPreset(name) {
    const p = presets[name]
    setParams(prev => ({...prev, ...p}))
  }

  // Model: direct translation of the expanded deterministic model to JS
  function runModel(beta, years, pop, p) {
    const months = years * 12
    const beta_m = beta / 12.0 * p.contact_rate_multiplier
    const sigma_m = p.sigma / 12.0
    const detection_month_base = 1 - Math.pow(1 - p.detection_rate, 1/12)
    const detection_month = detection_month_base / Math.max(1.0, p.diagnostic_delay_months)
    const tinit_m = 1 - Math.pow(1 - p.treatment_initiation_rate, 1/12)
    const relapse_m = 1 - Math.pow(1 - p.relapse_rate, 1/12)
    const natdeath_m = 1 - Math.pow(1 - p.natural_death_rate, 1/12)
    const tbdeath_s_m = 1 - Math.pow(1 - p.tb_death_rate_s, 1/12)
    const tbdeath_r_m = 1 - Math.pow(1 - p.tb_death_rate_r, 1/12)
    const fail_to_resistant = 0.10

    // Initialization using target incidence heuristic (195/100k)
    const incidence_rate_per_year = 195 / 100000
    const annual_incidence = incidence_rate_per_year * pop
    let L0 = annual_incidence / Math.max(p.sigma, 1e-6)
    let Iu_s0 = Math.max(10, annual_incidence / 5)
    let Iu_r0 = Math.max(1, Iu_s0 * p.prop_resistant / (1 - p.prop_resistant))
    let Id_s0 = Iu_s0 * 0.2
    let Id_r0 = Iu_r0 * 0.2
    let Ts0 = Id_s0 * 0.5
    let Tr0 = Id_r0 * 0.5
    let R0 = 0
    let V0 = p.vaccine_coverage * pop
    let S0 = pop - (L0 + Iu_s0 + Iu_r0 + Id_s0 + Id_r0 + Ts0 + Tr0 + R0 + V0)
    if (S0 < 0) {
      S0 = Math.max(0, pop - (Iu_s0 + Iu_r0 + Id_s0 + Id_r0 + Ts0 + Tr0 + R0 + V0))
      L0 = pop - (S0 + Iu_s0 + Iu_r0 + Id_s0 + Id_r0 + Ts0 + Tr0 + R0 + V0)
    }

    // allocate arrays
    const S = new Array(months+1).fill(0)
    const V = new Array(months+1).fill(0)
    const L = new Array(months+1).fill(0)
    const Iu_s = new Array(months+1).fill(0)
    const Id_s = new Array(months+1).fill(0)
    const Ts = new Array(months+1).fill(0)
    const Iu_r = new Array(months+1).fill(0)
    const Id_r = new Array(months+1).fill(0)
    const Tr = new Array(months+1).fill(0)
    const R = new Array(months+1).fill(0)
    const new_cases_month = new Array(months+1).fill(0)

    S[0]=S0; V[0]=V0; L[0]=L0
    Iu_s[0]=Iu_s0; Iu_r[0]=Iu_r0; Id_s[0]=Id_s0; Id_r[0]=Id_r0
    Ts[0]=Ts0; Tr[0]=Tr0; R[0]=R0

    function effective_success(base_success) {
      const s = base_success * (1 - p.stockout_frac) * (1 - p.ltfu_rate)
      return Math.max(0.0, Math.min(0.99, s))
    }

    for (let m=0; m<months; m++) {
      const Ncur = S[m] + V[m] + L[m] + Iu_s[m] + Id_s[m] + Ts[m] + Iu_r[m] + Id_r[m] + Tr[m] + R[m]
      const infectious = Iu_s[m] + Id_s[m] + Iu_r[m] + Id_r[m]
      const force = beta_m * infectious / Math.max(Ncur,1)
      const effective_S = S[m] + (1 - p.vaccine_efficacy) * V[m]
      const new_infections = force * effective_S
      const new_infections_r = new_infections * p.prop_resistant
      const new_infections_s = new_infections - new_infections_r

      const hiv_frac = p.hiv_prevalence
      const maln_frac = p.malnut_fraction
      const sigma_eff_nonhiv = sigma_m * ((1 - maln_frac) + maln_frac * p.malnut_multiplier)
      const sigma_eff_hiv = sigma_m * p.hiv_progression_multiplier * ((1 - maln_frac) + maln_frac * p.malnut_multiplier)
      const progressions = sigma_eff_nonhiv * (1 - hiv_frac) * L[m] + sigma_eff_hiv * hiv_frac * L[m]
      const prog_r = progressions * p.prop_resistant
      const prog_s = progressions - prog_r

      const detected_s = detection_month * Iu_s[m]
      const detected_r = detection_month * Iu_r[m]
      const notify_frac = (1 - p.private_sector_fraction) + p.private_sector_fraction * p.private_notify_frac
      const notified_s = detected_s * notify_frac
      const notified_r = detected_r * notify_frac
      const undetected_nonnotified_s = detected_s - notified_s
      const undetected_nonnotified_r = detected_r - notified_r

      const start_Ts = tinit_m * notified_s
      const start_Tr = tinit_m * notified_r

      const deaths_Iu_s = tbdeath_s_m * Iu_s[m]
      const deaths_Iu_r = tbdeath_r_m * Iu_r[m]
      const deaths_Id_s = tbdeath_s_m * Id_s[m]
      const deaths_Id_r = tbdeath_r_m * Id_r[m]

      const comp_Ts = (1.0 / p.treatment_duration_months_s) * Ts[m]
      const comp_Tr = (1.0 / p.treatment_duration_months_r) * Tr[m]
      const succ_Ts = comp_Ts * effective_success(p.treatment_success_s)
      const fail_Ts = comp_Ts - succ_Ts
      const succ_Tr = comp_Tr * effective_success(p.treatment_success_r)
      const fail_Tr = comp_Tr - succ_Tr

      const new_resistant_from_fail = fail_Ts * fail_to_resistant
      const returned_inf_from_fail_s = fail_Ts - new_resistant_from_fail
      const returned_inf_from_fail_r = fail_Tr

      const relapses = relapse_m * R[m]

      S[m+1] = S[m] - new_infections - natdeath_m * S[m] + natdeath_m * Ncur * (S[m]/Ncur)
      V[m+1] = V[m] - (- natdeath_m * V[m] + natdeath_m * Ncur * (V[m]/Ncur))
      L[m+1] = L[m] + new_infections_s + new_infections_r + relapses - progressions - natdeath_m * L[m]
      Iu_s[m+1] = Iu_s[m] + prog_s + undetected_nonnotified_s + returned_inf_from_fail_s - detected_s - deaths_Iu_s - natdeath_m * Iu_s[m]
      Iu_r[m+1] = Iu_r[m] + prog_r + new_resistant_from_fail + undetected_nonnotified_r + returned_inf_from_fail_r - detected_r - deaths_Iu_r - natdeath_m * Iu_r[m]
      Id_s[m+1] = Id_s[m] + notified_s - start_Ts - deaths_Id_s - natdeath_m * Id_s[m]
      Id_r[m+1] = Id_r[m] + notified_r - start_Tr - deaths_Id_r - natdeath_m * Id_r[m]
      Ts[m+1] = Ts[m] + start_Ts - comp_Ts - natdeath_m * Ts[m]
      Tr[m+1] = Tr[m] + start_Tr - comp_Tr - natdeath_m * Tr[m]
      R[m+1] = R[m] + succ_Ts + succ_Tr - relapses - natdeath_m * R[m]

      new_cases_month[m+1] = progressions

      // prevent negativity
      const arrs = [S,V,L,Iu_s,Id_s,Ts,Iu_r,Id_r,Tr,R]
      for (let a of arrs) {
        if (a[m+1] < 0) a[m+1] = 0
      }
    }

    const incidence_yearly = []
    for (let y=0; y<years; y++){
      const start = y*12
      const end = start + 12
      let sum = 0
      for (let k=start; k<=end; k++) sum += new_cases_month[k]
      incidence_yearly.push(sum)
    }

    return { incidence_yearly, compartments: {S,V,L,Iu_s,Id_s,Ts,Iu_r,Id_r,Tr,R}, params: p }
  }

  function runSimulation() {
    const out = runModel(params.beta, years, population, params)
    // compute percent change year1->year5
    const inc = out.incidence_yearly
    const perc = (inc[0] > 0) ? 100 * (inc[0] - inc[Math.min(4, inc.length-1)]) / inc[0] : 0
    // produce recommendation text
    const recs = generateRecommendations(params, perc, inc)
    setResult({ out, perc, recs })
  }

  function generateRecommendations(p, perc5, inc) {
    // Simple rule-based recommendations
    const rec = []
    if (p.detection_rate < 0.80) rec.push('Increase case detection: scale active case finding, AI-CXR triage, private sector notification incentives.')
    if (p.tpt_coverage < 0.30) rec.push('Scale-up TPT to contacts and high-risk groups (target ≥30% annual coverage).')
    if (p.treatment_success_s < 0.90 || p.treatment_success_r < 0.90) rec.push('Strengthen treatment support: adherence counselling, shorter regimens (BPaLM), monitor for stockouts and LTFU.')
    if (p.private_sector_fraction > 0.3 && p.private_notify_frac < 0.8) rec.push('Engage private sector: e-prescriptions, reporting incentives, pharmacist linkages to Ni-kshay.')
    if (p.malnut_fraction > 0.2) rec.push('Address nutrition: increase Ni-kshay Poshan or direct food support for vulnerable households.')
    if (p.hiv_prevalence > 0.05) rec.push('Integrate TB/HIV services: routine screening, ART optimisation and TPT for PLHIV.')
    if (p.stockout_frac > 0.05) rec.push('Strengthen supply chain management to avoid drug stockouts.')
    if (perc5 > 30) rec.push(`Projected reduction Year1->Year5 = ${perc5.toFixed(1)}% — good progress; maintain and scale.`)
    else rec.push(`Projected reduction Year1->Year5 = ${perc5.toFixed(1)}% — consider combination interventions listed above to improve impact.`)
    return rec
  }

  // UI
  return (
    <div className="p-6 max-w-7xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">TB Strategic Simulator — District-level</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="col-span-1 bg-white shadow p-4 rounded">
          <label className="block font-semibold">District</label>
          <input className="w-full border p-2 rounded mt-1" value={district} onChange={e=>setDistrict(e.target.value)} />
          <label className="block font-semibold mt-3">Population</label>
          <input type="number" className="w-full border p-2 rounded mt-1" value={population} onChange={e=>setPopulation(Number(e.target.value))} />

          <div className="mt-4">
            <label className="font-semibold">Presets</label>
            <div className="flex gap-2 mt-2">
              {Object.keys(presets).map(k => (
                <button key={k} onClick={()=>applyPreset(k)} className="px-2 py-1 bg-slate-100 rounded">{k}</button>
              ))}
            </div>
          </div>

          <div className="mt-4">
            <label className="font-semibold">Years</label>
            <input type="number" className="w-full border p-2 rounded mt-1" value={years} onChange={e=>setYears(Math.max(1, Number(e.target.value)))} />
          </div>

          <div className="mt-4">
            <button onClick={runSimulation} className="w-full bg-indigo-600 text-white py-2 rounded">Run Simulation</button>
          </div>
        </div>

        <div className="col-span-2 bg-white shadow p-4 rounded">
          <h2 className="font-semibold">Core parameters</h2>
          <div className="grid grid-cols-2 gap-3 mt-3">
            {Object.keys(defaultParams).map(key => (
              <div key={key} className="">
                <label className="text-sm capitalize">{key.replace(/_/g,' ')}</label>
                <input value={params[key]} onChange={e=>setParams(prev=>({...prev,[key]: parseFloat(e.target.value)}))} className="w-full border p-1 rounded mt-1" />
              </div>
            ))}
          </div>
          <div className="mt-4">
            <p className="text-sm text-slate-600">Tip: adjust detection_rate, tpt_coverage, treatment_success_s and stockout_frac to model service improvements.</p>
          </div>
        </div>
      </div>

      <div className="mt-6 bg-white p-4 shadow rounded">
        <h3 className="font-semibold">Results</h3>
        {!result && <p className="text-sm text-slate-600">No results yet — run the simulation.</p>}
        {result && (
          <div className="mt-3">
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={result.out.incidence_yearly.map((v,i)=>({year: i+1, incidence: Math.round(v)}))}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="year" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="incidence" stroke="#8884d8" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>

            <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-3 border rounded">
                <h4 className="font-semibold">Key metrics</h4>
                <p>Year-1 incidence: {Math.round(result.out.incidence_yearly[0])}</p>
                <p>Year-5 incidence: {Math.round(result.out.incidence_yearly[Math.min(4,result.out.incidence_yearly.length-1)])}</p>
                <p>Percent reduction Year1→Year5: {result.perc.toFixed(1)}%</p>
              </div>

              <
              div className="p-3 border rounded">
                <h4 className="font-semibold">Recommendations</h4>
                <ul className="list-disc pl-5">
                  {result.recs.map((r,i)=>(<li key={i}>{r}</li>))}
                </ul>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="mt-6 text-sm text-slate-600">
        <p>Notes: This deterministic model is for rapid policy exploration. For district-level deployment, calibrate with local Ni-kshay data, private-sector notification rates, and prevalence surveys. Use the exported results for further analysis.</p>
      </div>
    </div>
  )
}
