"""
Weave evaluation: compare baseline single-agent vs multi-agent harness.

Runs both systems on sampled IMR cases and compares performance using
4 scorers (W&B Inference gpt-oss-120b) while agents stay on OpenAI gpt-4o.

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

# Limit parallelism to avoid W&B Inference rate limits (default is 20).
# Must be set BEFORE weave.init() — Weave reads it at startup.
os.environ.setdefault("WEAVE_PARALLELISM", "20")

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

# Initialize — OpenAI for baseline/harness agents (DO NOT CHANGE)
client = OpenAI()

# W&B Inference for scorers only
wandb_scorer_client = OpenAI(
    base_url="https://api.inference.wandb.ai/v1",
    api_key=os.getenv("WANDB_API_KEY"),
    default_headers={
        "OpenAI-Project": "sabhisheksagar200-northeastern-university/denial-defense"
    },
)

SCORER_MODEL = "openai/gpt-oss-120b"

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
        response = wandb_scorer_client.chat.completions.create(
            model=SCORER_MODEL,
            response_format={"type": "json_object"},
            max_tokens=800,
            temperature=0.3,
            timeout=60,
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
        
        raw = response.choices[0].message.content
        if raw is None:
            raise ValueError("W&B Inference returned None content")
        result = json.loads(raw)
        
        # Weave scorers should return a dict with a "score" key
        return {
            "survives": result.get("survives", False),
            "weak_points": result.get("weak_points", []),
            "reasoning": result.get("reasoning", ""),
            "score": 1.0 if result.get("survives", False) else 0.0
        }

    except json.JSONDecodeError as e:
        print(f"[survives_attack_scorer] JSON parse failed: {e}")
        return {
            "survives": False,
            "weak_points": ["json_parse_failed"],
            "reasoning": "Scorer JSON parse error",
            "score": 0.0,
        }
    except Exception as e:
        print(f"ERROR in scorer: {e}")
        return {
            "survives": False,
            "weak_points": [f"Scorer error: {str(e)}"],
            "reasoning": "Error during evaluation",
            "score": 0.0
        }


@weave.op()
def cites_specific_evidence_scorer(output: str, denial_synopsis: str) -> dict:
    """Counts specific clinical citations in the appeal."""
    if not output or not isinstance(output, str):
        return {"specificity_score": 0, "citations_found": []}

    try:
        resp = wandb_scorer_client.chat.completions.create(
            model=SCORER_MODEL,
            response_format={"type": "json_object"},
            max_tokens=800,
            timeout=60,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You evaluate insurance appeal letters for citation specificity. "
                        "Count distinct citations to: (a) named clinical guideline bodies "
                        "(ASMBS, AAAAI, ACR, NCCN, ASAM, WPATH, ECNM, APA, ACOG, ADA, etc.), "
                        "(b) peer-reviewed studies with author names and years (e.g., 'Akin et al. 2020'), "
                        "(c) specific policy criteria cited verbatim. "
                        "Return JSON: {\"citations_found\": [\"list of citations\"], "
                        "\"specificity_score\": <integer count>, \"has_specific_citations\": true|false}"
                    ),
                },
                {"role": "user", "content": f"APPEAL: {output[:3000]}"},
            ],
        )
        raw = resp.choices[0].message.content
        if raw is None:
            raise ValueError("W&B Inference returned None content")
        result = json.loads(raw)
        result["specificity_score"] = int(result.get("specificity_score", 0))
        return result
    except json.JSONDecodeError as e:
        print(f"[cites_specific_evidence_scorer] JSON parse failed: {e}")
        return {"specificity_score": 0, "citations_found": [], "error": "json_parse_failed"}
    except Exception as e:
        print(f"[cites_specific_evidence_scorer] LLM call failed: {e}")
        return {"specificity_score": 0, "citations_found": [], "error": str(e)}


@weave.op()
def invokes_federal_protections_scorer(output: str, denial_synopsis: str) -> dict:
    """Detects invocation of federal patient protections."""
    if not output or not isinstance(output, str):
        return {"protections_invoked": [], "protection_count": 0, "invokes_any": False}

    output_lower = output.lower()
    protections = {
        "MHPAEA": ["mhpaea", "mental health parity", "parity act", "addiction equity"],
        "ACA": ["affordable care act", "aca", "essential health benefits"],
        "ACA_1557": ["section 1557", "1557", "nondiscrimination"],
        "ERISA": ["erisa", "29 cfr 2560", "full and fair review"],
        "NSA": ["no surprises act", "nsa", "surprise billing", "balance billing"],
        "ADA": ["americans with disabilities act", "ada accommodation"],
    }

    found = []
    for name, keywords in protections.items():
        if any(kw in output_lower for kw in keywords):
            found.append(name)

    return {
        "protections_invoked": found,
        "protection_count": len(found),
        "invokes_any": len(found) > 0,
    }


@weave.op()
def addresses_denial_reason_scorer(output: str, denial_synopsis: str) -> dict:
    """Evaluates whether the appeal directly addresses the denial reason."""
    if not output or not isinstance(output, str):
        return {"addresses_reason": False, "directness_score": 0}

    try:
        resp = wandb_scorer_client.chat.completions.create(
            model=SCORER_MODEL,
            response_format={"type": "json_object"},
            max_tokens=600,
            timeout=60,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You evaluate whether an insurance appeal directly addresses the specific "
                        "denial reason in the original denial letter. "
                        "Score 0-3: 0 = doesn't address denial reason, 1 = vague reference, "
                        "2 = addresses but lacks specificity, 3 = directly counters with specific evidence. "
                        "Return JSON: {\"directness_score\": 0|1|2|3, "
                        "\"addresses_reason\": true|false, \"reasoning\": \"brief explanation\"}"
                    ),
                },
                {
                    "role": "user",
                    "content": f"DENIAL REASON: {denial_synopsis[:1000]}\n\nAPPEAL: {output[:2500]}",
                },
            ],
        )
        raw = resp.choices[0].message.content
        if raw is None:
            raise ValueError("W&B Inference returned None content")
        result = json.loads(raw)
        result["directness_score"] = int(result.get("directness_score", 0))
        result["addresses_reason"] = bool(result.get("addresses_reason", False))
        return result
    except json.JSONDecodeError as e:
        print(f"[addresses_denial_reason_scorer] JSON parse failed: {e}")
        return {"directness_score": 0, "addresses_reason": False, "error": "json_parse_failed"}
    except Exception as e:
        print(f"[addresses_denial_reason_scorer] LLM call failed: {e}")
        return {"directness_score": 0, "addresses_reason": False, "error": str(e)}


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
    print("Baseline: Single-agent GPT-4o (OpenAI)")
    print("Harness: Multi-agent with adversarial critic (OpenAI gpt-4o)")
    print(f"Scorers: 4 metrics via W&B Inference ({SCORER_MODEL})")
    print("=" * 80)
    print()

    ds = build_dataset(n_samples=25)

    all_scorers = [
        survives_attack_scorer,
        cites_specific_evidence_scorer,
        invokes_federal_protections_scorer,
        addresses_denial_reason_scorer,
    ]

    print(f"[{datetime.now().isoformat()}] Starting n=25 eval, scorer model: {SCORER_MODEL}")

    baseline_eval = weave.Evaluation(
        dataset=ds,
        scorers=all_scorers,
        name="baseline_single_agent_n25_wandb_scorer",
    )
    baseline_summary = await baseline_eval.evaluate(baseline_system)
    print(f"Baseline summary: {baseline_summary}")

    harness_eval = weave.Evaluation(
        dataset=ds,
        scorers=all_scorers,
        name="multi_agent_harness_n25_wandb_scorer",
    )
    harness_summary = await harness_eval.evaluate(harness_system)
    print(f"Harness summary: {harness_summary}")

    print("\n" + "=" * 80)
    print("BOTH EVALS COMPLETE — n=100, 4 scorers, W&B Inference")
    print("=" * 80)
    print("Compare on Weave dashboard:")
    print("  baseline_single_agent_n25_wandb_scorer vs multi_agent_harness_n25_wandb_scorer")
    print("https://wandb.ai/sabhisheksagar200-northeastern-university/denial-defense/weave")
    print("=" * 80)


# ============================================================================
# MAIN
# ============================================================================

def test_wandb_inference() -> bool:
    """Verify W&B Inference is reachable BEFORE running full eval."""
    print("Testing W&B Inference connection...")
    try:
        resp = wandb_scorer_client.chat.completions.create(
            model=SCORER_MODEL,
            max_tokens=50,
            messages=[
                {"role": "user", "content": "Say 'connection ok' in JSON: {\"status\": \"ok\"}"}
            ],
            response_format={"type": "json_object"},
            timeout=30,
        )
        print(f"W&B Inference reachable: {resp.choices[0].message.content}")
        return True
    except Exception as e:
        print(f"W&B Inference connection failed: {e}")
        return False


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
    if not test_wandb_inference():
        print("ABORT: W&B Inference not reachable. Reverting to OpenAI scorers required.")
        exit(1)
    exit(main())
