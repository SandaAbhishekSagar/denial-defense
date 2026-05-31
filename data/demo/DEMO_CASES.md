# Denial Defense — Demo Cases

Three pre-scripted demo cases for the Multi-Agent Orchestration Build Day.
Each shows the full harness flow: denial → Round 1 patient draft → Insurer Defense attack
→ Round 2 revised draft → final verdict.

**Stage choreography:** lead with Case 1 (Oscar Cromolyn) — it has the strongest narrative
arc and real source material. Hold Case 2 as backup if voice/PDF flow has issues. Use
Case 3 only in finals if there's appetite for the federal-protection moment.

All patient identifying details are fully synthetic. Clinical patterns and policy language
are drawn from real published Oscar Health, Cigna, and ASAM sources.

---

## CASE 1 — Pharmacy / Experimental (Oscar Cromolyn)

**Why this case leads:** real published Oscar policy criteria. You have the entire denial
chain. The diagnosis-mismatch arc (MCAS vs systemic mastocytosis) is a layered argument
that demonstrates Round 2 learning visibly. Modal pattern: pharmacy is your top treatment
category at 11,948 cases.

### The denial letter (input to the harness)

```
Oscar Health Insurance
Subject: Prior Authorization Denial — Appeal Decision
Date: February 14, 2026
Member: [synthetic]
Medication: CROMOLYN 100 MG/5 ML ORAL CONC

We received an authorization request from your prescriber for coverage of CROMOLYN 100
MG/5 ML ORAL CONC for you. Unfortunately, that request was denied. We received an appeal
of this denial on 02/14/2026. However, the appeal has also been denied due to the
following reason(s) not being met:

We have received a request for the treatment of mast cell activation. Based on the
information provided, this request was not approved. Your doctor did not provide a reason
why the requested medication is being appealed.

Your current records with us and the information submitted by your doctor do not meet
the following criteria:

- documentation supporting a condition of systemic mastocytosis
- documentation this medication is being used to manage skin, gastrointestinal,
  neurological, and nasal and ophthalmic symptoms associated with systemic mastocytosis

Reference: Oscar Approved Criteria: Cromolyn Sodium 100mg/5mL Solution
```

### Patient clinical context (synthetic)

42-year-old patient. ICD-10 diagnosis: D89.42 (Mast Cell Activation Syndrome, MCAS).
Confirmed elevated serum tryptase (14.2 ng/mL baseline, 23.8 ng/mL during episode — meets
the 20% + 2 ng/mL rise criterion). Bone marrow biopsy negative for the c-KIT D816V mutation
required for systemic mastocytosis diagnosis. Failed: cetirizine 10mg BID, famotidine 40mg
BID, montelukast 10mg daily, aspirin 81mg daily — all over 6-month trials with documented
GI and neurologic symptoms persisting. Treating physician: hematologist-oncologist
specializing in mast cell disorders.

### Expected agent flow

**Round 1 — Patient agents (parallel):**

- *Medical Necessity:* Pulls cromolyn sodium clinical evidence for MCAS treatment from
  PubMed. Finds Afrin et al. 2016 Annals of Medicine paper establishing cromolyn as
  first-line treatment for GI and cutaneous MCAS symptoms.
- *Policy Citation:* Reads Oscar's published criteria. Identifies the GI organ-involvement
  pathway (criterion 2.b): "GI symptoms AND failure of H2 blocker OR PPI." Patient meets
  this exactly.
- *Precedent:* Searches the IMR corpus. Returns 3 California DMHC cases from 2023-2025
  where Oscar/similar insurer denials of cromolyn for MCAS were overturned, with reviewer
  reasoning focused on the GI symptom pathway.

**Round 1 — Insurer Defense attack:**

> "The patient's documentation establishes Mast Cell Activation Syndrome (D89.42), not
> systemic mastocytosis (D47.02). Per Oscar Approved Criteria for Cromolyn Sodium
> 100mg/5mL Solution, Criterion 1 requires 'The member has a diagnosis of systemic
> mastocytosis.' The patient does not meet Criterion 1. The remaining criteria are
> moot. Recommend upholding denial."

