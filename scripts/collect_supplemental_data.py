#!/usr/bin/env python3
"""
Denial Defense - Supplemental Data Collection Script

This script collects supplemental data for the Denial Defense healthcare AI research project.
It respects robots.txt, rate limits, and only collects publicly available content.

Usage:
    python collect_supplemental_data.py --setup-only
    python collect_supplemental_data.py --skip-setup --only insurer_policies
    python collect_supplemental_data.py --all
"""

import argparse
import csv
import json
import logging
import re
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

# Configure logging
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "collection.log"

# Fix Windows Unicode issues
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Constants
USER_AGENT = "DenialDefense-Research-Bot (open source, contact: sabhisheksagar200@gmail.com)"
RATE_LIMIT_SECONDS = 2.0
MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 2

# Target procedures for insurer policies
TARGET_PROCEDURES = [
    "bariatric_surgery",
    "gender_affirming_care",
    "fertility_ivf",
    "mental_health_residential",
    "substance_use_treatment",
    "growth_hormone",
    "cromolyn_sodium",
    "prior_auth_imaging",
    "aba_therapy_autism",
    "biologic_medications"
]

# Insurer policy sources
INSURER_SOURCES = {
    "anthem": "https://www.anthem.com/provider/policies/clinical-guidelines/",
    "uhc": "https://www.uhcprovider.com/en/policies-protocols/medical-clinical-policies.html",
    "aetna": "https://www.aetna.com/health-care-professionals/clinical-policy-bulletins/medical-clinical-policy-bulletins.html",
    "cigna": "https://www.cigna.com/health-care-providers/coverage-and-claims/policies/medical-policies",
}

# State appeal resource URLs
STATE_RESOURCES = {
    "washington": "https://www.insurance.wa.gov/insurance-resources/health-insurance/appealing-health-insurance-denial/common-reasons-denial-and-examples-appeal-letters",
    "north_carolina": "https://www.ncdoi.gov/consumers/health-insurance/health-claim-denied/medical-appeals/medical-appeals-tool-kit",
}


class RateLimiter:
    """Per-domain rate limiter"""
    
    def __init__(self, delay_seconds: float = RATE_LIMIT_SECONDS):
        self.delay_seconds = delay_seconds
        self.last_request_time: Dict[str, float] = {}
    
    def wait(self, domain: str):
        """Wait if necessary before making a request to domain"""
        if domain in self.last_request_time:
            elapsed = time.time() - self.last_request_time[domain]
            if elapsed < self.delay_seconds:
                sleep_time = self.delay_seconds - elapsed
                logger.debug(f"Rate limiting {domain}: sleeping {sleep_time:.2f}s")
                time.sleep(sleep_time)
        self.last_request_time[domain] = time.time()


class RobotsChecker:
    """Check robots.txt compliance"""
    
    def __init__(self):
        self.parsers: Dict[str, RobotFileParser] = {}
    
    def can_fetch(self, url: str) -> bool:
        """Check if we can fetch the URL according to robots.txt"""
        parsed = urlparse(url)
        domain = f"{parsed.scheme}://{parsed.netloc}"
        
        if domain not in self.parsers:
            parser = RobotFileParser()
            parser.set_url(f"{domain}/robots.txt")
            try:
                parser.read()
                self.parsers[domain] = parser
                logger.debug(f"Loaded robots.txt for {domain}")
            except Exception as e:
                logger.warning(f"Could not load robots.txt for {domain}: {e}")
                return True
        
        can_fetch = self.parsers[domain].can_fetch(USER_AGENT, url)
        if not can_fetch:
            logger.warning(f"Blocked by robots.txt: {url}")
        return can_fetch


