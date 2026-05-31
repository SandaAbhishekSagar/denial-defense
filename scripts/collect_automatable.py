#!/usr/bin/env python3
"""
Denial Defense - Automatable Data Collection Script

Collects data from sources that don't require interactive browser sessions or login walls.
Organized into 3 tiers by confidence level and complexity.
"""

import argparse
import json
import logging
import re
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup
from PyPDF2 import PdfReader
from tenacity import retry, stop_after_attempt, wait_exponential
import trafilatura

# Fix Windows Unicode issues
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Configure paths
ROOT = Path(__file__).parent.parent
DATA_RAW = ROOT / "data" / "raw"
LOGS_DIR = ROOT / "logs"
QUARANTINE_DIR = ROOT / "data" / "quarantine"

# Ensure directories exist
LOGS_DIR.mkdir(parents=True, exist_ok=True)
QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "collection.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Constants
USER_AGENT = "DenialDefense-Research-Bot/0.1 (open-source hackathon project; contact: sabhisheksagar200@gmail.com)"
RATE_LIMIT_SECONDS = 2.0
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3
ERROR_PAUSE_THRESHOLD = 5
ERROR_PAUSE_DURATION = 300  # 5 minutes

# PHI patterns
SSN_PATTERN = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')
MRN_PATTERN = re.compile(r'MRN:\s*\d+', re.IGNORECASE)

# Global state
last_request_time: Dict[str, float] = {}
domain_error_counts: Dict[str, int] = defaultdict(int)
domain_pause_until: Dict[str, float] = {}
stats = {
    "tier1": {"ok": 0, "skip": 0, "error": 0, "manual": 0, "blocked": 0},
    "tier2": {"ok": 0, "skip": 0, "error": 0, "manual": 0, "blocked": 0},
    "tier3": {"ok": 0, "skip": 0, "error": 0, "manual": 0, "blocked": 0},
}
manual_downloads: List[Dict[str, str]] = []
errors_log: List[Dict[str, str]] = []


class RobotsCache:
    """Cache for robots.txt parsers"""
    def __init__(self):
        self.parsers: Dict[str, RobotFileParser] = {}
    
    def can_fetch(self, url: str) -> bool:
        """Check if URL can be fetched according to robots.txt"""
        parsed = urlparse(url)
        domain = f"{parsed.scheme}://{parsed.netloc}"
        
        if domain not in self.parsers:
            parser = RobotFileParser()
            parser.set_url(f"{domain}/robots.txt")
            try:
                parser.read()
                self.parsers[domain] = parser
            except Exception as e:
                logger.debug(f"Could not read robots.txt for {domain}: {e}")
                return True  # Allow by default if can't read
        
        return self.parsers[domain].can_fetch(USER_AGENT, url)


robots_cache = RobotsCache()


def get_domain(url: str) -> str:
    """Extract domain from URL"""
    return urlparse(url).netloc


def wait_for_rate_limit(domain: str):
    """Wait if necessary to respect rate limit"""
    if domain in last_request_time:
        elapsed = time.time() - last_request_time[domain]
        if elapsed < RATE_LIMIT_SECONDS:
            time.sleep(RATE_LIMIT_SECONDS - elapsed)


def check_domain_paused(domain: str) -> bool:
    """Check if domain is in error pause"""
    if domain in domain_pause_until:
        if time.time() < domain_pause_until[domain]:
            return True
        else:
            # Pause expired, reset
            del domain_pause_until[domain]
            domain_error_counts[domain] = 0
    return False


def record_domain_error(domain: str):
    """Record error for domain and pause if threshold reached"""
    domain_error_counts[domain] += 1
    if domain_error_counts[domain] >= ERROR_PAUSE_THRESHOLD:
        domain_pause_until[domain] = time.time() + ERROR_PAUSE_DURATION
        logger.warning(f"Domain {domain} paused for {ERROR_PAUSE_DURATION}s after {ERROR_PAUSE_THRESHOLD} consecutive errors")


def record_domain_success(domain: str):
    """Reset error count on success"""
    domain_error_counts[domain] = 0


@retry(stop=stop_after_attempt(MAX_RETRIES), wait=wait_exponential(multiplier=2, min=2, max=8))
def fetch_with_retry(url: str) -> requests.Response:
    """Fetch URL with retry logic"""
    response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return response


