"""
Denial playbook loader and matcher.

Loads denial_playbook.json and exposes helpers used by:
- Insurer Defense agent: build adversarial critiques from typical_insurer_arguments
- Patient agents (Medical Necessity, Policy Citation, Precedent): pull counter
  arguments, evidence requirements, and weak-spot ammunition
- Supervisor: set realistic expectations based on appealability tier

Example usage in an agent's system prompt construction:

    from agents.playbook import Playbook
    pb = Playbook.load()
    entry = pb.match_denial("Service is not medically necessary per policy CG-MED-50")
    insurer_prompt = pb.build_insurer_defense_context(entry)
    patient_prompt = pb.build_patient_counter_context(entry)
"""

from __future__ import annotations
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

PLAYBOOK_PATH = Path(__file__).parent.parent / "data" / "processed" / "denial_playbook.json"


# Regex patterns for matching denial language to playbook entries
_PATTERNS = {
    "CARC_50": [
        r"not\s+medically\s+necessary",
        r"medical\s+necessity",
        r"does\s+not\s+meet\s+(?:our\s+)?criteria",
        r"CARC\s*0?50\b",
    ],
    "CARC_197": [
        r"prior\s+authorization",
        r"precertification",
        r"pre-?cert",
        r"authorization\s+(?:required|not\s+obtained)",
        r"CARC\s*197\b",
    ],
    "CARC_96_N130_experimental": [
        r"experimental",
        r"investigational",
        r"unproven",
        r"not\s+established\s+as\s+safe",
        r"CARC\s*0?96\b.*N130",
    ],
    "CARC_167": [
        r"diagnosis\s+(?:is\s+)?not\s+covered",
        r"diagnosis\s+(?:does\s+not\s+match|mismatch)",
        r"CARC\s*167\b",
    ],
    "CARC_252": [
        r"additional\s+(?:documentation|information)\s+(?:is\s+)?required",
        r"attachment\s+(?:is\s+)?required",
        r"missing\s+(?:medical\s+records?|documentation)",
        r"CARC\s*252\b",
    ],
    "CARC_16": [
        r"lacks\s+information",
        r"submission\s+error",
        r"billing\s+error",
        r"incomplete\s+claim",
        r"CARC\s*0?16\b",
    ],
    "CARC_204": [
        r"not\s+covered\s+under\s+(?:your|the\s+patient'?s?)\s+(?:current\s+)?(?:benefit\s+)?plan",
        r"plan\s+exclusion",
        r"excluded\s+benefit",
        r"CARC\s*204\b",
    ],
    "CARC_119": [
        r"benefit\s+(?:maximum|limit)\s+(?:has\s+been\s+)?reached",
        r"visit\s+limit\s+exceeded",
        r"annual\s+(?:maximum|limit)",
        r"CARC\s*119\b",
    ],
    "CARC_242": [
        r"out[\s-]of[\s-]network",
        r"non[\s-]?network\s+provider",
        r"OON\s+provider",
        r"CARC\s*242\b",
    ],
    "CARC_B7": [
        r"provider\s+(?:not\s+)?(?:certified|eligible|credentialed)",
        r"credentialing",
        r"provider's?\s+license",
        r"CARC\s*B7\b",
    ],
}


@dataclass
class DenialEntry:
    """A single playbook entry matched to a denial."""
    key: str
    code: str
    category: str
    plain_english: str
    appealability: str
    typical_insurer_arguments: list[str]
    common_patient_counters: list[str]
    weak_spots_for_insurer: list[str]
    typical_evidence_needed: list[str]
    imr_overturn_rate_observed: str

    @classmethod
    def from_dict(cls, key: str, data: dict) -> "DenialEntry":
        return cls(
            key=key,
            code=data["code"],
            category=data["category"],
            plain_english=data["plain_english"],
            appealability=data["appealability"],
            typical_insurer_arguments=data["typical_insurer_arguments"],
            common_patient_counters=data["common_patient_counters"],
            weak_spots_for_insurer=data["weak_spots_for_insurer"],
            typical_evidence_needed=data["typical_evidence_needed"],
            imr_overturn_rate_observed=data["imr_overturn_rate_observed"],
        )


