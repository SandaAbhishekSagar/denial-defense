"""
Convert state-published sample appeal letters from .doc/.docx to markdown,
preserving placeholder structure for use as reference exemplars.
Python deps: pip install mammoth python-docx
For .doc (old format): convert to .docx first with: soffice --headless --convert-to docx file.doc
"""
from pathlib import Path
import mammoth
import re

ROOT = Path("data/raw/sample_appeals")
OUT = Path("data/processed/sample_appeals_md")
OUT.mkdir(parents=True, exist_ok=True)

METADATA = {
    "example-of-letter-seeking-payment-to-an-out-of-network-provider": {
        "denial_category": "out_of_network",
        "use_case": "Out-of-network provider payment dispute",
        "key_arguments": ["network adequacy", "no in-network alternative", "continuity of care"],
        "state_source": "Washington State OIC",
    },
    "example-prior-authorization-request-gender-affirming-care-appeal-letter": {
        "denial_category": "prior_auth_gender_affirming",
        "use_case": "Prior auth denial for gender-affirming care",
        "key_arguments": ["medical necessity", "WPATH standards", "ACA Section 1557"],
        "state_source": "Washington State OIC",
    },
    "example-appeal-mental-health-substance-use-disorder-denial": {
        "denial_category": "mh_sud_parity",
        "use_case": "Mental health / substance use parity violation",
        "key_arguments": ["MHPAEA parity", "medical necessity", "level of care"],
        "state_source": "Washington State OIC",
    },
}

def docx_to_markdown(path: Path) -> str:
    with open(path, "rb") as f:
        result = mammoth.convert_to_markdown(f)
    return result.value

def extract_placeholders(md: str) -> list[str]:
    return sorted(set(re.findall(r"\[([^\]]+)\]", md)))

def process(path: Path):
    stem = path.stem
    meta = METADATA.get(stem, {})
    try:
        body = docx_to_markdown(path)
    except Exception as e:
        print(f"✗ {path.name}: {e} (you may need to convert .doc → .docx first)")
        return
    placeholders = extract_placeholders(body)
    md = f"""---
source_file: {path.name}
denial_category: {meta.get('denial_category', 'unknown')}
use_case: {meta.get('use_case', '')}
key_arguments: {meta.get('key_arguments', [])}
state_source: {meta.get('state_source', '')}
placeholders: {placeholders}
---

{body}
"""
    out = OUT / f"{stem}.md"
    out.write_text(md)
    print(f"✓ {path.name} → {out.name} ({len(placeholders)} placeholders)")

if __name__ == "__main__":
    files = list(ROOT.rglob("*.doc*"))
    print(f"Found {len(files)} appeal letters")
    for f in files:
        process(f)