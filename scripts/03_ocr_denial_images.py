"""
OCR the denial letter images into markdown reference files.
Uses Tesseract; install with: brew install tesseract  (or apt-get install tesseract-ocr)
Python deps: pip install pytesseract Pillow
"""
from pathlib import Path
import pytesseract
from PIL import Image

ROOT = Path("data/raw/denial_letters")
OUT = Path("data/processed/denial_letters_ocr")
OUT.mkdir(parents=True, exist_ok=True)

CASE_CONTEXT = {
    "cigna_van_terheyden_labcorp": {
        "source": "ProPublica Cigna PXDX investigation, March 2023",
        "insurer": "Cigna",
        "procedure": "LabCorp blood work",
        "denial_reason": "not medically necessary",
        "amount": "$358",
        "notes": "Famous PXDX-era denial. Patient is a physician himself."
    },
    "medicare_irf_72yo_parkinsons": {
        "source": "r/HealthInsurance",
        "insurer": "Medicare Advantage (unspecified)",
        "procedure": "Inpatient Rehabilitation Facility post-hip surgery",
        "patient": "72yo with Parkinson's disease",
        "denial_reason": "level of care not justified",
    },
    "cromolyn_denial_oscar_1": {
        "source": "r/HealthInsurance",
        "insurer": "Oscar Health",
        "procedure": "Cromolyn Sodium 100mg/5mL Solution",
        "diagnosis": "systemic mastocytosis / mast cell activation",
        "denial_reason": "diagnosis criteria not met per policy",
        "notes": "Page 1: prior auth screen showing 'Not covered'."
    },
    "cromolyn_denial_oscar_2": {
        "source": "r/HealthInsurance",
        "insurer": "Oscar Health",
        "notes": "Page 2: Oscar's medical necessity criteria for cromolyn."
    },
    "cromolyn_denial_oscar_3": {
        "source": "r/HealthInsurance",
        "insurer": "Oscar Health",
        "notes": "Page 3: appeal denial letter from Oscar."
    },
}

def ocr_image(image_path: Path) -> str:
    img = Image.open(image_path)
    return pytesseract.image_to_string(img, config="--psm 6")

def write_markdown(image_path: Path):
    stem = image_path.stem.replace("-v0", "").rsplit("-", 1)[0]
    # match a context key by best prefix
    key = next((k for k in CASE_CONTEXT if k in stem.lower().replace("_", "-").replace("-", "_")), None)
    ctx = CASE_CONTEXT.get(key, {"source": "unknown", "notes": "needs manual annotation"})
    text = ocr_image(image_path)
    md = f"""---
source_file: {image_path.name}
{chr(10).join(f"{k}: {v}" for k, v in ctx.items())}
---

# Extracted text

{text.strip()}
"""
    out_path = OUT / f"{image_path.stem}.md"
    out_path.write_text(md)
    print(f"✓ {image_path.name} → {out_path.name} ({len(text)} chars)")

if __name__ == "__main__":
    images = list(ROOT.rglob("*.webp")) + list(ROOT.rglob("*.png")) + list(ROOT.rglob("*.jpg"))
    print(f"Found {len(images)} images")
    for img in images:
        try:
            write_markdown(img)
        except Exception as e:
            print(f"✗ {img.name}: {e}")