class Playbook:
    def __init__(self, data: dict):
        self.data = data
        self.codes = data["codes"]
        self.protections = data["cross_cutting_protections"]
        self.synthesis_notes = data["synthesis_notes_for_agents"]

    @classmethod
    def load(cls, path: Optional[Path] = None) -> "Playbook":
        path = path or PLAYBOOK_PATH
        with open(path, "r", encoding="utf-8") as f:
            return cls(json.load(f))

    def get(self, key: str) -> Optional[DenialEntry]:
        entry = self.codes.get(key)
        if entry is None:
            return None
        return DenialEntry.from_dict(key, entry)

    def match_denial(self, denial_text: str) -> list[DenialEntry]:
        """Match denial letter text against known patterns. Returns all matching entries
        ordered by specificity (more specific matches first)."""
        text = denial_text.lower()
        matches = []
        for key, patterns in _PATTERNS.items():
            score = sum(1 for p in patterns if re.search(p, text, re.IGNORECASE))
            if score > 0:
                matches.append((score, key))
        matches.sort(reverse=True)
        return [self.get(key) for _, key in matches if self.get(key)]

    def build_insurer_defense_context(self, entry: DenialEntry) -> str:
        """Returns a context block to inject into the Insurer Defense agent's prompt."""
        return f"""You are reviewing a patient's draft appeal letter. The original denial was a {entry.category} denial (CARC {entry.code}: {entry.plain_english}).

Your job is to write the strongest counter-argument the insurer's internal medical reviewer would make in response to the patient's draft. Pick the SINGLE WEAKEST claim in the patient's draft and attack it specifically.

Standard insurer arguments for this denial category:
{chr(10).join(f"- {arg}" for arg in entry.typical_insurer_arguments)}

Phrase your critique as a specific clinical or policy challenge, not vague disagreement. Cite the type of evidence the patient is missing or misciting."""

    def build_patient_counter_context(self, entry: DenialEntry) -> str:
        """Returns a context block for Patient-side agents to construct rebuttals."""
        return f"""The denial is a {entry.category} denial (CARC {entry.code}: {entry.plain_english}).
Appealability: {entry.appealability}. Observed overturn pattern: {entry.imr_overturn_rate_observed}.

Counter-arguments that historically work:
{chr(10).join(f"- {c}" for c in entry.common_patient_counters)}

Weak spots in the insurer's position you can exploit:
{chr(10).join(f"- {w}" for w in entry.weak_spots_for_insurer)}

Evidence the appeal must include:
{chr(10).join(f"- {e}" for e in entry.typical_evidence_needed)}"""

    def get_applicable_protections(self, denial_text: str) -> list[dict]:
        """Surface federal/state protections that may apply based on denial content."""
        text = denial_text.lower()
        applicable = []
        keywords = {
            "no_surprises_act": ["emergency", "out-of-network", "out of network", "air ambulance", "facility"],
            "mental_health_parity_addiction_equity_act": ["mental health", "substance use", "behavioral", "psychiatric", "addiction", "SUD"],
            "aca_essential_health_benefits": ["annual limit", "lifetime limit", "dollar maximum"],
            "section_1557_nondiscrimination": ["gender", "transgender", "pregnancy", "discrimination"],
            "erisa_full_and_fair_review": ["erisa", "employer", "group health plan"],
        }
        for key, kws in keywords.items():
            if any(kw in text for kw in kws):
                protection = self.protections[key]
                applicable.append({"name": key, **protection})
        return applicable


if __name__ == "__main__":
    # Quick smoke test
    pb = Playbook.load()
    print(f"Loaded {len(pb.codes)} playbook entries\n")

    sample_denial = """We have reviewed your request for prior authorization of cromolyn 
    sodium 100mg/5mL oral concentrate. Based on the information provided, your request 
    was not approved because the documented diagnosis does not meet our medical 
    necessity criteria for this medication."""

    matches = pb.match_denial(sample_denial)
    print(f"Matched {len(matches)} playbook entries for sample denial:")
    for m in matches:
        print(f"  - CARC {m.code} ({m.category}): {m.appealability} appealability")

    protections = pb.get_applicable_protections(sample_denial)
    print(f"\nApplicable cross-cutting protections: {len(protections)}")

    if matches:
        print(f"\n--- Insurer Defense context (first match) ---")
        print(pb.build_insurer_defense_context(matches[0])[:400] + "...")
