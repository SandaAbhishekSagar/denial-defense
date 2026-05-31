"""
Baseline single-agent appeal system for comparison.

Architecture: Simple single-call GPT-4o with no revision loop.
This establishes the baseline performance for the Weave evaluation.
"""

import json
import os
import sys
import io
from pathlib import Path
from openai import OpenAI
import weave
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Fix Unicode output on Windows
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        if hasattr(sys.stderr, 'buffer') and sys.stderr.buffer is not None:
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except (ValueError, AttributeError):
        # Already wrapped or redirected, skip
        pass

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.prompts import BASELINE_SYSTEM

# Security: assert API keys exist
assert os.getenv("OPENAI_API_KEY"), "OPENAI_API_KEY environment variable required"

# Initialize
client = OpenAI()
weave.init("denial-defense")


@weave.op()
def single_agent_appeal(denial_synopsis: str, patient_context: str) -> str:
    """
    Single-agent baseline: one GPT-4o call produces the entire appeal.
    
    Args:
        denial_synopsis: Summary of the denial (diagnosis, treatment, reason)
        patient_context: Patient's clinical details and history
        
    Returns:
        Complete appeal letter as plain text
    """
    
    user_message = f"""DENIAL INFORMATION:
{denial_synopsis}

PATIENT CONTEXT:
{patient_context}

Write a complete insurance appeal letter addressing this denial."""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            max_tokens=2000,
            temperature=0.7,
            messages=[
                {"role": "system", "content": BASELINE_SYSTEM},
                {"role": "user", "content": user_message}
            ]
        )
        
        appeal_text = response.choices[0].message.content
        
        # Log token usage
        usage = response.usage
        print(f"[Baseline] Tokens: {usage.total_tokens} (prompt: {usage.prompt_tokens}, completion: {usage.completion_tokens})")
        
        return appeal_text
        
    except Exception as e:
        error_msg = f"Baseline agent failed: {str(e)}"
        print(f"ERROR: {error_msg}")
        return f"[Error generating appeal: {error_msg}]"


def main():
    """Test the baseline agent with a sample case."""
    
    # Test case
    denial_synopsis = """
Type: Medical Necessity
Diagnosis: Morbid Obesity (BMI 42, hypertension, diabetes)
Treatment: Bariatric surgery (gastric sleeve)
Denial Reason: Patient does not meet Class I obesity criteria (BMI 30-35 with comorbidities). 
Policy requires BMI 35-40 with major comorbidities OR BMI 40+ for coverage.
Insurer argues patient is Class II obesity and standard treatment is lifestyle modification first.
"""
    
    patient_context = """
Patient is a 45-year-old with:
- BMI 42 (qualifying as Class II/III obesity)
- Type 2 diabetes (HbA1c 8.2% despite metformin + insulin)
- Hypertension (on 3 medications, BP 145/95)
- Obstructive sleep apnea (requires CPAP)
- Failed lifestyle modification: 2-year supervised diet program, lost 15 lbs then regained 20 lbs
- Endocrinologist letter supporting bariatric surgery as medically necessary
"""
    
    print("=" * 80)
    print("TESTING BASELINE SINGLE-AGENT APPEAL")
    print("=" * 80)
    print()
    
    appeal = single_agent_appeal(denial_synopsis, patient_context)
    
    print()
    print("=" * 80)
    print("GENERATED APPEAL:")
    print("=" * 80)
    print(appeal)
    print()
    print("=" * 80)
    print("✓ Baseline test complete. Check Weave dashboard for trace.")
    print("=" * 80)


if __name__ == "__main__":
    main()
