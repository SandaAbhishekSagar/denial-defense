"""
Multi-agent insurance appeal harness with adversarial critic.

Architecture: Supervisor-worker with adversarial critic and round-based revision.
Three patient agents work in parallel. The critic has no external tools, only 
adversarial reasoning, simulating an insurer's internal medical reviewer.

Flow:
1. Supervisor kicks off Round 1
2. Three patient agents run in PARALLEL (Medical Necessity, Policy Citation, Precedent)
3. Critic attacks the weakest claim
4. Patient agents revise (Round 2) addressing the critique
5. Critic attacks again
6. Supervisor synthesizes final verdict

Hard cap at 2 rounds to prevent infinite loops.
"""

import json
import os
import sys
import io
from pathlib import Path
from typing import Annotated, TypedDict
from operator import add
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

from langgraph.graph import StateGraph, END
from openai import OpenAI
import weave

from agents.prompts import (
    MEDICAL_NECESSITY_SYSTEM,
    POLICY_CITATION_SYSTEM,
    PRECEDENT_SYSTEM,
    INSURER_DEFENSE_SYSTEM,
    SUPERVISOR_SYNTHESIS_SYSTEM,
)
from agents.playbook import Playbook

# Security: assert API keys exist
assert os.getenv("OPENAI_API_KEY"), "OPENAI_API_KEY environment variable required"

# Initialize
client = OpenAI()
weave.init("denial-defense")

# Load playbook
playbook = Playbook.load()


# ============================================================================
# STATE SCHEMA
# ============================================================================

class HarnessState(TypedDict):
    """State passed between nodes in the LangGraph."""
    denial_letter: str
    patient_context: str
    medical_necessity: dict
    policy_citation: dict
    precedent: dict
    critiques: Annotated[list, add]  # Appends across rounds
    round_num: int
    final_verdict: str


# ============================================================================
# LLM HELPER
# ============================================================================

def _llm_json(system: str, user: str, max_tokens: int = 1500) -> dict:
    """
    Call GPT-4o with JSON response format.
    Falls back to {"raw": text} if parsing fails.
    Includes cost guard - aborts if tokens exceed 50K cumulative.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            max_tokens=max_tokens,
            temperature=0.7,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ]
        )
        
        usage = response.usage
        print(f"[LLM] Tokens: {usage.total_tokens} (prompt: {usage.prompt_tokens}, completion: {usage.completion_tokens})")
        
        # Cost guard: abort if single call exceeds 50K tokens
        if usage.total_tokens > 50000:
            print(f"WARNING: Token limit exceeded ({usage.total_tokens} tokens)")
            return {"error": "token_limit_exceeded", "raw": ""}
        
        content = response.choices[0].message.content
        return json.loads(content)
        
    except json.JSONDecodeError as e:
        print(f"WARNING: JSON parse failed: {e}")
        return {"raw": content if 'content' in locals() else ""}
    except Exception as e:
        print(f"ERROR: LLM call failed: {e}")
        return {"error": str(e), "raw": ""}


def _llm_text(system: str, user: str, max_tokens: int = 2000) -> str:
    """Call GPT-4o for plain text response (supervisor synthesis)."""
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            max_tokens=max_tokens,
            temperature=0.7,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ]
        )
        
        usage = response.usage
        print(f"[LLM] Tokens: {usage.total_tokens} (prompt: {usage.prompt_tokens}, completion: {usage.completion_tokens})")
        
        return response.choices[0].message.content
        
    except Exception as e:
        print(f"ERROR: LLM call failed: {e}")
        return f"[Error: {str(e)}]"


# ============================================================================
# PATIENT AGENTS (Run in parallel)
# ============================================================================

@weave.op()
def medical_necessity_agent(state: HarnessState) -> dict:
    """
    Medical Necessity agent: argues clinical need using evidence.
    Runs in parallel with Policy Citation and Precedent agents.
    """
    print(f"\n[Round {state['round_num']}] Medical Necessity Agent")
    
    user_msg = f"""DENIAL LETTER:
{state['denial_letter']}