def fetch_url(
    url: str,
    target_path: Path,
    tier: str,
    binary: bool = False,
    validate_func=None
) -> Tuple[str, int, int]:
    """
    Fetch URL and save to target_path.
    
    Returns:
        (status, bytes_downloaded, elapsed_ms)
        status: one of OK, SKIP_EXISTS, ERROR_<reason>, MANUAL_REQUIRED, BLOCKED
    """
    start_time = time.time()
    
    # Check if already exists
    if target_path.exists() and target_path.stat().st_size > 0:
        return ("SKIP_EXISTS", 0, 0)
    
    # Check robots.txt
    if not robots_cache.can_fetch(url):
        stats[tier]["blocked"] += 1
        return ("BLOCKED", 0, 0)
    
    domain = get_domain(url)
    
    # Check if domain is paused
    if check_domain_paused(domain):
        remaining = int(domain_pause_until[domain] - time.time())
        return (f"ERROR_DOMAIN_PAUSED_{remaining}s", 0, int((time.time() - start_time) * 1000))
    
    # Rate limit
    wait_for_rate_limit(domain)
    
    try:
        # Fetch
        response = fetch_with_retry(url)
        last_request_time[domain] = time.time()
        
        # Save
        target_path.parent.mkdir(parents=True, exist_ok=True)
        if binary:
            target_path.write_bytes(response.content)
        else:
            target_path.write_text(response.text, encoding='utf-8')
        
        # Validate if function provided
        if validate_func and not validate_func(target_path):
            target_path.unlink()
            return ("ERROR_VALIDATION_FAILED", 0, int((time.time() - start_time) * 1000))
        
        # Check for PHI
        if not binary and scan_for_phi(target_path):
            quarantine_path = QUARANTINE_DIR / target_path.name
            target_path.rename(quarantine_path)
            return ("ERROR_PHI_DETECTED", 0, int((time.time() - start_time) * 1000))
        
        bytes_downloaded = target_path.stat().st_size
        elapsed_ms = int((time.time() - start_time) * 1000)
        
        stats[tier]["ok"] += 1
        record_domain_success(domain)
        
        return ("OK", bytes_downloaded, elapsed_ms)
        
    except requests.exceptions.HTTPError as e:
        elapsed_ms = int((time.time() - start_time) * 1000)
        stats[tier]["error"] += 1
        record_domain_error(domain)
        
        status_code = e.response.status_code if hasattr(e, 'response') else 0
        return (f"ERROR_HTTP_{status_code}", 0, elapsed_ms)
        
    except Exception as e:
        elapsed_ms = int((time.time() - start_time) * 1000)
        stats[tier]["error"] += 1
        record_domain_error(domain)
        
        error_type = type(e).__name__
        return (f"ERROR_{error_type}", 0, elapsed_ms)


def validate_pdf(path: Path) -> bool:
    """Validate PDF has > 0 pages"""
    try:
        reader = PdfReader(path)
        return len(reader.pages) > 0
    except Exception as e:
        logger.error(f"PDF validation failed for {path}: {e}")
        return False


def scan_for_phi(path: Path) -> bool:
    """Scan file for PHI patterns. Returns True if PHI detected."""
    try:
        content = path.read_text(encoding='utf-8')
        if SSN_PATTERN.search(content) or MRN_PATTERN.search(content):
            logger.warning(f"PHI detected in {path}")
            with open(LOGS_DIR / "phi_quarantine.log", "a", encoding='utf-8') as f:
                f.write(f"{datetime.now().isoformat()} - {path}\n")
            return True
    except Exception as e:
        logger.error(f"Error scanning {path} for PHI: {e}")
    return False


def log_status(status: str, tier: str, target_path: Path, bytes_size: int, elapsed_ms: int, url: str):
    """Print standardized status line"""
    emoji_map = {
        "OK": "✅",
        "SKIP_EXISTS": "⏭️",
        "MANUAL_REQUIRED": "⚠️",
        "BLOCKED": "🚫",
    }
    
    for prefix in ["ERROR_", "SKIP_"]:
        if status.startswith(prefix):
            emoji = "❌" if prefix == "ERROR_" else "⏭️"
            break
    else:
        emoji = emoji_map.get(status, "❓")
    
    bytes_str = f"{bytes_size:>8}" if bytes_size > 0 else "—".rjust(8)
    elapsed_str = f"{elapsed_ms:>6}ms" if elapsed_ms > 0 else "—".rjust(9)
    
    rel_path = target_path.relative_to(ROOT) if target_path.is_absolute() else target_path
    
    print(f"{emoji} {status:<20} {tier:<6} {str(rel_path):<60} {bytes_str} {elapsed_str} {url[:80]}")


