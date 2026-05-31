"""
Weave evaluation: compare baseline single-agent vs multi-agent harness.

Runs both systems on 15 sampled IMR cases and compares performance using
an adversarial "survives attack" scorer.

Results appear in the Weave dashboard Evals tab for side-by-side comparison.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import weave
from openai import OpenAI

from agents.baseline import single_agent_appeal
from agents.harness import run_harness

# Security: assert API keys
assert os.getenv("OPENAI_API_KEY"), "OPENAI_API_KEY required"
assert os.getenv("WANDB_API_KEY"), "WANDB_API_KEY required"

# Initialize
client = OpenAI()
weave.init("denial-defense")


# ============================================================================
# MODEL WRAPPERS
# ============================================================================

@weave.op()
def baseline_system(denial_synopsis: str, patient_context: str) -> str:
    """Baseline: single-agent GPT-4o call."""
    return single_agent_appeal(denial_synopsis, patient_context)


@weave.op()
def harness_system(denial_synopsis: str, patient_context: str) -> str:
    """Multi-agent harness with adversarial critic and 2 rounds."""
    try:
        result = run_harness(denial_synopsis, patient_context)
        return result.get("final_verdict", "[No verdict generated]")
    except Exception as e:
        return f"[Harness error: {str(e)}]"


# ============================================================================
# SCORER
# ============================================================================

@weave.op()
def survives_attack_scorer(output: str, denial_synopsis: str) -> dict:
    """
    Adversarial scorer: separate GPT-4o-mini plays insurer reviewer.
    Does the appeal survive a re-attack?
    
    Returns:
        {"survives": bool, "weak_points": [str], "score": 0.0 or 1.0}
    """
    if not output or not isinstance(output, str):
        return {
            "survives": False,
            "weak_points": ["empty or invalid output"],
            "reasoning": "No output to evaluate",
            "score": 0.0
        }
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            max_tokens=400,
            temperature=0.3,
            messages=[
                {
                    "role": "system",
                    "content": """You are an insurance medical reviewer. Read the patient's appeal. 
Identify whether it survives basic adversarial scrutiny. 

Return JSON:
{
  "survives": true or false,
  "weak_points": ["list of specific weaknesses"],
  "reasoning": "brief explanation"
}

Strong appeals have:
- Specific clinical citations (guideline + year, or study author + journal)
- Exact policy criteria matches with documentation
- Clear precedent references

Weak appeals have:
- Vague language ("may be appropriate", "similar to")
- No specific citations
- Missing documentation claims
- Criteria mismatches"""
                },
                {
                    "role": "user",
                    "content": f"DENIAL:\n{denial_synopsis}\n\nPATIENT APPEAL:\n{output}"
                }
            ]
        )
        
        result = json.loads(response.choices[0].message.content)
        
        # Weave scorers should return a dict with a "score" key
        return {
            "survives": result.get("survives", False),
            "weak_points": result.get("weak_points", []),
            "reasoning": result.get("reasoning", ""),
            "score": 1.0 if result.get("survives", False) else 0.0
        }
        
    except Exception as e:
        print(f"ERROR in scorer: {e}")
        return {
            "survives": False,
            "weak_points": [f"Scorer error: {str(e)}"],
            "reasoning": "Error during evaluation",
            "score": 0.0
        }


# ============================================================================
# DATASET PREPARATION
# ============================================================================

def build_dataset(n_samples: int = 15) -> weave.Dataset:
    """
    Load IMR eval set and prepare dataset for Weave evaluation.
    
    Args:
        n_samples: Number of cases to sample (default 15 for faster eval)
        
    Returns:
        Weave Dataset with denial_synopsis and patient_context
    """
    eval_path = Path(__file__).parent.parent / "data" / "processed" / "eval_set_imr.parquet"
    
    if not eval_path.exists():
        raise FileNotFoundError(f"Eval set not found at {eval_path}")
    
    df = pd.read_parquet(eval_path)
    
    # Sample cases - reduced to 15 for faster turnaround
    if len(df) > n_samples:
        df = df.sample(n_samples, random_state=42)
    
    print(f"Loaded {len(df)} cases from eval set")
    
    # Convert to Weave dataset format
    rows = []
    for _, row in df.iterrows():
        # Build denial synopsis from IMR fields
        denial_synopsis = f"""Type: {row['Type']}