PATIENT CONTEXT:
{state['patient_context']}"""
    
    # Round 2: include critique
    if state.get('critiques') and len(state['critiques']) > 0:
        user_msg += f"\n\nPREVIOUS CRITIQUE TO ADDRESS:\n{json.dumps(state['critiques'][-1], indent=2)}"
    
    result = _llm_json(MEDICAL_NECESSITY_SYSTEM, user_msg)
    return {"medical_necessity": result}


@weave.op()
def policy_citation_agent(state: HarnessState) -> dict:
    """
    Policy Citation agent: matches patient to policy criteria.
    Runs in parallel with Medical Necessity and Precedent agents.
    """
    print(f"\n[Round {state['round_num']}] Policy Citation Agent")
    
    user_msg = f"""DENIAL LETTER:
{state['denial_letter']}

PATIENT CONTEXT:
{state['patient_context']}"""
    
    # Round 2: include critique
    if state.get('critiques') and len(state['critiques']) > 0:
        user_msg += f"\n\nPREVIOUS CRITIQUE TO ADDRESS:\n{json.dumps(state['critiques'][-1], indent=2)}"
    
    result = _llm_json(POLICY_CITATION_SYSTEM, user_msg)
    return {"policy_citation": result}


@weave.op()
def precedent_agent(state: HarnessState) -> dict:
    """
    Precedent agent: surfaces CA DMHC IMR cases with similar overturns.
    Runs in parallel with Medical Necessity and Policy Citation agents.
    """
    print(f"\n[Round {state['round_num']}] Precedent Agent")
    
    # TODO: In production, query the IMR dataset here
    # For now, use the denial letter context
    
    user_msg = f"""DENIAL LETTER:
{state['denial_letter']}

PATIENT CONTEXT:
{state['patient_context']}

Note: Reference California DMHC Independent Medical Review precedents where similar medical necessity denials were overturned. The IMR dataset contains 42,749 cases with a ~50-60% overturn rate for well-documented medical necessity denials."""
    
    # Round 2: include critique
    if state.get('critiques') and len(state['critiques']) > 0:
        user_msg += f"\n\nPREVIOUS CRITIQUE TO ADDRESS:\n{json.dumps(state['critiques'][-1], indent=2)}"
    
    result = _llm_json(PRECEDENT_SYSTEM, user_msg)
    return {"precedent": result}


# ============================================================================
# ADVERSARIAL CRITIC
# ============================================================================

@weave.op()
def insurer_defense_critic(state: HarnessState) -> dict:
    """
    Insurer Defense agent: adversarial critic with NO external tools.
    Simulates the insurer's internal medical reviewer attacking the appeal.
    """
    print(f"\n[Round {state['round_num']}] Insurer Defense Critic")
    
    # Build context from playbook if we can match CARC codes
    playbook_context = ""
    try:
        carc_match = playbook.match_denial(state['denial_letter'])
        if carc_match:
            playbook_context = f"\n\nPLAYBOOK CONTEXT (CARC patterns):\n{json.dumps(carc_match, indent=2)}"
    except Exception as e:
        print(f"Warning: Playbook match failed: {e}")
    
    user_msg = f"""DENIAL LETTER:
{state['denial_letter']}

PATIENT'S DRAFT APPEAL (3 agents):

MEDICAL NECESSITY ARGUMENT:
{json.dumps(state.get('medical_necessity', {}), indent=2)}

POLICY CITATION ARGUMENT:
{json.dumps(state.get('policy_citation', {}), indent=2)}

PRECEDENT ARGUMENT:
{json.dumps(state.get('precedent', {}), indent=2)}
{playbook_context}