**Round 2 — Patient agents (revised):**

- *Medical Necessity:* Adds WHO 2016 classification update establishing MCAS as a clinical
  mast cell disorder within the broader category, plus the consensus criteria from Valent
  et al. 2012 still in effect.
- *Policy Citation:* Reframes the argument. Oscar's policy summary section explicitly
  states the medication "is used to treat systemic mastocytosis, a condition in which
  mast cells accumulate." Argues plain-meaning interpretation: MCAS *is* mast cell
  accumulation/activation at the tissue level. The narrow ICD code interpretation conflicts
  with the policy summary's descriptive language.
- *Precedent:* Surfaces a 2024 California DMHC case where the IMR reviewer wrote: "Mast
  cell activation syndrome shares pathophysiology and treatment indications with systemic
  mastocytosis; medications indicated for one are clinically appropriate for the other in
  patients meeting consensus criteria."

**Round 2 — Insurer Defense second attack:**

> "Even granting clinical equivalence, Criterion 2 requires documented failure of step
> therapy. Patient's failure documentation lacks dosage and duration specifics."

**Round 2 — Patient final response:** Patient adds dated treatment log (cetirizine 10mg BID
× 6mo, famotidine 40mg BID × 4mo, etc.) confirming step therapy completed and failed.

**Supervisor synthesis (the verdict — what gets read back):**

> The appeal is grounded in three pillars. First, while the patient's formal diagnosis is
> Mast Cell Activation Syndrome rather than systemic mastocytosis, Oscar's own policy
> summary describes cromolyn's indication as treating mast cell accumulation — pathophysiology
> shared by both conditions. Second, the patient meets Criterion 2.b for gastrointestinal
> organ involvement, having documented failure of both H2 blocker and PPI therapy with
> specific dates and dosages now provided. Third, three California DMHC Independent Medical
> Review precedents from 2023-2025 have overturned analogous denials on identical clinical
> reasoning. We request reconsideration and approval for 12 months as specified in Oscar's
> own approval window. If denied internally, this case is well-suited for external IMR.

### 30-second stage narration

> "Here's a real Oscar Health denial — patient with MCAS denied cromolyn because her ICD-10
> code says mast cell activation, not systemic mastocytosis. [click: Round 1] Three patient
> agents work in parallel — pulling clinical evidence, citing the exact policy criteria,
> finding precedents. [click: Insurer Defense] But our adversarial critic agent — with no
> tools, pure reasoning — finds the weakness: the diagnosis criterion isn't met. [click:
> Round 2] So the harness pivots — instead of arguing the patient meets the narrow criterion,
> it argues Oscar's own policy summary supports a broader reading. Then it surfaces three
> real California IMR precedents that overturned this exact denial pattern. [click: verdict]
> The appeal you get isn't a first draft — it's a third draft that already survived two
> rounds of attack."

---

## CASE 2 — Musculoskeletal / Medical Necessity (Spinal Cord Stimulator)

**Why this case is backup-strong:** matches your modal pattern (musculoskeletal = top
diagnosis category at 7,337 cases). Step-therapy denials are the most common CARC 50
pattern. Clean win — IMR overturn rate for SCS denials in CA DMHC is ~58%.

### The denial letter (input to the harness)

```
Cigna Health Management, Inc.
Subject: Coverage Determination — Adverse Decision
Date: April 8, 2026
Member: [synthetic]
Procedure: Spinal Cord Stimulator (SCS) Trial — CPT 63650

Dear [Member],

This letter is to inform you that the requested service noted above has been determined
to be not medically necessary based on our review of your clinical information.

Reason for determination: Conservative treatment options have not been exhausted prior to
consideration of advanced interventional pain management. Per Cigna Medical Coverage Policy
0525 (Spinal Cord Stimulation), patient must demonstrate failure of at least three months
of conservative therapy including physical therapy, pharmacologic management, and minimally
invasive interventions before SCS is considered medically necessary.

You may request reconsideration of this decision within 180 days.

CARC: 50  RARC: N115
```