Diagnosis Category: {row['DiagnosisCategory']}
Diagnosis Subcategory: {row.get('DiagnosisSubCategory', 'N/A')}
Treatment Category: {row['TreatmentCategory']}
Treatment Subcategory: {row.get('TreatmentSubCategory', 'N/A')}
Determination: {row['Determination']}

IMR Reviewer Findings (excerpt):
{str(row['Findings'])[:400]}..."""
        
        patient_context = f"""Report Year: {row['ReportYear']}
Diagnosis: {row['DiagnosisCategory']} - {row.get('DiagnosisSubCategory', 'N/A')}
Treatment: {row['TreatmentCategory']} - {row.get('TreatmentSubCategory', 'N/A')}"""
        
        rows.append({
            "denial_synopsis": denial_synopsis,
            "patient_context": patient_context
        })
    
    return weave.Dataset(name="imr-eval-sample", rows=rows)


# ============================================================================
# ASYNC EVALUATION
# ============================================================================

async def run_evaluations():
    """Run both baseline and harness evaluations asynchronously."""
    
    print("=" * 80)
    print("DENIAL DEFENSE - COMPARATIVE EVALUATION")
    print("=" * 80)
    print("Baseline: Single-agent GPT-4o")
    print("Harness: Multi-agent with adversarial critic (2 rounds)")
    print("Scorer: Adversarial 'survives attack' test (GPT-4o-mini)")
    print("=" * 80)
    print()
    
    # Prepare dataset once
    print(f"[{datetime.now().isoformat()}] Preparing dataset...")
    ds = build_dataset(n_samples=15)
    print(f"[{datetime.now().isoformat()}] ✓ Dataset ready: {len(ds.rows)} cases")
    print()
    
    # Evaluate baseline
    print("=" * 80)
    print(f"[{datetime.now().isoformat()}] EVALUATING BASELINE (single-agent GPT-4o)")
    print("=" * 80)
    try:
        baseline_eval = weave.Evaluation(
            dataset=ds,
            scorers=[survives_attack_scorer],
            name="baseline_single_agent"
        )
        baseline_summary = await baseline_eval.evaluate(baseline_system)
        print(f"[{datetime.now().isoformat()}] ✓ Baseline evaluation complete")
        print(f"  Summary: {baseline_summary}")
    except Exception as e:
        print(f"ERROR in baseline eval: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    
    # Evaluate harness
    print("=" * 80)
    print(f"[{datetime.now().isoformat()}] EVALUATING HARNESS (multi-agent with critic)")
    print("=" * 80)
    print("This will take 15-20 minutes for 15 cases...")
    print("=" * 80)
    try:
        harness_eval = weave.Evaluation(
            dataset=ds,
            scorers=[survives_attack_scorer],
            name="multi_agent_harness"
        )
        harness_summary = await harness_eval.evaluate(harness_system)
        print(f"[{datetime.now().isoformat()}] ✓ Harness evaluation complete")
        print(f"  Summary: {harness_summary}")
    except Exception as e:
        print(f"ERROR in harness eval: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("=" * 80)
    print(f"[{datetime.now().isoformat()}] ✓ BOTH EVALUATIONS COMPLETE")
    print("=" * 80)
    print("Visit Weave dashboard → Evals tab → see side-by-side comparison")
    print("https://wandb.ai/sabhisheksagar200-northeastern-university/denial-defense/weave")
    print("=" * 80)


# ============================================================================
# MAIN
# ============================================================================

def main() -> int:
    """Main entry point with async execution."""
    try:
        asyncio.run(run_evaluations())
        return 0
    except KeyboardInterrupt:
        print("\n\nEvaluation interrupted by user")
        return 1
    except Exception as e:
        print(f"\nEvaluation failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