Your task: identify the SINGLE WEAKEST argument and attack it specifically."""
    
    result = _llm_json(INSURER_DEFENSE_SYSTEM, user_msg)
    
    # Add round number to critique
    result['round'] = state['round_num']
    
    return {"critiques": [result]}


# ============================================================================
# SUPERVISOR
# ============================================================================

@weave.op()
def supervisor_start(state: HarnessState) -> dict:
    """
    Supervisor: kicks off Round 1.
    Increments round counter and routes to patient agents.
    """
    print("\n" + "=" * 80)
    print("SUPERVISOR: Starting Round 1")
    print("=" * 80)
    
    return {"round_num": 1}


@weave.op()
def supervisor_round_2(state: HarnessState) -> dict:
    """
    Supervisor: kicks off Round 2 after Round 1 critique.
    Increments round counter and routes back to patient agents for revision.
    """
    print("\n" + "=" * 80)
    print("SUPERVISOR: Starting Round 2 (revision)")
    print("=" * 80)
    
    return {"round_num": 2}


@weave.op()
def supervisor_synthesize(state: HarnessState) -> dict:
    """
    Supervisor: synthesizes final appeal verdict after 2 rounds.
    Integrates all patient agent outputs and addresses both critiques.
    """
    print("\n" + "=" * 80)
    print("SUPERVISOR: Synthesizing final verdict")
    print("=" * 80)
    
    user_msg = f"""ORIGINAL DENIAL:
{state['denial_letter']}

PATIENT CONTEXT:
{state['patient_context']}

ROUND 1 PATIENT ARGUMENTS:
Medical Necessity: {json.dumps(state.get('medical_necessity', {}), indent=2)}
Policy Citation: {json.dumps(state.get('policy_citation', {}), indent=2)}
Precedent: {json.dumps(state.get('precedent', {}), indent=2)}

ROUND 1 CRITIQUE:
{json.dumps(state['critiques'][0] if len(state['critiques']) > 0 else {}, indent=2)}

ROUND 2 REVISED ARGUMENTS:
(Patient agents revised their arguments addressing the critique)

ROUND 2 CRITIQUE:
{json.dumps(state['critiques'][1] if len(state['critiques']) > 1 else {}, indent=2)}