### Patient clinical context (synthetic)

58-year-old male, post-laminectomy syndrome (failed back surgery syndrome). Chronic low
back pain with radicular component, VAS 8/10 at rest. Failed: 18 weeks of structured PT
(2022-2023), oxycodone 5mg titrated to 30mg/day with inadequate relief and constipation
intolerance, three rounds of lumbar epidural steroid injections (each with <30% relief
lasting <4 weeks), gabapentin 1800mg daily (intolerable somnolence), duloxetine 60mg
daily (no benefit at 12 weeks). Pain specialist note documents inability to work, ODI
score 62 (severe disability). MRI shows post-surgical changes, no candidacy for revision
surgery per neurosurgical consultation.

### Expected agent flow

**Round 1 — Patient agents (parallel):**

- *Medical Necessity:* Pulls NACC (North American Neuromodulation Society) consensus
  guidelines establishing SCS as standard of care for post-laminectomy syndrome after
  conservative therapy failure. Pulls Kapural et al. 2016 RCT data on SCS efficacy.
- *Policy Citation:* Reads Cigna Coverage Policy 0525. Confirms patient meets all criteria:
  documented chronic pain >6 months, failed conservative therapy, no surgical candidacy,
  psychological evaluation completed (adds note to obtain if not on file).
- *Precedent:* Returns IMR cases where Cigna SCS denials based on "conservative therapy
  not exhausted" were overturned when detailed treatment timelines were provided.

**Round 1 — Insurer Defense attack:**

> "Patient's submission documents multiple conservative therapies but does not establish
> a continuous failed-therapy window meeting policy criteria. The PT was completed in
> 2023; current acuity may have changed. Recommend denying pending updated 90-day
> conservative trial documentation."

**Round 2 — Patient revision:**

- Adds 2025-2026 treatment timeline showing continuous opioid management with documented
  dose escalation and side-effect tolerance limits.
- Adds October 2025 attempt at radiofrequency ablation (minimally invasive intervention)
  with <30% relief.
- Notes that Cigna Policy 0525 does not require conservative therapy to be sequential or
  uninterrupted — it requires documented failure, which is present across 4 years.
- Adds the psychological evaluation report (cleared for SCS candidacy, no
  contraindications).

**Round 2 — Insurer Defense second attack:**

> "Trial period requirement under Section IV.C of Policy 0525 requires a temporary
> percutaneous SCS trial before permanent implant. Authorization sought is for permanent
> implant CPT 63685, not trial CPT 63650."

**Round 2 — Patient final response:** Confirms requested authorization is for trial (CPT
63650 as listed in original denial), not permanent implant. Cites the original denial
letter's own CPT code.

**Supervisor synthesis:**

> The denial misapplies Cigna Coverage Policy 0525 in two respects. First, the policy
> requires documented failure of conservative therapy, not continuous failure within a
> rolling 90-day window — the patient has a four-year documented timeline including PT,
> three pharmacologic classes, three rounds of epidural injections, and most recently
> radiofrequency ablation. Second, the procedure requested is the percutaneous trial
> stimulator (CPT 63650), which the denial itself references, not the permanent implant
> (CPT 63685). The trial is the appropriate next diagnostic step under Section IV.B of
> the policy. Comparable cases at California DMHC have been overturned at the IMR level
> at rates exceeding 55%. We request reversal.

### 30-second stage narration

> "Spinal cord stimulator denial — Cigna says conservative therapy not exhausted.
> [Round 1] Our agents pull NACC guidelines, the exact Cigna policy, and find precedent
> overturns. The Insurer Defense agent attacks — says the patient's PT was too long ago.
> [Round 2] The harness pivots to show a four-year continuous treatment timeline. Then
> Insurer Defense attacks again — wrong CPT code. [Round 2 final] The harness catches
> that Cigna's own denial letter cites CPT 63650 — the trial code — so the request
> matches. [verdict] Three rounds of attack survived. This is what 'sophisticated harness'
> actually means."

