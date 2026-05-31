# IMR Reviewer Language Patterns

Based on sampling findings from the evaluation set, here are the key patterns in how IMR reviewers write their determinations:

## Common Opening Phrases

### Medical Necessity Cases
- "Nature of Statutory Criteria/Case Summary: The patient has requested..."
- "On review of the current medical records, the requested [treatment] is not supported..."
- "The Clinical Practice Guidelines for [specialty] support that..."

### Experimental/Investigational Cases
- "Findings: The physician reviewer found that..."
- "Nature of Statutory Criteria/Case Summary: An enrollee has requested..."
- "The current peer-reviewed medical literature supports..."
- Heavy emphasis on "lack of large-scale, long-term peer-reviewed literature"

### Urgent Care Cases
- Focus on whether the condition was "acute onset" vs. chronic
- Emphasize whether services were "emergent" or could have been delayed
- Compare actual treatment to "appropriate emergency care" standards

## Key Structural Elements

### 1. Medical Necessity Denials
**Pattern**: 
- State the request
- Reference clinical guidelines (ASAM, FDA, specialty-specific)
- Document what criteria were NOT met
- Note what alternative treatments should be tried first
- Conclude with "not medically necessary"

**Example phrases**:
- "Per ASAM criteria, this patient doesn't meet Level 3.5 criteria..."
- "The records indicate that... [specific deficiency]"
- "While the patient may benefit from therapy, given that..."
- "There is a lack of documentation to support..."

### 2. Experimental/Investigational Denials
**Pattern**:
- Acknowledge what literature exists
- Emphasize limitations: "limited large-scale," "absence of randomized," "lack of long-term outcomes"
- Note lack of FDA approval or guideline support
- Conclude experimental/investigational

**Example phrases**:
- "The current peer-reviewed medical literature supports... [BUT]"
- "There remains an absence of randomized, blinded clinical studies..."
- "Limited large-scale, long-term references showing safety and efficacy..."
- "The requested [treatment] is considered experimental/investigational"

### 3. Urgent Care Denials
**Pattern**:
- Define what constitutes "urgent/emergent"
- Contrast patient's timeline with emergency criteria
- Note whether condition could wait for scheduled care
- Conclude whether truly urgent

**Example phrases**:
- "This was noted to be an emergency operation as... However, this was not an acute onset..."
- "When oral analgesics have failed, the next step involves..."
- "Given this patient's severe pain, other treatment options could have included..."

## Citation Patterns

### Strong Citations (Support Denial)
- "The American Association of Clinical Endocrinologists (AACE) guidelines state..."
- "According to the American College of Rheumatology/Arthritis Foundation guideline..."
- "The FDA approves [medication] for [indication A] but not for [indication B]..."
- "Researchers explain, '[direct quote]'..."

### Weak Spots (Could Support Overturn)
- "While [treatment] may be beneficial..." (acknowledges benefit but denies anyway)
- "The patient may continue to benefit from therapy..." (acknowledges ongoing need)
- "Given [patient's condition], other treatment options could have included..." (acknowledges alternatives exist)

## Denial Reasoning Hierarchy

### Tier 1: Absolute (Hardest to Overturn)
1. "Does not meet diagnostic criteria" (e.g., height z-score above threshold)
2. "FDA not approved for this indication"
3. "Considered experimental/investigational - no RCTs"

### Tier 2: Procedural (Can Challenge)
1. "Failed to try conservative measures first"
2. "Lack of documentation" (could provide documentation)
3. "Alternative treatment available" (could argue alternatives failed/contraindicated)

### Tier 3: Discretionary (Easiest to Challenge)
1. "May benefit but not medically necessary" (subjective determination)
2. "Limited large-scale literature" (cite smaller studies, case series)
3. "Patient preference" vs. medical necessity (could argue medical justification)

## Language for Appeal Drafting

When the Precedent agent surfaces similar cases, look for:
1. **Exact guideline citations** - cite same guidelines with different interpretation
2. **Studies mentioned** - find more recent studies or counter-studies
3. **Criteria checklists** (ASAM dimensions, FDA criteria) - systematically address each
4. **Alternative treatments mentioned** - document why alternatives failed/contraindicated
5. **"May benefit but..."** language - challenge the "but" with clinical evidence

## Red Flags in Reviewer Language

These phrases signal vulnerable denials (good overturn candidates):
- "While [treatment] may be beneficial..."
- "The patient may continue to benefit..."
- "Limited [but not zero] literature..."
- "Considering [positive factor] but..."
- "Given [valid clinical reason], other options could have..."

These signal strong denials (harder to overturn):
- "Does not meet FDA-approved criteria"
- "Absence of randomized controlled trials"
- "No documented trial of [standard treatment]"
- "Does not meet diagnostic threshold" (with specific numbers)

## Practical Use for Agents

### Precedent Agent
- Match on: DiagnosisCategory + TreatmentCategory + Type
- Surface: Findings field (2-4k characters of reviewer reasoning)
- Extract: Specific guideline citations, studies mentioned, criteria lists

### Medical Necessity Agent  
- Parse ASAM dimensions, FDA criteria from Findings
- Identify which dimension/criterion failed
- Generate evidence to satisfy that specific criterion

### Insurer Defense Agent
- Parse for plan language: "not covered," "not medically indicated," "experimental"
- Extract reviewer's medical reasoning to counter with clinical evidence
- Note cited guidelines to show plan's own guidelines support coverage

---

**Key Insight**: Reviewers follow rigid templates. The Findings field is structured gold for agent prompts because it reveals:
1. Exactly which criteria failed
2. Which guidelines they're applying
3. What evidence they found lacking
4. What alternatives they think should be tried first

This makes IMR cases **ideal for precedent-based prompting** - you can show the agent "here's how a reviewer analyzed a similar case" and generate appeals that directly address the reviewer's framework.
