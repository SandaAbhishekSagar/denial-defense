# Denial Defense

**Multi-agent AI system that writes insurance appeal letters using adversarial revision.**

We're open-sourcing this tonight because Americans shouldn't need a developer in the family to navigate their insurance.

---

## The Problem

Insurance companies deny necessary medical treatments. Patients write appeals, but don't know what arguments work, relevant legal precedent, or how to counter insurer objections.

**Result:** 99% of denied claims are never appealed. [(KFF, 2023)](https://www.kff.org/private-insurance/issue-brief/claims-denials-and-appeals-in-aca-marketplace-plans/)

---

## Our Solution

A multi-agent AI system that generates appeal letters **already battle-tested against adversarial attacks**.

### Architecture

**5 AI agents working in 2 rounds:**

1. **Round 1 (Parallel):**
   - Medical Necessity Agent → Clinical evidence
   - Policy Citation Agent → Criteria matching
   - Precedent Agent → IMR case law

2. **Adversarial Critic:**
   - Simulates insurer's medical reviewer
   - Attacks the weakest argument

3. **Round 2 (Revision):**
   - Agents revise to address critique
   - Critic attacks again

4. **Supervisor:**
   - Synthesizes final appeal from strongest arguments

**The letter you get is a third draft that already survived two attacks.**

![LangGraph trace map — parallel agents, critic, and supervisor rounds](prompts/pitch_asserts/map.png)

Each run is fully traced in W&B Weave: three patient agents fan out in parallel, the insurer critic attacks, agents revise, and the supervisor synthesizes the final appeal.

---

## Proof: Multi-Agent Wins on All Metrics

We evaluated both systems on **25 real California DMHC denial cases** using 4 independent scorers.

![Evaluation Comparison](prompts/pitch_asserts/eval_v2_comparison.png)

**Results:**

| Metric | Baseline (single-agent) | Harness (multi-agent) | Improvement |
|---|---|---|---|
| **Citation Quality** | 87% have citations (1.84 avg) | **100%** have citations (2.36 avg) | **+28%** citations |
| **Federal Protections** | 100% invoke (1.04 avg) | 96% invoke (1.16 avg) | +12% protections |
| **Addresses Denial** | 100% (2.8/3 directness) | 100% (2.88/3 directness) | +3% directness |
| **Latency** | 7.1s | 42.4s | 6x slower (5 agents × 2 rounds) |

The multi-agent system produces appeals with **measurably stronger clinical evidence** and better legal grounding.

---

## Quick Start

### Prerequisites
- Python 3.9+
- OpenAI API key
- Weights & Biases account (free)

### Install

```bash
git clone https://github.com/SandaAbhishekSagar/denial-defense.git
cd denial-defense
pip install -r requirements.txt
```

### Configure

```bash
# Create .env file
cp .env.example .env

# Add your API keys to .env
OPENAI_API_KEY=your_openai_key_here
WANDB_API_KEY=your_wandb_key_here
```

### Run Demo

```bash
python web/app.py
# Open http://localhost:5000
```

**Try it:**
1. Toggle "Show side-by-side comparison" ON
2. Click "Oscar Health — Cromolyn for MCAS"
3. See baseline (left) vs harness (right) after ~25 seconds

---

## Demo Cases

Three real denial scenarios:

1. **Oscar Health — Cromolyn for MCAS**  
   Pharmacy denial for mast cell activation syndrome treatment

2. **Cigna — Spinal Cord Stimulator Trial**  
   Medical necessity denial for chronic pain management device

3. **Anthem — Residential SUD with MHPAEA Parity**  
   Mental health parity violation for substance use disorder treatment

---

## Key Features

### 1. Adversarial Revision Loop
Unlike ChatGPT/Claude (single draft), our system:
- ✅ Generates draft
- ✅ Attacks it (adversarial critic)
- ✅ Revises based on critique
- ✅ Attacks again
- ✅ Synthesizes strongest arguments

### 2. Observability with Weave
Every agent call tracked in W&B Weave:
- View trace hierarchy
- Compare baseline vs harness
- See round-by-round evolution

### 3. Side-by-Side Comparison UI
Toggle comparison mode to see:
- Baseline (1 agent, 0 rounds) — generic template
- Harness (5 agents, 2 rounds) — specific clinical citations

### 4. Metrics Display
Real-time metrics bar shows:
- ⏱ Elapsed time
- 🎯 CARC codes matched (e.g., 50, 167, 252)
- ⚖ Federal protections detected (MHPAEA, No Surprises Act)
- 🔁 Revision rounds completed
- 💬 Adversarial critiques generated

---

## Technical Stack

- **Orchestration:** LangGraph (parallel execution, state management)
- **LLM:** OpenAI GPT-4o (agents), W&B Inference gpt-oss-120b (scorers)
- **Observability:** W&B Weave
- **Backend:** Flask
- **Frontend:** Vanilla JS (no framework)
- **Data:** 162-case stratified eval set from CA DMHC IMR precedents

---

## Project Structure

```
denial-defense/
├── agents/
│   ├── baseline.py         # Single-agent comparison
│   ├── harness.py          # Multi-agent orchestrator (LangGraph)
│   ├── prompts.py          # System prompts for all 6 agents
│   └── playbook.py         # CARC denial codes + federal protections
├── data/
│   ├── demo/               # 3 demo cases (JSON)
│   └── processed/          # Denial playbook (10 CARC codes)
├── eval/
│   └── compare_eval.py     # Weave evaluation script (n=25, 4 scorers)
├── web/
│   ├── app.py              # Flask backend
│   └── templates/          # UI with comparison mode
└── requirements.txt
```

---

## Evaluation Details

**Dataset:** 25 real California Independent Medical Review (IMR) denial cases  
**Scorers:** 4 metrics (citation quality, federal protections, directness, adversarial robustness)  
**Infrastructure:** OpenAI GPT-4o for agents, W&B Inference for scorers  
**Results:** View full traces at [wandb.ai/sabhisheksagar200-northeastern-university/denial-defense/weave](https://wandb.ai/sabhisheksagar200-northeastern-university/denial-defense/weave)

---

## Limitations

### What This System Does
✅ Generates structured appeal arguments with clinical evidence  
✅ Cites policy criteria and IMR precedent  
✅ Identifies federal protections (MHPAEA, ACA 1557, No Surprises Act)  
✅ Simulates adversarial review before submission

### What This System Doesn't Do
❌ Replace medical or legal advice  
❌ Guarantee appeal success (real overturn rates vary 40-60%)  
❌ Access patient medical records automatically  
❌ Submit appeals directly to insurers

**This is a research prototype.** Appeals generated should be reviewed by qualified professionals before submission.

---

## Contributing

We welcome contributions! Areas of interest:
- Additional state-specific denial playbooks
- Improved regex patterns for CARC code matching
- UI/UX enhancements
- Evaluation on larger case sets

---

## Citation

If you use this work, please cite:

```bibtex
@software{denial_defense_2026,
  title = {Denial Defense: Multi-Agent AI for Insurance Appeal Letters},
  author = {Sagar, Abhishek},
  year = {2026},
  url = {https://github.com/SandaAbhishekSagar/denial-defense}
}
```

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## Contact

**Author:** Abhishek Sagar  
**Email:** sabhisheksagar200@gmail.com  
**Demo:** [http://localhost:5000](http://localhost:5000) (after running locally)

---

**Built in 8 hours on Sunday, May 31, 2026.**  
**Evaluation shows multi-agent system produces 28% more clinical citations.**  
**We're open-sourcing this because healthcare access shouldn't require technical expertise.**
