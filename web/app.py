"""
Flask web UI for Denial Defense multi-agent harness.

Simple single-page app with three demo case buttons.
Displays round-by-round agent outputs and final verdict.
"""

from flask import Flask, render_template, request, jsonify
import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.harness import run_harness
from agents.baseline import single_agent_appeal

app = Flask(__name__, template_folder="templates")

# Load demo cases
DEMO_DIR = Path(__file__).parent.parent / "data" / "demo"
CASES = {}
for case_file in DEMO_DIR.glob("case_*.json"):
    try:
        case_data = json.load(open(case_file))
        CASES[case_file.stem] = case_data
    except Exception as e:
        print(f"Warning: Could not load {case_file}: {e}")

print(f"Loaded {len(CASES)} demo cases: {list(CASES.keys())}")


@app.route("/")
def index():
    """Main page with case selector."""
    return render_template("index.html", cases=CASES)


@app.route("/run/<case_id>", methods=["POST"])
def run_case(case_id):
    """
    Run the harness on a specific demo case.
    Returns structured JSON with all round outputs.
    """
    if case_id not in CASES:
        return jsonify({"status": "error", "message": f"Case '{case_id}' not found"}), 404
    
    case = CASES[case_id]
    
    try:
        # Run the multi-agent harness
        result = run_harness(
            denial_letter=case["denial_letter"]["denial_text"],
            patient_context=json.dumps(case["patient_context"], indent=2)
        )
        
        # Structure response for UI
        return jsonify({
            "status": "ok",
            "case_name": case["display_name"],
            "denial": case["denial_letter"],
            "patient_context": case["patient_context"],
            "round_1": {
                "medical_necessity": result.get("medical_necessity", {}),
                "policy_citation": result.get("policy_citation", {}),
                "precedent": result.get("precedent", {}),
            },
            "critiques": result.get("critiques", []),
            "final_verdict": result.get("final_verdict", ""),
        })
        
    except Exception as e:
        # Friendly error display
        import traceback
        error_detail = traceback.format_exc()
        print(f"ERROR running case {case_id}:")
        print(error_detail)
        
        return jsonify({
            "status": "error",
            "message": f"Harness failed: {str(e)}",
            "detail": error_detail
        }), 500


@app.route("/compare/<case_id>", methods=["POST"])
def compare_case(case_id):
    """
    Run BOTH baseline and harness on a case for side-by-side comparison.
    Returns structured JSON with both results.
    """
    if case_id not in CASES:
        return jsonify({"status": "error", "message": f"Case '{case_id}' not found"}), 404
    
    case = CASES[case_id]
    denial_text = case["denial_letter"]["denial_text"]
    patient_ctx = json.dumps(case["patient_context"], indent=2)
    
    try:
        print(f"\n[COMPARE] Running baseline for {case_id}...")
        baseline_output = single_agent_appeal(denial_text, patient_ctx)
        
        print(f"[COMPARE] Running harness for {case_id}...")
        harness_output = run_harness(denial_text, patient_ctx)
        
        return jsonify({
            "status": "ok",
            "denial": case["denial_letter"],
            "baseline": {
                "appeal_letter": baseline_output,
                "agents_used": 1,
                "rounds": 0,
                "label": "Single-Agent Baseline (what ChatGPT/Claude would produce)"
            },
            "harness": {
                "round_1": {
                    "medical_necessity": harness_output.get("medical_necessity", {}),
                    "policy_citation": harness_output.get("policy_citation", {}),
                    "precedent": harness_output.get("precedent", {}),
                },
                "critiques": harness_output.get("critiques", []),
                "final_verdict": harness_output.get("final_verdict", ""),
                "agents_used": 5,
                "rounds": 2,
                "label": "Multi-Agent Harness with Adversarial Critic"
            }
        })
        
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"ERROR in comparison for {case_id}:")
        print(error_detail)
        
        return jsonify({
            "status": "error",
            "message": f"Comparison failed: {str(e)}",
            "detail": error_detail
        }), 500


@app.route("/cases")
def list_cases():
    """API endpoint: list available cases."""
    return jsonify({
        cid: c["display_name"] 
        for cid, c in CASES.items()
    })


if __name__ == "__main__":
    # Verify API keys
    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY environment variable required")
        sys.exit(1)
    
    print("=" * 80)
    print("Denial Defense - Multi-Agent Insurance Appeal Harness")
    print("=" * 80)
    print(f"Available cases: {len(CASES)}")
    print("Starting Flask server on http://localhost:5000")
    print("=" * 80)
    
    app.run(host="0.0.0.0", port=5000, debug=False)