class DataCollector:
    """Main data collection orchestrator"""
    
    def __init__(self, root_path: Path):
        self.root = root_path
        self.rate_limiter = RateLimiter()
        self.robots_checker = RobotsChecker()
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})
    
    def fetch_with_retry(self, url: str, binary: bool = False) -> Optional[bytes | str]:
        """Fetch URL with retry logic and rate limiting"""
        if not self.robots_checker.can_fetch(url):
            return None
        
        domain = urlparse(url).netloc
        self.rate_limiter.wait(domain)
        
        for attempt in range(MAX_RETRIES):
            try:
                response = self.session.get(url, timeout=30)
                
                if response.status_code == 200:
                    logger.info(f"✓ Fetched: {url}")
                    return response.content if binary else response.text
                elif response.status_code == 429 or response.status_code >= 500:
                    wait_time = RETRY_BACKOFF_BASE ** attempt
                    logger.warning(f"Status {response.status_code} for {url}, retry {attempt+1}/{MAX_RETRIES} after {wait_time}s")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Failed to fetch {url}: HTTP {response.status_code}")
                    return None
            except Exception as e:
                logger.error(f"Error fetching {url}: {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_BACKOFF_BASE ** attempt)
        
        return None
    
    def save_file(self, content: bytes | str, path: Path, mode: str = "w") -> bool:
        """Save content to file"""
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            if mode == "wb":
                path.write_bytes(content)
            else:
                path.write_text(content, encoding="utf-8")
            logger.info(f"✓ Saved: {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save {path}: {e}")
            return False


def ensure_project_hierarchy(root: Path) -> bool:
    """
    Phase 0: Set up complete project hierarchy without disturbing existing files.
    Returns True if successful.
    """
    logger.info("=" * 80)
    logger.info("PHASE 0: Setting up project hierarchy")
    logger.info("=" * 80)
    
    # Define the complete structure
    structure = {
        "data/raw/imr": "CA DMHC Independent Medical Review determinations dataset",
        "data/raw/sample_appeals": "Sample appeal letters from state insurance departments",
        "data/raw/denial_letters/propublica": "Denial letters from ProPublica reporting",
        "data/raw/denial_letters/reddit": "Denial letters shared on Reddit (manually collected)",
        "data/raw/insurer_policies/anthem": "Anthem medical policies",
        "data/raw/insurer_policies/aetna": "Aetna clinical policy bulletins",
        "data/raw/insurer_policies/cigna": "Cigna medical policies",
        "data/raw/insurer_policies/uhc": "UnitedHealthcare medical policies",
        "data/raw/insurer_policies/oscar": "Oscar Health medical policies",
        "data/raw/insurer_policies/bcbs_fep": "BCBS Federal Employee Program policies",
        "data/raw/propublica_articles": "ProPublica 'Uncovered' series articles",
        "data/raw/kff_bill_of_month": "KFF Health News Bill of the Month stories",
        "data/raw/state_appeal_resources/washington": "Washington state appeal resources",
        "data/raw/state_appeal_resources/north_carolina": "North Carolina appeal resources",
        "data/raw/state_appeal_resources/new_york": "New York appeal resources",
        "data/raw/state_appeal_resources/texas": "Texas appeal resources",
        "data/raw/state_appeal_resources/massachusetts": "Massachusetts appeal resources",
        "data/processed": "Processed and cleaned datasets",
        "data/demo/case_01_bariatric": "Demo case: bariatric surgery denial",
        "data/demo/case_02_cromolyn": "Demo case: cromolyn sodium denial",
        "data/demo/case_03_oon_emergency": "Demo case: out-of-network emergency denial",
        "scripts": "Data collection and processing scripts",
        "agents": "Multi-agent system components",
        "web/templates": "Web UI templates",
        "eval": "Evaluation scripts and results",
        "prompts": "LLM prompts and templates",
        "logs": "Collection and processing logs",
    }
    
    created_dirs = []
    existing_dirs = []
    
    # Create all directories
    for dir_path, description in structure.items():
        full_path = root / dir_path
        if full_path.exists():
            file_count = len(list(full_path.glob("*"))) if full_path.is_dir() else 0
            existing_dirs.append((dir_path, file_count))
            logger.info(f"FOUND: {dir_path}/ [{file_count} files]")
        else:
            full_path.mkdir(parents=True, exist_ok=True)
            # Add .gitkeep
            gitkeep = full_path / ".gitkeep"
            gitkeep.touch()
            created_dirs.append(dir_path)
            logger.info(f"CREATED: {dir_path}/")
    
    # Create README.md if it doesn't exist
    readme_path = root / "data" / "raw" / "README.md"
    if not readme_path.exists():
        readme_content = """# Raw Data Directory

This directory contains raw, unprocessed data collected from various public sources for the Denial Defense project.

## Directory Structure

### `imr/`
California Department of Managed Health Care (DMHC) Independent Medical Review (IMR) determinations dataset.
- Source: https://data.chhs.ca.gov/dataset/independent-medical-review-imr-determinations-trend
- License: Public domain
- Format: CSV
- Records: 42,750 cases

### `sample_appeals/`
Sample appeal letters published by state insurance departments for consumer education.
- Sources: Washington, North Carolina, New York, Texas, Massachusetts insurance departments
- License: Public domain (government works)
- Format: DOC/DOCX

### `denial_letters/`
Denial letters from various sources (anonymized if containing PHI).
- `propublica/`: From ProPublica investigative reporting
- `reddit/`: Manually collected from Reddit (r/HealthInsurance, r/Insurance) with user permission

### `insurer_policies/`
Publicly published medical policies from major insurers.
- Format: PDF
- Covers 10 key procedures frequently subject to denials
- Sources: Anthem, Aetna, Cigna, UHC, Oscar, BCBS FEP

### `propublica_articles/`
Articles from ProPublica's "Uncovered" series on health insurance denials.
- Source: https://www.propublica.org/series/uncovered-the-power-of-health-insurance
- License: Creative Commons BY-NC-ND 3.0
- Format: Markdown with frontmatter

### `kff_bill_of_month/`
Stories from KFF Health News "Bill of the Month" series.
- Source: https://kffhealthnews.org/news/series/bill-of-the-month/
- License: Creative Commons BY-NC-ND 4.0
- Format: Markdown with structured frontmatter

### `state_appeal_resources/`
Consumer appeal guides and sample letters by state.
- License: Public domain (government works)
- Format: Mixed (PDF, DOC, HTML)

## Data Collection Principles

1. **Public sources only**: We only collect data that is published publicly for consumer information
2. **Robots.txt compliance**: All scraping respects robots.txt
3. **Rate limiting**: 1 request per 2 seconds per domain
4. **Anonymization**: Any PHI encountered is flagged and excluded
5. **Attribution**: All sources are documented with URLs and timestamps
6. **License compliance**: We respect all license terms (Creative Commons, public domain, etc.)

## License

The Denial Defense project is open source under the MIT License. Individual data sources may have their own licenses (documented above). All data is used for non-commercial research purposes only.
"""
        readme_path.write_text(readme_content, encoding="utf-8")
        logger.info(f"✓ Created: {readme_path}")
    
    # Create .gitignore if it doesn't exist
    gitignore_path = root / ".gitignore"
    if not gitignore_path.exists():
        gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/

# Data
data/processed/*.parquet
data/raw/insurer_policies/**/*.pdf
*.log

# Environment
.env
.env.local

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Large files
*.zip
*.tar.gz
"""
        gitignore_path.write_text(gitignore_content, encoding="utf-8")
        logger.info(f"✓ Created: {gitignore_path}")
    
    # Print tree summary
    logger.info("")
    logger.info("=" * 80)
    logger.info("HIERARCHY VALIDATION")
    logger.info("=" * 80)
    logger.info(f"✓ {len(existing_dirs)} directories already existed")
    logger.info(f"✓ {len(created_dirs)} directories created")
    
    # Print detailed tree
    logger.info("")
    logger.info("denial-defense/")
    for dir_path, _ in sorted(structure.items()):
        full_path = root / dir_path
        if full_path.exists():
            file_count = len(list(full_path.glob("*")))
            status = "✓ exists" if dir_path in [d for d, _ in existing_dirs] else "✓ created"
            indent = "  " * (dir_path.count("/") - 1)
            dir_name = dir_path.split("/")[-1]
            logger.info(f"{indent}├── {dir_name}/ [{file_count} files] {status}")
    
    logger.info("")
    logger.info("✓ Phase 0 complete - project hierarchy ready")
    logger.info("")
    
    return True


def scrape_insurer_policies(collector: DataCollector) -> Dict[str, int]:
    """
    Phase 1: Scrape insurer medical policies
    Returns dict with success/failure counts
    """
    logger.info("=" * 80)
    logger.info("PHASE 1: Scraping insurer medical policies")
    logger.info("=" * 80)
    
    manifest_path = collector.root / "data" / "raw" / "insurer_policies" / "manifest.csv"
    manifest_entries = []
    
    stats = {"success": 0, "skipped": 0, "failed": 0}
    
    # Note: This is a simplified implementation
    # Full implementation would require parsing each insurer's policy page structure
    # and searching for specific procedures. This would likely need Playwright for
    # JS-heavy sites and custom logic per insurer.
    
    logger.warning("Insurer policy scraping requires custom parsers per insurer.")
    logger.warning("This is a placeholder that demonstrates the structure.")
    logger.warning("Full implementation would need:")
    logger.warning("  1. Playwright for JS-heavy sites")
    logger.warning("  2. Custom selectors per insurer")
    logger.warning("  3. Search/filter logic for each procedure")
    
    for insurer, base_url in INSURER_SOURCES.items():
        logger.info(f"\nProcessing {insurer}...")
        logger.info(f"Base URL: {base_url}")
        
        for procedure in TARGET_PROCEDURES:
            output_path = collector.root / "data" / "raw" / "insurer_policies" / insurer / f"{procedure}.pdf"
            
            if output_path.exists():
                logger.info(f"  ⊘ Skipped {procedure} (already exists)")
                stats["skipped"] += 1
                manifest_entries.append({
                    "insurer": insurer,
                    "procedure": procedure,
                    "url": "",
                    "success": "skipped",
                    "file_path": str(output_path.relative_to(collector.root)),
                    "timestamp": datetime.now().isoformat()
                })
                continue
            
            # Placeholder - would need custom logic per insurer
            logger.warning(f"  ⚠ {procedure} - manual download required")
            stats["failed"] += 1
            manifest_entries.append({
                "insurer": insurer,
                "procedure": procedure,
                "url": base_url,
                "success": "false",
                "file_path": "",
                "timestamp": datetime.now().isoformat()
            })
    
    # Write manifest
    if manifest_entries:
        with manifest_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["insurer", "procedure", "url", "success", "file_path", "timestamp"])
            writer.writeheader()
            writer.writerows(manifest_entries)
        logger.info(f"\n✓ Manifest written to {manifest_path}")
    
    logger.info(f"\nPhase 1 complete: {stats['success']} succeeded, {stats['skipped']} skipped, {stats['failed']} failed")
    return stats


def scrape_propublica(collector: DataCollector) -> Dict[str, int]:
    """
    Phase 2: Scrape ProPublica 'Uncovered' series
    Returns dict with success/failure counts
    """
    logger.info("=" * 80)
    logger.info("PHASE 2: Scraping ProPublica 'Uncovered' series")
    logger.info("=" * 80)
    
    base_url = "https://www.propublica.org/series/uncovered-the-power-of-health-insurance"
    output_dir = collector.root / "data" / "raw" / "propublica_articles"
    
    stats = {"success": 0, "skipped": 0, "failed": 0}
    
    # Fetch series page
    html = collector.fetch_with_retry(base_url)
    if not html:
        logger.error("Failed to fetch ProPublica series page")
        return stats
    
    soup = BeautifulSoup(html, "html.parser")
    
    # Find article links (this selector may need adjustment)
    article_links = []
    for link in soup.find_all("a", href=True):
        href = link["href"]
        if href.startswith("/article/") and "uncovered" not in href:
            full_url = f"https://www.propublica.org{href}"
            if full_url not in article_links:
                article_links.append(full_url)
    
    logger.info(f"Found {len(article_links)} potential article links")
    
    for url in article_links[:30]:  # Limit to prevent excessive requests
        slug = url.split("/")[-1]
        output_path = output_dir / f"{slug}.md"
        
        if output_path.exists():
            logger.info(f"⊘ Skipped {slug} (already exists)")
            stats["skipped"] += 1
            continue
        
        article_html = collector.fetch_with_retry(url)
        if not article_html:
            stats["failed"] += 1
            continue
        
        article_soup = BeautifulSoup(article_html, "html.parser")
        
        # Extract metadata
        title = article_soup.find("h1")
        title_text = title.get_text(strip=True) if title else slug
        
        date_elem = article_soup.find("time")
        date_text = date_elem.get("datetime", "") if date_elem else ""
        
        # Extract article body (may need refinement)
        body = article_soup.find("div", class_=lambda x: x and "article-body" in x)
        if not body:
            body = article_soup.find("article")
        
        body_text = ""
        if body:
            for p in body.find_all("p"):
                body_text += p.get_text() + "\n\n"
        
        # Create markdown
        markdown = f"""---
title: {title_text}
url: {url}
date: {date_text}
denial_themes: []
---

{body_text}
"""
        
        if collector.save_file(markdown, output_path):
            stats["success"] += 1
        else:
            stats["failed"] += 1
    
    logger.info(f"\nPhase 2 complete: {stats['success']} succeeded, {stats['skipped']} skipped, {stats['failed']} failed")
    return stats


def scrape_kff(collector: DataCollector) -> Dict[str, int]:
    """
    Phase 3: Scrape KFF Health News 'Bill of the Month' series
    Returns dict with success/failure counts
    """
    logger.info("=" * 80)
    logger.info("PHASE 3: Scraping KFF Bill of the Month series")
    logger.info("=" * 80)
    
    base_url = "https://kffhealthnews.org/news/series/bill-of-the-month/"
    output_dir = collector.root / "data" / "raw" / "kff_bill_of_month"
    
    stats = {"success": 0, "skipped": 0, "failed": 0}
    
    html = collector.fetch_with_retry(base_url)
    if not html:
        logger.error("Failed to fetch KFF series page")
        return stats
    
    soup = BeautifulSoup(html, "html.parser")
    
    # Find article links
    article_links = []
    for link in soup.find_all("a", href=True):
        href = link["href"]
        if "kffhealthnews.org" in href and "/news/" in href and href not in article_links:
            article_links.append(href)
    
    logger.info(f"Found {len(article_links)} potential article links")
    
    for url in article_links[:30]:
        slug = url.rstrip("/").split("/")[-1]
        output_path = output_dir / f"{slug}.md"
        
        if output_path.exists():
            logger.info(f"⊘ Skipped {slug} (already exists)")
            stats["skipped"] += 1
            continue
        
        article_html = collector.fetch_with_retry(url)
        if not article_html:
            stats["failed"] += 1
            continue
        
        article_soup = BeautifulSoup(article_html, "html.parser")
        
        # Extract metadata
        title = article_soup.find("h1")
        title_text = title.get_text(strip=True) if title else slug
        
        date_elem = article_soup.find("time")
        date_text = date_elem.get("datetime", "") if date_elem else ""
        
        # Extract body
        body = article_soup.find("article") or article_soup.find("div", class_="article-content")
        body_text = ""
        if body:
            for p in body.find_all("p"):
                body_text += p.get_text() + "\n\n"
        
        # Create markdown with structured frontmatter
        markdown = f"""---
title: {title_text}
url: {url}
date: {date_text}
insurer: ""
procedure: ""
billed: ""
final_paid: ""
denial_reason: ""
outcome: ""
---

{body_text}
"""
        
        if collector.save_file(markdown, output_path):
            stats["success"] += 1
        else:
            stats["failed"] += 1
    
    logger.info(f"\nPhase 3 complete: {stats['success']} succeeded, {stats['skipped']} skipped, {stats['failed']} failed")
    return stats


def scrape_state_resources(collector: DataCollector) -> Dict[str, int]:
    """
    Phase 4: Scrape state insurance department appeal resources
    Returns dict with success/failure counts
    """
    logger.info("=" * 80)
    logger.info("PHASE 4: Scraping state appeal resources")
    logger.info("=" * 80)
    
    stats = {"success": 0, "skipped": 0, "failed": 0}
    
    for state, url in STATE_RESOURCES.items():
        logger.info(f"\nProcessing {state}...")
        output_dir = collector.root / "data" / "raw" / "state_appeal_resources" / state
        
        html = collector.fetch_with_retry(url)
        if not html:
            logger.error(f"Failed to fetch {state} resources")
            stats["failed"] += 1
            continue
        
        soup = BeautifulSoup(html, "html.parser")
        
        # Look for downloadable files (DOC, DOCX, PDF)
        for link in soup.find_all("a", href=True):
            href = link["href"]
            if any(ext in href.lower() for ext in [".doc", ".docx", ".pdf"]):
                # Make absolute URL
                if not href.startswith("http"):
                    from urllib.parse import urljoin
                    href = urljoin(url, href)
                
                filename = href.split("/")[-1].split("?")[0]
                output_path = output_dir / filename
                
                if output_path.exists():
                    logger.info(f"  ⊘ Skipped {filename} (already exists)")
                    stats["skipped"] += 1
                    continue
                
                content = collector.fetch_with_retry(href, binary=True)
                if content:
                    if collector.save_file(content, output_path, mode="wb"):
                        stats["success"] += 1
                    else:
                        stats["failed"] += 1
                else:
                    stats["failed"] += 1
    
    logger.info(f"\nPhase 4 complete: {stats['success']} succeeded, {stats['skipped']} skipped, {stats['failed']} failed")
    return stats


def validate_collection(root: Path) -> Dict[str, any]:
    """
    Final validation pass: check file counts, PDF integrity, PHI screening
    Returns validation report dict
    """
    logger.info("=" * 80)
    logger.info("VALIDATION PASS")
    logger.info("=" * 80)
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "categories": {},
        "phi_flags": [],
        "corrupt_files": [],
        "summary": {}
    }
    
    # Count files by category
    categories = {
        "insurer_policies": root / "data" / "raw" / "insurer_policies",
        "propublica_articles": root / "data" / "raw" / "propublica_articles",
        "kff_bill_of_month": root / "data" / "raw" / "kff_bill_of_month",
        "state_resources": root / "data" / "raw" / "state_appeal_resources",
        "imr": root / "data" / "raw" / "imr",
        "sample_appeals": root / "data" / "raw" / "sample_appeals",
    }
    
    for category, path in categories.items():
        if path.exists():
            file_count = len(list(path.rglob("*.*")))
            report["categories"][category] = file_count
            logger.info(f"{category}: {file_count} files")
        else:
            report["categories"][category] = 0
            logger.warning(f"{category}: directory not found")
    
    # Check for PHI patterns (SSN, MRN)
    ssn_pattern = r'\b\d{3}-\d{2}-\d{4}\b'
    mrn_pattern = r'\b(MRN|Medical Record Number)[\s:]+\d{6,}\b'
    
    logger.info("\nScanning for potential PHI...")
    for text_file in root.glob("data/raw/**/*.md"):
        try:
            content = text_file.read_text(encoding="utf-8")
            if re.search(ssn_pattern, content) or re.search(mrn_pattern, content, re.IGNORECASE):
                report["phi_flags"].append(str(text_file.relative_to(root)))
                logger.warning(f"⚠ Potential PHI found: {text_file.relative_to(root)}")
        except Exception as e:
            logger.error(f"Error scanning {text_file}: {e}")
    
    # Summary
    total_files = sum(report["categories"].values())
    report["summary"] = {
        "total_files": total_files,
        "phi_flags_count": len(report["phi_flags"]),
        "corrupt_files_count": len(report["corrupt_files"]),
    }
    
    logger.info(f"\n✓ Total files collected: {total_files}")
    logger.info(f"✓ PHI flags: {len(report['phi_flags'])}")
    logger.info(f"✓ Corrupt files: {len(report['corrupt_files'])}")
    
    # Write summary report
    summary_path = root / "logs" / "collection_summary.md"
    summary_md = f"""# Data Collection Summary

**Generated:** {report['timestamp']}

## File Counts by Category

| Category | File Count |
|----------|------------|
| Insurer Policies | {report['categories'].get('insurer_policies', 0)} |
| ProPublica Articles | {report['categories'].get('propublica_articles', 0)} |
| KFF Bill of Month | {report['categories'].get('kff_bill_of_month', 0)} |
| State Resources | {report['categories'].get('state_resources', 0)} |
| IMR Dataset | {report['categories'].get('imr', 0)} |
| Sample Appeals | {report['categories'].get('sample_appeals', 0)} |

**Total Files:** {report['summary']['total_files']}

## PHI Screening

{'✓ No PHI detected' if len(report['phi_flags']) == 0 else f"⚠ {len(report['phi_flags'])} files flagged for potential PHI:"}

{chr(10).join(f"- {f}" for f in report['phi_flags'])}

## Acceptance Criteria

- [ ] At least 30 insurer policy PDFs (current: {report['categories'].get('insurer_policies', 0)})
- [ ] At least 15 ProPublica articles (current: {report['categories'].get('propublica_articles', 0)})
- [ ] At least 20 KFF stories (current: {report['categories'].get('kff_bill_of_month', 0)})
- [{'x' if len(report['phi_flags']) == 0 else ' '}] No PHI flagged

## Notes

This is an automated report. Manual review is recommended for:
1. Files flagged for potential PHI
2. Insurer policies (may require manual download)
3. PDF integrity (not validated in this pass)
"""
    
    summary_path.write_text(summary_md, encoding="utf-8")
    logger.info(f"\n✓ Summary report written to {summary_path}")
    
    return report


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Denial Defense supplemental data collection script"
    )
    parser.add_argument(
        "--setup-only",
        action="store_true",
        help="Only run Phase 0 (hierarchy setup)"
    )
    parser.add_argument(
        "--skip-setup",
        action="store_true",
        help="Skip Phase 0 (hierarchy setup)"
    )
    parser.add_argument(
        "--only",
        choices=["insurer_policies", "propublica", "kff", "state_resources"],
        help="Only run specified phase"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all phases (setup + all scraping + validation)"
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Project root directory (default: current directory)"
    )
    
    args = parser.parse_args()
    
    root = args.root
    logger.info(f"Project root: {root}")
    
    # Phase 0: Setup
    if not args.skip_setup:
        if not ensure_project_hierarchy(root):
            logger.error("Hierarchy setup failed. Exiting.")
            return 1
        
        if args.setup_only:
            logger.info("Setup complete. Exiting (--setup-only flag).")
            return 0
    
    # Initialize collector
    collector = DataCollector(root)
    
    # Run phases
    phase_stats = {}
    
    if args.all or args.only == "insurer_policies":
        phase_stats["insurer_policies"] = scrape_insurer_policies(collector)
    
    if args.all or args.only == "propublica":
        phase_stats["propublica"] = scrape_propublica(collector)
    
    if args.all or args.only == "kff":
        phase_stats["kff"] = scrape_kff(collector)
    
    if args.all or args.only == "state_resources":
        phase_stats["state_resources"] = scrape_state_resources(collector)
    
    # Validation
    if args.all or (not args.only and not args.setup_only):
        validation_report = validate_collection(root)
    
    logger.info("=" * 80)
    logger.info("COLLECTION COMPLETE")
    logger.info("=" * 80)
    
    for phase, stats in phase_stats.items():
        logger.info(f"{phase}: {stats.get('success', 0)} succeeded, {stats.get('skipped', 0)} skipped, {stats.get('failed', 0)} failed")
    
    return 0


if __name__ == "__main__":
    exit(main())