---

## CASE 3 — Mental Health / Federal Protection (MHPAEA Parity)

**Why this case is the finalist round play:** demonstrates cross-cutting federal protections
that no other team will surface. Mental Health is your #2 diagnosis category at 6,120
cases. The "did you know you have federal protections" moment is emotionally and
legally powerful.

### The denial letter (input to the harness)

```
Anthem Blue Cross
Subject: Residential SUD Treatment Authorization — Adverse Determination
Date: March 22, 2026
Member: [synthetic]
Requested Service: ASAM Level 3.5 — Clinically Managed High-Intensity Residential
                   Treatment for Substance Use Disorder
Duration Requested: 30 days

This letter is to inform you that the requested level of care is not authorized.

Reason: Based on the clinical information provided, your treatment needs can be met at
a lower level of care. ASAM Level 2.1 — Intensive Outpatient Program — is appropriate for
your current presentation. Residential treatment is not medically necessary at this time.

You have completed medically supervised withdrawal management (Level 3.7-WM) and are
clinically stable for transition to outpatient services.

CARC: 50  RARC: N115
```

### Patient clinical context (synthetic)

34-year-old female. Diagnosis: Alcohol Use Disorder, severe (F10.20). Just completed
inpatient medically managed withdrawal (Level 3.7-WM, 5 days). Comorbid PTSD (F43.10),
moderate. Lives alone in an apartment where she previously drank. No supportive sober
network. Prior IOP attempts (2022, 2024) both resulted in relapse within 14 days of
discharge. Treatment team recommends Level 3.5 residential. Anthem's own benefit
documentation: SUD residential covered up to 30 days/year. Medical/surgical residential
(eating disorder, rehabilitation after orthopedic surgery, etc.) covered without quantitative
limits at the same plan tier.

### Expected agent flow

**Round 1 — Patient agents (parallel):**

- *Medical Necessity:* Pulls ASAM Criteria 4th Edition. Patient assessment across the six
  ASAM dimensions yields Level 3.5 indication: high acuity in Dimension 3 (emotional/
  behavioral — active PTSD), Dimension 5 (relapse potential — two recent IOP failures),
  and Dimension 6 (recovery environment — unsafe living situation).
- *Policy Citation:* Reads Anthem's clinical UM guideline for SUD residential. Confirms
  the patient meets the listed criteria.
- *Precedent:* IMR search returns parity-related overturns from 2024-2025 where insurers
  denied SUD residential while approving comparable medical/surgical residential care.

**Round 1 — Insurer Defense attack:**

> "Patient is post-withdrawal, ambulatory, and clinically stable. ASAM Level 2.1 IOP
> meets the standard of care for stabilization after acute withdrawal. The patient has
> not failed IOP in the past 90 days. Residential is not the least restrictive setting."

**Round 2 — Patient revision — and this is where the federal protection surfaces:**

- *Medical Necessity:* Documents that "least restrictive setting" is not the ASAM standard —
  ASAM requires the *appropriate* level of care matched to the six dimensions. Patient's
  Dimension 5 and 6 scores indicate residential is the matched level.
- *Policy Citation:* Surfaces the MHPAEA argument. Anthem's plan covers medical/surgical
  residential care without quantitative day limits and without "least restrictive setting"
  preconditions. Applying these restrictions only to SUD residential constitutes a
  Non-Quantitative Treatment Limitation (NQTL) parity violation under the federal Mental
  Health Parity and Addiction Equity Act.
- *Precedent:* Surfaces 2024 DOL enforcement actions against insurers for MHPAEA NQTL
  violations on SUD residential. Cites Wit v. United Behavioral Health (9th Cir. 2023)
  establishing that generic medical necessity criteria more restrictive than generally
  accepted standards constitute parity violations.

**Round 2 — Insurer Defense second attack:**