Synthesize the final appeal letter incorporating the strongest arguments and addressing both critiques."""
    
    final_verdict = _llm_text(SUPERVISOR_SYNTHESIS_SYSTEM, user_msg, max_tokens=2000)
    
    return {"final_verdict": final_verdict}


# ============================================================================
# CONDITIONAL ROUTING
# ============================================================================

def should_continue_rounds(state: HarnessState) -> str:
    """
    Routing logic: after critique, either go to Round 2 or finish.
    Hard cap at round_num >= 2 to prevent infinite loops.
    """
    if state['round_num'] < 2:
        print(f"\n→ Routing to Round 2 (current round: {state['round_num']})")
        return "round_2"
    else:
        print(f"\n→ Routing to final synthesis (round cap reached: {state['round_num']})")
        return "finish"


# ============================================================================
# BUILD THE GRAPH
# ============================================================================

def build_harness() -> StateGraph:
    """
    Build the LangGraph StateGraph for the multi-agent harness.
    
    Flow:
    supervisor_start → [medical_necessity, policy_citation, precedent] (parallel)
    → join → critic → conditional:
        if round < 2: → supervisor_round_2 → [patient agents again] → critic → finish
        else: → supervisor_synthesize → END
    """
    
    workflow = StateGraph(HarnessState)
    
    # Add nodes
    workflow.add_node("supervisor_start", supervisor_start)
    workflow.add_node("supervisor_round_2", supervisor_round_2)
    workflow.add_node("supervisor_synthesize", supervisor_synthesize)
    workflow.add_node("medical_necessity", medical_necessity_agent)
    workflow.add_node("policy_citation", policy_citation_agent)
    workflow.add_node("precedent", precedent_agent)
    workflow.add_node("critic", insurer_defense_critic)
    
    # Set entry point
    workflow.set_entry_point("supervisor_start")
    
    # Round 1: supervisor → three patient agents in parallel
    workflow.add_edge("supervisor_start", "medical_necessity")
    workflow.add_edge("supervisor_start", "policy_citation")
    workflow.add_edge("supervisor_start", "precedent")
    
    # All three patient agents → critic
    workflow.add_edge("medical_necessity", "critic")
    workflow.add_edge("policy_citation", "critic")
    workflow.add_edge("precedent", "critic")
    
    # Critic → conditional routing
    workflow.add_conditional_edges(
        "critic",
        should_continue_rounds,
        {
            "round_2": "supervisor_round_2",
            "finish": "supervisor_synthesize"
        }
    )
    
    # Round 2: supervisor_round_2 → patient agents again
    workflow.add_edge("supervisor_round_2", "medical_necessity")
    workflow.add_edge("supervisor_round_2", "policy_citation")
    workflow.add_edge("supervisor_round_2", "precedent")
    
    # Final synthesis → END
    workflow.add_edge("supervisor_synthesize", END)
    
    return workflow.compile()


# Build the harness
harness = build_harness()


# ============================================================================
# TOP-LEVEL WRAPPER FOR CLEAN WEAVE TRACES
# ============================================================================

@weave.op()
def run_harness(denial_letter: str, patient_context: str) -> dict:
    """
    Top-level entry point for the multi-agent harness.
    
    Wraps harness.invoke() so Weave nests all child calls under one parent
    trace named 'run_harness' instead of showing as flat langchain calls.
    
    Also captures metrics: elapsed time, CARC codes matched, federal protections,
    rounds completed, and critiques generated.
    
    Args:
        denial_letter: Full text of the insurance denial letter
        patient_context: JSON string of patient clinical details
        
    Returns:
        Dict containing medical_necessity, policy_citation, precedent,
        critiques, round_num, final_verdict, and _metrics
    """
    import time
    
    start = time.time()
    
    # Match denial to playbook CARC codes BEFORE invoking the harness
    try:
        matched_entries = playbook.match_denial(denial_letter)
        carc_codes_matched = [e.code for e in matched_entries[:3]]  # top 3 matches
    except Exception:
        carc_codes_matched = []
    
    try:
        applicable_protections = playbook.get_applicable_protections(denial_letter)
    except Exception:
        applicable_protections = []
    
    # Run the harness
    result = harness.invoke({
        "denial_letter": denial_letter,
        "patient_context": patient_context,
        "critiques": [],
        "round_num": 0,
        "medical_necessity": {},
        "policy_citation": {},
        "precedent": {},
        "final_verdict": ""
    })
    
    elapsed = time.time() - start
    
    # Add metrics to result
    result["_metrics"] = {
        "elapsed_seconds": round(elapsed, 1),
        "carc_codes_matched": carc_codes_matched,
        "federal_protections_found": [p["name"] for p in applicable_protections],
        "rounds_completed": result.get("round_num", 0),
        "critiques_generated": len(result.get("critiques", [])),
    }
    
    return result


# ============================================================================
# MAIN (for testing)
# ============================================================================

def main():
    """Test the harness with Case 1 (Oscar Cromolyn)."""
    
    # Load demo case
    import json
    from pathlib import Path
    
    case_path = Path("data/demo/case_01_oscar_cromolyn.json")
    if not case_path.exists():
        print(f"ERROR: Demo case not found at {case_path}")
        return 1
    
    case = json.load(open(case_path))
    
    print("=" * 80)
    print("TESTING MULTI-AGENT HARNESS")
    print(f"Case: {case['display_name']}")
    print("=" * 80)
    
    # Run harness
    result = run_harness(
        denial_letter=case["denial_letter"]["denial_text"],
        patient_context=json.dumps(case["patient_context"], indent=2)
    )
    
    print("\n" + "=" * 80)
    print("HARNESS COMPLETE")
    print("=" * 80)
    print("\nFINAL VERDICT:")
    print("-" * 80)
    print(result.get("final_verdict", "[No verdict generated]"))
    print("\n" + "=" * 80)
    print("✓ Check Weave dashboard for full call tree")
    print("=" * 80)
    
    return 0


if __name__ == "__main__":
    exit(main())
