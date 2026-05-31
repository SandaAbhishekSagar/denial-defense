#!/usr/bin/env python3
"""
Fix CARC codes download using Washington Publishing Company mirror.
WPC publishes the official CARC list in clean, parseable HTML.
"""

import io
import re
import sys
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# Fix Windows Unicode
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Paths
ROOT = Path(__file__).parent.parent
OUTPUT_DIR = ROOT / "data" / "raw" / "adjudication_logic" / "carc_rarc"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Try multiple sources for CARC codes
CARC_SOURCES = [
    "https://x12.org/codes/claim-adjustment-reason-codes",
    "https://www.wpc-edi.com/reference/codelists/healthcare/claim-adjustment-reason-codes",
    "https://med.noridianmedicare.com/web/jea/topics/claim-submission/reason-codes/carc",
]
USER_AGENT = "DenialDefense-Research-Bot/0.1 (contact: sabhisheksagar200@gmail.com)"

def download_carc_codes():
    """Download CARC codes - try multiple sources"""
    print(f"Attempting to download CARC codes from multiple sources...")
    
    headers = {"User-Agent": USER_AGENT}
    
    for url in CARC_SOURCES:
        print(f"\nTrying: {url}")
        try:
            response = requests.get(url, headers=headers, timeout=30, allow_redirects=True)
            response.raise_for_status()
            
            if len(response.text) < 1000:
                print(f"  ⚠ Response too small ({len(response.text)} bytes), skipping")
                continue
            
            print(f"  ✓ Downloaded {len(response.text):,} bytes")
            
            # Save raw HTML for reference
            html_path = OUTPUT_DIR / "carc_codes_full.html"
            html_path.write_text(response.text, encoding='utf-8')
            print(f"  ✓ Saved raw HTML to {html_path}")
            
            return response.text, url
            
        except Exception as e:
            print(f"  ✗ Failed: {e}")
            continue
    
    raise ValueError("All CARC sources failed")


def parse_carc_table(html, source_url):
    """Parse HTML table to extract CARC codes"""
    print("\nParsing CARC codes table...")
    print(f"Source: {source_url}")
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Find tables
    tables = soup.find_all('table')
    print(f"Found {len(tables)} tables")
    
    codes = []
    
    # Try each table
    for table_idx, table in enumerate(tables):
        table_codes = []
        
        for row in table.find_all('tr'):
            cols = row.find_all(['td', 'th'])
            
            if len(cols) < 2:
                continue
            
            # First column is code, second (and maybe more) is description
            code_text = cols[0].get_text(strip=True)
            # Get text from all remaining columns and join them
            desc_parts = [col.get_text(strip=True) for col in cols[1:]]
            desc_text = ' '.join(desc_parts)
            
            # Skip header rows
            if code_text.lower() in ['code', 'carc', 'reason code', '', 'group code']:
                continue
            
            # Extract numeric code - CARC codes are 1-3 digits
            code_match = re.match(r'^(\d{1,3})$', code_text.strip())
            if code_match:
                code = code_match.group(1)
                # Clean up description
                description = ' '.join(desc_text.split())
                description = description.replace('"', '""')  # Escape quotes for CSV
                
                table_codes.append((code, description))
        
        print(f"  Table {table_idx + 1}: {len(table_codes)} codes")
        
        # Use the table with the most codes
        if len(table_codes) > len(codes):
            codes = table_codes
    
    if not codes:
        # Fallback: try to find codes in divs or other elements
        print("No codes found in tables, trying alternative parsing...")
        
        # Look for patterns like "Code: 1, Description: ..."
        text = soup.get_text()
        for line in text.split('\n'):
            match = re.search(r'^\s*(\d{1,3})\s+(.{10,})', line)
            if match:
                code = match.group(1)
                description = match.group(2).strip()
                if len(description) > 10:  # Reasonable description length
                    codes.append((code, description[:200]))  # Limit length
    
    print(f"✓ Extracted {len(codes)} total CARC codes")
    return codes


def save_to_csv(codes, output_path):
    """Save CARC codes to CSV"""
    print(f"\nSaving to {output_path}...")
    
    # Write CSV with proper escaping
    csv_lines = ['code,description']
    for code, description in codes:
        csv_lines.append(f'"{code}","{description}"')
    
    csv_content = '\n'.join(csv_lines)
    output_path.write_text(csv_content, encoding='utf-8')
    
    print(f"✓ Saved {len(codes)} codes to CSV")
    return len(codes)


def validate_codes(codes):
    """Validate that we got a reasonable set of CARC codes"""
    print("\nValidating codes...")
    
    # Check for known CARC codes
    code_numbers = [int(c[0]) for c in codes]
    
    # CARC codes should include common ones like:
    # 1 = Deductible
    # 2 = Coinsurance
    # 3 = Copayment
    # 16 = Claim/service lacks information
    # 50 = Non-covered service
    # 96 = Non-covered charge
    # 97 = Payment adjusted - benefit maximum reached
    
    known_codes = [1, 2, 3, 16, 50, 96, 97, 167, 197]
    found_known = [c for c in known_codes if c in code_numbers]
    
    print(f"✓ Code range: {min(code_numbers)} to {max(code_numbers)}")
    print(f"✓ Found {len(found_known)}/{len(known_codes)} known critical codes")
    
    if len(codes) < 100:
        print(f"⚠ WARNING: Only {len(codes)} codes found (expected 200+)")
        return False
    
    if len(found_known) < len(known_codes) * 0.7:
        print(f"⚠ WARNING: Missing many critical codes")
        return False
    
    print("✓ Validation passed")
    return True


def main():
    print("=" * 80)
    print("CARC Codes Download Fix - Using WPC Mirror")
    print("=" * 80)
    print()
    
    start_time = time.time()
    
    try:
        # Download from multiple sources
        html, source_url = download_carc_codes()
        
        # Parse table
        codes = parse_carc_table(html, source_url)
        
        if not codes:
            print("✗ ERROR: No codes extracted!")
            return 1
        
        # Validate
        is_valid = validate_codes(codes)
        
        # Save to CSV
        csv_path = OUTPUT_DIR / "carc_codes.csv"
        save_to_csv(codes, csv_path)
        
        # Print sample codes
        print("\nSample CARC codes:")
        for code, desc in codes[:10]:
            print(f"  {code:>3} - {desc[:70]}...")
        
        elapsed = time.time() - start_time
        print()
        print("=" * 80)
        print(f"✓ CARC codes download complete in {elapsed:.1f}s")
        print(f"✓ Total codes: {len(codes)}")
        print(f"✓ Output: {csv_path}")
        print("=" * 80)
        
        if not is_valid:
            print("\n⚠ WARNING: Validation concerns detected - review output")
            return 1
        
        return 0
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