> "MHPAEA NQTL analysis is the insurer's burden, not the patient's. Denial stands on
> medical necessity grounds independent of parity analysis."

**Round 2 — Patient final response:** Argues that under 29 CFR 2590.712(c)(4), the plan
must demonstrate that any NQTL applied to mental health/SUD benefits is comparable to and
applied no more stringently than NQTLs applied to medical/surgical benefits. This patient's
denial citing "least restrictive setting" — a criterion absent from the plan's medical/
surgical residential coverage — is prima facie evidence of NQTL disparity. The patient is
not required to prove the violation; the plan must prove compliance.

**Supervisor synthesis:**

> This appeal rests on both clinical and federal legal grounds. Clinically, the patient
> meets ASAM Level 3.5 residential criteria across Dimensions 3, 5, and 6. ASAM's standard
> is appropriate level of care, not "least restrictive setting" — applying a least-
> restrictive framework conflicts with the published ASAM Criteria 4th Edition that Anthem
> references in its own policy. Legally, applying admission criteria to substance use
> residential care that are not applied to medical/surgical residential care is a
> Non-Quantitative Treatment Limitation under the Mental Health Parity and Addiction
> Equity Act. Under 29 CFR 2590.712, the plan bears the burden of demonstrating NQTL
> comparability. We request immediate authorization for 30 days of ASAM Level 3.5
> residential treatment. If denied, this case will be escalated to the Department of Labor
> for MHPAEA enforcement review and to California DMHC for IMR, where comparable parity
> challenges have been resolved in the patient's favor.

### 30-second stage narration

> "Anthem denied 30 days of residential SUD treatment for a patient post-withdrawal — said
> outpatient is enough. [Round 1] Our agents pull ASAM criteria — patient meets Level 3.5
> across three dimensions. [Insurer Defense] But the critic argues 'least restrictive
> setting.' [Round 2] Here's where it gets interesting. Our harness surfaces the Mental
> Health Parity Act — Anthem doesn't apply this restriction to medical residential care,
> only to addiction residential. That's a federal NQTL violation. [verdict] The patient
> didn't know this. Most patients never do. The harness found a federal protection that
> shifts the burden of proof to the insurer. This is what we mean when we say a real
> appeal isn't a letter — it's an argument."

---

## Stage logistics

**Choreography decision:**
- **Round 1 (panel, 3 minutes):** Lead with Case 1 (Oscar Cromolyn). It's real, has the
  cleanest narrative, and demonstrates the round-based revision pattern most visibly.
- **Finalist round (full room, 3 minutes):** Switch to Case 3 (MHPAEA parity). The
  federal-protection moment lands harder with a larger audience and the legal angle
  separates you from every other team's "AI helped me with X" demo.
- **Case 2 (spinal cord stimulator)** is held in reserve. Use it if (a) the parquet eval
  set needs a quick demo example pulled from the modal pattern in your data, or (b) Case 1
  has a technical issue during the live demo.

**Pre-load each case as a JSON file** at `data/demo/case_01_oscar_cromolyn.json`,
`data/demo/case_02_spinal_cord_stimulator.json`, `data/demo/case_03_mhpaea_parity.json`.
At demo time, select which to run from a dropdown in the web UI. Never type during the
demo. Click-to-run only.

**Backup plan if voice/web fails:** record one successful run of each case to MP4 on
Saturday night. Keep on phone and laptop. If anything breaks during live demo, switch to
the recording mid-sentence without acknowledging the issue.

**The reusable closing line for all three cases:**
> "Built on LangGraph for orchestration, MCP for agent isolation, Claude for adversarial
> reasoning, and W&B Weave for the entire harness. Adversarial self-play with a judge —
> a pattern from AlphaGo applied to appeal quality. Three rounds, four specialized agents,
> one decision."

**The line worth memorizing for Q&A:**
> "We evaluated against 162 cases stratified from 42,749 real California DMHC Independent
> Medical Review decisions. Our harness's job is to match or beat the 54% baseline
> overturn rate while a single-agent baseline produces generic appeals."