def add_manual_download(tier: str, target: str, url: str, reason: str):
    """Add to manual downloads list"""
    manual_downloads.append({
        "tier": tier,
        "target": target,
        "url": url,
        "reason": reason,
        "timestamp": datetime.now().isoformat()
    })
    stats[tier]["manual"] += 1


def add_error_log(tier: str, target: str, url: str, error: str):
    """Add to errors log"""
    errors_log.append({
        "tier": tier,
        "target": target,
        "url": url,
        "error": error,
        "timestamp": datetime.now().isoformat()
    })


# ============================================================================
# TIER 1: High-confidence sources
# ============================================================================

def tier1_carc_rarc():
    """Scrape CARC and RARC codes from X12.org"""
    logger.info("=" * 80)
    logger.info("TIER 1: CARC and RARC codes")
    logger.info("=" * 80)
    
    output_dir = DATA_RAW / "adjudication_logic" / "carc_rarc"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    sources = [
        {
            "name": "CARC",
            "url": "https://x12.org/codes/claim-adjustment-reason-codes",
            "output": output_dir / "carc_codes.csv"
        },
        {
            "name": "RARC",
            "url": "https://x12.org/codes/remittance-advice-remark-codes",
            "output": output_dir / "rarc_codes.csv"
        }
    ]
    
    for source in sources:
        if source["output"].exists() and source["output"].stat().st_size > 10000:
            # Skip if file exists and is reasonably large (> 10KB)
            log_status("SKIP_EXISTS", "Tier1", source["output"], 0, 0, source["url"])
            stats["tier1"]["skip"] += 1
            continue
        
        start_time = time.time()
        domain = get_domain(source["url"])
        
        if not robots_cache.can_fetch(source["url"]):
            log_status("BLOCKED", "Tier1", source["output"], 0, 0, source["url"])
            stats["tier1"]["blocked"] += 1
            continue
        
        wait_for_rate_limit(domain)
        
        try:
            response = requests.get(source["url"], headers={"User-Agent": USER_AGENT}, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            last_request_time[domain] = time.time()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all tables and use the one with the most codes
            tables = soup.find_all('table')
            best_codes = []
            
            for table in tables:
                table_codes = []
                for tr in table.find_all('tr'):
                    cols = tr.find_all(['td', 'th'])
                    if len(cols) < 2:
                        continue
                    
                    code = cols[0].get_text(strip=True)
                    desc_parts = [col.get_text(strip=True) for col in cols[1:]]
                    description = ' '.join(desc_parts)
                    
                    # Skip header rows
                    if code.lower() in ['code', 'carc', 'rarc', 'reason code', 'remark code', '', 'group code']:
                        continue
                    
                    # For CARC: look for numeric codes (1-308)
                    # For RARC: look for alphanumeric codes (N1, M1, etc.)
                    if source["name"] == "CARC":
                        code_match = re.match(r'^(\d{1,3})$', code)
                    else:
                        code_match = re.match(r'^([A-Z]?\d+[A-Z]?)$', code, re.IGNORECASE)
                    
                    if code_match:
                        code_clean = code_match.group(1)
                        description_clean = ' '.join(description.split())
                        description_clean = description_clean.replace('"', '""')
                        table_codes.append((code_clean, description_clean))
                
                # Use table with most codes
                if len(table_codes) > len(best_codes):
                    best_codes = table_codes
            
            if not best_codes:
                raise ValueError(f"No {source['name']} codes found in any table")
            
            # Write CSV
            csv_content = "code,description\n"
            for code, description in best_codes:
                csv_content += f'"{code}","{description}"\n'
            
            source["output"].write_text(csv_content, encoding='utf-8')
            
            bytes_size = source["output"].stat().st_size
            elapsed_ms = int((time.time() - start_time) * 1000)
            
            logger.info(f"Extracted {len(best_codes)} {source['name']} codes")
            log_status("OK", "Tier1", source["output"], bytes_size, elapsed_ms, source["url"])
            stats["tier1"]["ok"] += 1
            
        except Exception as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            log_status(f"ERROR_{type(e).__name__}", "Tier1", source["output"], 0, elapsed_ms, source["url"])
            stats["tier1"]["error"] += 1
            add_error_log("tier1", str(source["output"]), source["url"], str(e))


def tier1_cms_ncd_lcd():
    """Search CMS NCD/LCD database"""
    logger.info("=" * 80)
    logger.info("TIER 1: CMS NCD/LCD database")
    logger.info("=" * 80)
    
    # Note: The CMS Medicare Coverage Database doesn't have a simple REST API
    # It requires form-based search. This would need manual work or Selenium.
    
    output_dir = DATA_RAW / "adjudication_logic" / "cms_ncd_lcd"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.warning("CMS NCD/LCD database requires interactive search - marking as MANUAL_REQUIRED")
    
    add_manual_download(
        "tier1",
        str(output_dir / "*.pdf"),
        "https://www.cms.gov/medicare-coverage-database/",
        "Requires form-based search for: bariatric surgery, gender-affirming care, growth hormone, ABA therapy, IRF criteria, mental health residential, substance use treatment"
    )
    
    log_status("MANUAL_REQUIRED", "Tier1", output_dir / "README.txt", 0, 0, 
               "https://www.cms.gov/medicare-coverage-database/")


def tier1_pubmed_test():
    """PubMed E-utilities connectivity test"""
    logger.info("=" * 80)
    logger.info("TIER 1: PubMed connectivity test")
    logger.info("=" * 80)
    
    output_dir = DATA_RAW / "pubmed_test"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "connectivity_test.json"
    
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=bariatric+surgery+BMI+30-35+diabetes&retmax=5&retmode=json"
    
    status, bytes_size, elapsed_ms = fetch_url(url, output_file, "tier1", binary=False)
    log_status(status, "Tier1", output_file, bytes_size, elapsed_ms, url)
    
    if status == "OK":
        logger.info("✓ PubMed E-utilities accessible - Medical Necessity agent can function")
    else:
        logger.error("✗ PubMed E-utilities failed - Medical Necessity agent will not work at runtime!")


# ============================================================================
# TIER 2: Static PDFs from cooperative sites
# ============================================================================

def tier2_cigna_policies():
    """Scrape Cigna medical policies"""
    logger.info("=" * 80)
    logger.info("TIER 2: Cigna medical policies")
    logger.info("=" * 80)
    
    output_dir = DATA_RAW / "insurer_policies" / "cigna"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    base_url = "https://www.cigna.com/health-care-providers/coverage-and-claims/policies/medical-policies"
    
    # Note: Cigna's site structure requires navigation through multiple pages
    # This is a simplified implementation - full version would need page-by-page scraping
    
    logger.warning("Cigna policies require multi-page navigation and search - marking for manual review")
    
    add_manual_download(
        "tier2",
        str(output_dir / "*.pdf"),
        base_url,
        "Cigna site requires navigation through alphabetical index. Target procedures: Bariatric surgery, Gender dysphoria, Growth hormone, IVIG, ABA, Sleep studies, MRI PA, Spinal surgery, Cromolyn"
    )
    
    log_status("MANUAL_REQUIRED", "Tier2", output_dir / "README.txt", 0, 0, base_url)


def tier2_bcbs_fep_policies():
    """Scrape BCBS FEP medical policies"""
    logger.info("=" * 80)
    logger.info("TIER 2: BCBS FEP medical policies")
    logger.info("=" * 80)
    
    output_dir = DATA_RAW / "insurer_policies" / "bcbs_fep"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    base_url = "https://www.fepblue.org/benefit-plans/medical-policies"
    
    logger.warning("BCBS FEP policies require navigation - marking for manual review")
    
    add_manual_download(
        "tier2",
        str(output_dir / "*.pdf"),
        base_url,
        "BCBS FEP site requires policy lookup. Same 9 procedures as Cigna"
    )
    
    log_status("MANUAL_REQUIRED", "Tier2", output_dir / "README.txt", 0, 0, base_url)


def tier2_clinical_guidelines():
    """Download clinical guidelines from professional societies"""
    logger.info("=" * 80)
    logger.info("TIER 2: Clinical guidelines")
    logger.info("=" * 80)
    
    guidelines = [
        {
            "org": "asmbs",
            "name": "bariatric_class1_obesity",
            "search": "ASMBS position statement Class I obesity site:asmbs.org filetype:pdf",
            "note": "Search Google for latest version (2022 or 2024)"
        },
        {
            "org": "wpath",
            "name": "soc8_executive_summary",
            "url": "https://www.wpath.org/soc8",
            "note": "May require email submission - check site"
        },
        {
            "org": "asam",
            "name": "criteria_summary",
            "search": "ASAM criteria summary site:asam.org filetype:pdf",
            "note": "Search for public summary document"
        },
        {
            "org": "endocrine_society",
            "name": "growth_hormone_guideline",
            "search": "Endocrine Society growth hormone deficiency clinical practice guideline filetype:pdf",
            "note": "Search for latest CPG"
        }
    ]
    
    for guideline in guidelines:
        org_dir = DATA_RAW / "clinical_guidelines" / guideline["org"]
        org_dir.mkdir(parents=True, exist_ok=True)
        output_file = org_dir / f"{guideline['name']}.pdf"
        
        # These require manual search/download
        url = guideline.get("url", f"https://www.google.com/search?q={guideline.get('search', '')}")
        
        add_manual_download(
            "tier2",
            str(output_file),
            url,
            guideline["note"]
        )
        
        log_status("MANUAL_REQUIRED", "Tier2", output_file, 0, 0, url)


def tier2_state_medicaid_manuals():
    """Download state Medicaid provider manuals"""
    logger.info("=" * 80)
    logger.info("TIER 2: State Medicaid provider manuals")
    logger.info("=" * 80)
    
    states = [
        {
            "name": "masshealth",
            "url": "https://www.mass.gov/lists/masshealth-provider-manuals",
            "keywords": ["prior authorization", "coverage criteria", "behavioral health", "medical necessity"]
        },
        {
            "name": "va_dmas",
            "url": "https://www.dmas.virginia.gov/for-providers/general-information/manuals/",
            "keywords": ["prior authorization", "coverage criteria", "behavioral health", "medical necessity"]
        },
        {
            "name": "in_ihcp",
            "url": "https://www.in.gov/medicaid/providers/provider-references/ihcp-provider-reference-modules/",
            "keywords": ["prior authorization", "coverage criteria", "behavioral health", "medical necessity"]
        }
    ]
    
    for state in states:
        output_dir = DATA_RAW / "adjudication_logic" / state["name"]
        output_dir.mkdir(parents=True, exist_ok=True)
        
        if not robots_cache.can_fetch(state["url"]):
            log_status("BLOCKED", "Tier2", output_dir / "README.txt", 0, 0, state["url"])
            stats["tier2"]["blocked"] += 1
            continue
        
        domain = get_domain(state["url"])
        wait_for_rate_limit(domain)
        
        try:
            response = requests.get(state["url"], headers={"User-Agent": USER_AGENT}, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            last_request_time[domain] = time.time()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all PDF links
            pdf_links = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                if href.endswith('.pdf'):
                    # Check if matches keywords
                    link_text = link.get_text().lower()
                    if any(kw.lower() in link_text for kw in state["keywords"]):
                        full_url = urljoin(state["url"], href)
                        pdf_links.append((full_url, link.get_text(strip=True)))
            
            # Download first 5 matching PDFs
            for i, (pdf_url, pdf_name) in enumerate(pdf_links[:5]):
                filename = f"{i+1:02d}_{pdf_name[:50].replace(' ', '_').replace('/', '_')}.pdf"
                output_file = output_dir / filename
                
                status, bytes_size, elapsed_ms = fetch_url(
                    pdf_url, output_file, "tier2", binary=True, validate_func=validate_pdf
                )
                log_status(status, "Tier2", output_file, bytes_size, elapsed_ms, pdf_url)
                
        except Exception as e:
            logger.error(f"Error processing {state['name']}: {e}")
            add_error_log("tier2", str(output_dir), state["url"], str(e))


# ============================================================================
# TIER 3: Careful rate-limited scraping
# ============================================================================

def tier3_propublica():
    """Scrape ProPublica 'Uncovered' series"""
    logger.info("=" * 80)
    logger.info("TIER 3: ProPublica 'Uncovered' series")
    logger.info("=" * 80)
    
    output_dir = DATA_RAW / "propublica_articles"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    series_url = "https://www.propublica.org/series/uncovered-the-power-of-health-insurance"
    
    if not robots_cache.can_fetch(series_url):
        log_status("BLOCKED", "Tier3", output_dir / "README.txt", 0, 0, series_url)
        stats["tier3"]["blocked"] += 1
        return
    
    domain = get_domain(series_url)
    wait_for_rate_limit(domain)
    
    try:
        # Get series page
        response = requests.get(series_url, headers={"User-Agent": USER_AGENT}, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        last_request_time[domain] = time.time()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find article links
        article_links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if '/article/' in href and href.startswith('/'):
                full_url = f"https://www.propublica.org{href}"
                if full_url not in article_links:
                    article_links.append(full_url)
        
        logger.info(f"Found {len(article_links)} article links, processing first 25")
        
        # Process articles
        for article_url in article_links[:25]:
            slug = article_url.split('/')[-1]
            output_file = output_dir / f"{slug}.md"
            
            if output_file.exists() and output_file.stat().st_size > 0:
                log_status("SKIP_EXISTS", "Tier3", output_file, 0, 0, article_url)
                stats["tier3"]["skip"] += 1
                continue
            
            wait_for_rate_limit(domain)
            start_time = time.time()
            
            try:
                article_response = requests.get(article_url, headers={"User-Agent": USER_AGENT}, timeout=REQUEST_TIMEOUT)
                article_response.raise_for_status()
                last_request_time[domain] = time.time()
                
                # Use trafilatura for clean extraction
                article_text = trafilatura.extract(article_response.text, include_comments=False)
                
                if not article_text:
                    raise ValueError("No text extracted")
                
                # Parse metadata
                article_soup = BeautifulSoup(article_response.text, 'html.parser')
                title = article_soup.find('h1')
                title_text = title.get_text(strip=True) if title else slug
                
                date_elem = article_soup.find('time')
                date_text = date_elem.get('datetime', '') if date_elem else ''
                
                # Create markdown with frontmatter
                markdown = f"""---
title: {title_text}
url: {article_url}
date: {date_text}
denial_themes: []
---

{article_text}
"""
                output_file.write_text(markdown, encoding='utf-8')
                
                bytes_size = output_file.stat().st_size
                elapsed_ms = int((time.time() - start_time) * 1000)
                
                log_status("OK", "Tier3", output_file, bytes_size, elapsed_ms, article_url)
                stats["tier3"]["ok"] += 1
                
            except Exception as e:
                elapsed_ms = int((time.time() - start_time) * 1000)
                log_status(f"ERROR_{type(e).__name__}", "Tier3", output_file, 0, elapsed_ms, article_url)
                stats["tier3"]["error"] += 1
                add_error_log("tier3", str(output_file), article_url, str(e))
                
    except Exception as e:
        logger.error(f"Error fetching ProPublica series page: {e}")
        add_error_log("tier3", str(output_dir), series_url, str(e))


def tier3_kff():
    """Scrape KFF Bill of the Month series"""
    logger.info("=" * 80)
    logger.info("TIER 3: KFF Bill of the Month series")
    logger.info("=" * 80)
    
    output_dir = DATA_RAW / "kff_bill_of_month"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    series_url = "https://kffhealthnews.org/news/series/bill-of-the-month/"
    
    if not robots_cache.can_fetch(series_url):
        log_status("BLOCKED", "Tier3", output_dir / "README.txt", 0, 0, series_url)
        stats["tier3"]["blocked"] += 1
        return
    
    domain = get_domain(series_url)
    wait_for_rate_limit(domain)
    
    try:
        response = requests.get(series_url, headers={"User-Agent": USER_AGENT}, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        last_request_time[domain] = time.time()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find article links
        article_links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if 'kffhealthnews.org' in href and '/news/' in href:
                if href not in article_links:
                    article_links.append(href)
        
        logger.info(f"Found {len(article_links)} article links, processing first 30")
        
        # Common insurer names for regex
        insurer_pattern = re.compile(
            r'\b(UnitedHealthcare|United Healthcare|Aetna|Cigna|Anthem|Blue Cross|BCBS|Humana|Kaiser|Oscar)\b',
            re.IGNORECASE
        )
        amount_pattern = re.compile(r'\$[\d,]+')
        
        for article_url in article_links[:30]:
            slug = article_url.rstrip('/').split('/')[-1]
            output_file = output_dir / f"{slug}.md"
            
            if output_file.exists() and output_file.stat().st_size > 0:
                log_status("SKIP_EXISTS", "Tier3", output_file, 0, 0, article_url)
                stats["tier3"]["skip"] += 1
                continue
            
            wait_for_rate_limit(domain)
            start_time = time.time()
            
            try:
                article_response = requests.get(article_url, headers={"User-Agent": USER_AGENT}, timeout=REQUEST_TIMEOUT)
                article_response.raise_for_status()
                last_request_time[domain] = time.time()
                
                # Extract text
                article_text = trafilatura.extract(article_response.text, include_comments=False)
                
                if not article_text:
                    raise ValueError("No text extracted")
                
                # Parse metadata
                article_soup = BeautifulSoup(article_response.text, 'html.parser')
                title = article_soup.find('h1')
                title_text = title.get_text(strip=True) if title else slug
                
                date_elem = article_soup.find('time')
                date_text = date_elem.get('datetime', '') if date_elem else ''
                
                # Extract structured data
                insurer_match = insurer_pattern.search(article_text)
                insurer = insurer_match.group(0) if insurer_match else ""
                
                amounts = amount_pattern.findall(article_text)
                billed = amounts[0] if len(amounts) > 0 else ""
                final_paid = amounts[1] if len(amounts) > 1 else ""
                
                # Create markdown
                markdown = f"""---
title: {title_text}
url: {article_url}
date: {date_text}
insurer: {insurer}
procedure: ""
billed: {billed}
final_paid: {final_paid}
denial_reason: ""
outcome: ""
---

{article_text}
"""
                output_file.write_text(markdown, encoding='utf-8')
                
                bytes_size = output_file.stat().st_size
                elapsed_ms = int((time.time() - start_time) * 1000)
                
                log_status("OK", "Tier3", output_file, bytes_size, elapsed_ms, article_url)
                stats["tier3"]["ok"] += 1
                
            except Exception as e:
                elapsed_ms = int((time.time() - start_time) * 1000)
                log_status(f"ERROR_{type(e).__name__}", "Tier3", output_file, 0, elapsed_ms, article_url)
                stats["tier3"]["error"] += 1
                add_error_log("tier3", str(output_file), article_url, str(e))
                
    except Exception as e:
        logger.error(f"Error fetching KFF series page: {e}")
        add_error_log("tier3", str(output_dir), series_url, str(e))


def tier3_state_appeal_letters():
    """Download state appeal letter samples"""
    logger.info("=" * 80)
    logger.info("TIER 3: State appeal letters")
    logger.info("=" * 80)
    
    states = [
        {
            "name": "washington",
            "url": "https://www.insurance.wa.gov/insurance-resources/health-insurance/appealing-health-insurance-denial/common-reasons-denial-and-examples-appeal-letters"
        },
        {
            "name": "north_carolina",
            "url": "https://www.ncdoi.gov/consumers/health-insurance/health-claim-denied/medical-appeals/medical-appeals-tool-kit"
        }
    ]
    
    for state in states:
        output_dir = DATA_RAW / "state_appeal_resources" / state["name"]
        output_dir.mkdir(parents=True, exist_ok=True)
        
        if not robots_cache.can_fetch(state["url"]):
            log_status("BLOCKED", "Tier3", output_dir / "README.txt", 0, 0, state["url"])
            stats["tier3"]["blocked"] += 1
            continue
        
        domain = get_domain(state["url"])
        wait_for_rate_limit(domain)
        
        try:
            response = requests.get(state["url"], headers={"User-Agent": USER_AGENT}, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            last_request_time[domain] = time.time()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all DOC/DOCX/PDF links
            for link in soup.find_all('a', href=True):
                href = link['href']
                if any(ext in href.lower() for ext in ['.doc', '.docx', '.pdf']):
                    # Make absolute URL
                    if not href.startswith('http'):
                        href = urljoin(state["url"], href)
                    
                    filename = href.split('/')[-1].split('?')[0]
                    output_file = output_dir / filename
                    
                    # Check if we already have this file
                    if output_file.exists() and output_file.stat().st_size > 0:
                        log_status("SKIP_EXISTS", "Tier3", output_file, 0, 0, href)
                        stats["tier3"]["skip"] += 1
                        continue
                    
                    # Download
                    validate_func = validate_pdf if filename.endswith('.pdf') else None
                    status, bytes_size, elapsed_ms = fetch_url(
                        href, output_file, "tier3", binary=True, validate_func=validate_func
                    )
                    log_status(status, "Tier3", output_file, bytes_size, elapsed_ms, href)
                    
        except Exception as e:
            logger.error(f"Error processing {state['name']}: {e}")
            add_error_log("tier3", str(output_dir), state["url"], str(e))


# ============================================================================
# SUMMARY AND REPORTING
# ============================================================================

def print_summary():
    """Print and save collection summary"""
    print("\n")
    print("=" * 80)
    print(" COLLECTION SUMMARY ".center(80, "="))
    print("=" * 80)
    
    # Stats by tier
    for tier_name, tier_stats in [("Tier 1 (high-confidence)", "tier1"),
                                     ("Tier 2 (static PDFs)", "tier2"),
                                     ("Tier 3 (rate-limited)", "tier3")]:
        s = stats[tier_stats]
        print(f"{tier_name:30}  OK={s['ok']:<3}  SKIP={s['skip']:<3}  ERROR={s['error']:<3}  MANUAL={s['manual']:<3}  BLOCKED={s['blocked']:<3}")
    
    print("-" * 80)
    
    # Total files and size
    total_files = 0
    total_bytes = 0
    for path in DATA_RAW.rglob("*"):
        if path.is_file() and path.name != ".gitkeep":
            total_files += 1
            total_bytes += path.stat().st_size
    
    total_mb = total_bytes / (1024 * 1024)
    print(f"Total files now in data/raw:  {total_files} files, {total_mb:.1f} MB")
    
    manual_count = len(manual_downloads)
    errors_count = len(errors_log)
    print(f"Manual downloads required:    {manual_count} items → see logs/manual_downloads_needed.md")
    print(f"Errors needing investigation: {errors_count} items → see logs/errors.log")
    
    # PHI check
    phi_log = LOGS_DIR / "phi_quarantine.log"
    if phi_log.exists():
        phi_count = len(phi_log.read_text().strip().split('\n'))
        print(f"⚠️  PHI DETECTED: {phi_count} files quarantined → see logs/phi_quarantine.log")
    
    print("=" * 80)
    
    # Write manual downloads list
    if manual_downloads:
        manual_md = LOGS_DIR / "manual_downloads_needed.md"
        with manual_md.open("w", encoding='utf-8') as f:
            f.write("# Manual Downloads Needed\n\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n\n")
            for item in manual_downloads:
                f.write(f"## {item['tier'].upper()}: {item['target']}\n\n")
                f.write(f"**URL**: {item['url']}\n\n")
                f.write(f"**Reason**: {item['reason']}\n\n")
                f.write(f"**Timestamp**: {item['timestamp']}\n\n")
                f.write("---\n\n")
    
    # Write errors log
    if errors_log:
        errors_file = LOGS_DIR / "errors.log"
        with errors_file.open("w", encoding='utf-8') as f:
            for item in errors_log:
                f.write(f"{item['timestamp']} [{item['tier']}] {item['target']}\n")
                f.write(f"  URL: {item['url']}\n")
                f.write(f"  Error: {item['error']}\n\n")
    
    # Write summary markdown
    summary_md = LOGS_DIR / "collection_summary.md"
    with summary_md.open("w", encoding='utf-8') as f:
        f.write("# Data Collection Summary\n\n")
        f.write(f"**Generated**: {datetime.now().isoformat()}\n\n")
        f.write("## Statistics by Tier\n\n")
        f.write("| Tier | OK | Skip | Error | Manual | Blocked |\n")
        f.write("|------|-------|------|-------|--------|----------|\n")
        for tier_name, tier_key in [("Tier 1", "tier1"), ("Tier 2", "tier2"), ("Tier 3", "tier3")]:
            s = stats[tier_key]
            f.write(f"| {tier_name} | {s['ok']} | {s['skip']} | {s['error']} | {s['manual']} | {s['blocked']} |\n")
        f.write("\n")
        f.write(f"**Total Files**: {total_files} files ({total_mb:.1f} MB)\n\n")
        f.write(f"**Manual Downloads**: {manual_count}\n\n")
        f.write(f"**Errors**: {errors_count}\n\n")


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Denial Defense - Automatable Data Collection"
    )
    parser.add_argument(
        "--tier",
        choices=["1", "2", "3", "all"],
        default="all",
        help="Which tier to run (default: all)"
    )
    parser.add_argument(
        "--only",
        help="Run only one function by name (e.g., tier1_carc_rarc)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Plan only, no downloads"
    )
    
    args = parser.parse_args()
    
    if args.dry_run:
        logger.info("DRY RUN MODE - No downloads will be performed")
        return
    
    logger.info(f"Starting data collection - Tier: {args.tier}")
    logger.info(f"Project root: {ROOT}")
    
    start_time = time.time()
    
    # Dispatch
    if args.only:
        func = globals().get(args.only)
        if func and callable(func):
            func()
        else:
            logger.error(f"Function '{args.only}' not found")
            return 1
    else:
        if args.tier in ["1", "all"]:
            tier1_carc_rarc()
            tier1_cms_ncd_lcd()
            tier1_pubmed_test()
        
        if args.tier in ["2", "all"]:
            tier2_cigna_policies()
            tier2_bcbs_fep_policies()
            tier2_clinical_guidelines()
            tier2_state_medicaid_manuals()
        
        if args.tier in ["3", "all"]:
            tier3_propublica()
            tier3_kff()
            tier3_state_appeal_letters()
    
    elapsed = time.time() - start_time
    logger.info(f"\nCollection completed in {elapsed:.1f}s")
    
    # Print summary
    print_summary()
    
    return 0


if __name__ == "__main__":
    exit(main())
