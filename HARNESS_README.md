# Denial Defense - Multi-Agent Insurance Appeal Harness

## Quick Start

### 1. Set up environment variables

```bash
cp .env.example .env
# Edit .env and add your API keys
```

Required:
- `OPENAI_API_KEY` - Get from https://platform.openai.com/api-keys
- `WANDB_API_KEY` - Get from https://wandb.ai/authorize

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Test individual components

**Test baseline (single-agent):**
```bash
python agents/baseline.py
```
Expected: Generates an appeal letter + Weave trace appears

**Test harness (multi-agent):**
```bash
python agents/harness.py
```
Expected: Runs Case 1 through 2 rounds + final verdict

### 4. Run the web UI

```bash
python web/app.py
```

Open http://localhost:5000 in your browser. Click one of the three demo cases to run the harness.

### 5. Run evaluation (optional)

Compare baseline vs harness on 30 IMR cases:

```bash
python eval/compare_eval.py
```

**Warning:** This takes 30-60 minutes. Results appear in Weave dashboard at https://wandb.ai/denial-defense

## Architecture

**Pattern:** Supervisor-worker with adversarial critic and round-based revision

**Flow:**
1. Supervisor kicks off Round 1
2. Three patient agents run in PARALLEL:
   - Medical Necessity (clinical evidence)
   - Policy Citation (exact criteria match)
   - Precedent (CA DMHC IMR cases)
3. Adversarial Critic attacks the weakest claim
4. Patient agents revise (Round 2) addressing critique
5. Critic attacks again
6. Supervisor synthesizes final verdict

**Key files:**
- `agents/prompts.py` - All system prompts (tune here!)
- `agents/baseline.py` - Single-agent baseline
- `agents/harness.py` - Multi-agent LangGraph orchestrator
- `web/app.py` - Flask web UI
- `eval/compare_eval.py` - Weave evaluation

## Demo Cases

1. **Oscar Health — Cromolyn for MCAS**
   - Pharmacy denial (experimental treatment)
   - ICD-10 mismatch (MCAS vs systemic mastocytosis)
   - Pivot: policy plain-meaning interpretation

2. **Cigna — Spinal Cord Stimulator**
   - DME denial (not medically necessary)
   - Step therapy documentation
   - Pivot: chronic pain guideline citations

3. **Anthem — MHPAEA Parity**
   - Mental health denial (not medically necessary)
   - Federal law violation (MHPAEA)
   - Pivot: state parity law + precedent

## Acceptance Criteria

- ✅ `python agents/baseline.py` produces appeal + Weave trace
- ✅ `python agents/harness.py` completes in <90 sec with final verdict
- ✅ Weave shows call tree: supervisor → 3 agents parallel → critic → round 2 → critic → synthesis
- ✅ `python web/app.py` starts Flask on port 5000
- ✅ Browser shows 3 case buttons, each runs harness end-to-end
- ✅ `python eval/compare_eval.py` runs 30 cases and posts to Weave

## Troubleshooting

**LangGraph parallel fan-out issues?**
→ Simplify to sequential if needed (doesn't affect demo)

**JSON parsing fails?**
→ Prompts use `response_format={"type": "json_object"}` to force valid JSON

**Demo takes >2 min?**
→ Reduce `max_tokens` to 1000 in `harness.py` for speed

**Weave eval slow?**
→ Drop sample size from 30 to 15 in `compare_eval.py`

## Tech Stack

- **LLM:** OpenAI GPT-4o (gpt-4o-mini for eval scorer only)
- **Orchestration:** LangGraph with explicit StateGraph
- **Observability:** W&B Weave (project: denial-defense)
- **Web UI:** Flask + vanilla JS (no build step)
- **Eval:** weave.Evaluation API with adversarial scorer

## Next Steps (Post-Demo)

- Add MCP server integration for real-time IMR precedent lookup
- Add streaming token display in web UI
- Add voice integration (Twilio)
- Add authentication for multi-user deployment
- Expand eval to full 162-case stratified set
