# Automatable Data Collection Script

This script handles **automatable sources only** - sources that don't require interactive browser sessions, login walls, or manual intervention.

## Quick Start

```bash
# Install dependencies
python -m pip install -r requirements.txt

# Test Tier 1 (fastest, highest confidence)
python scripts/collect_automatable.py --tier 1

# Run everything
python scripts/collect_automatable.py --tier all

# Run specific function
python scripts/collect_automatable.py --only tier3_propublica

# Dry run (plan without downloading)
python scripts/collect_automatable.py --dry-run
```

## Tier Structure

### Tier 1: High-Confidence Sources
✅ **CARC/RARC codes** - X12.org HTML tables → CSV  
⚠️ **CMS NCD/LCD** - Requires form-based search (manual)  
✅ **PubMed connectivity test** - E-utilities API check  

**Expected**: 2-3 files, <1 minute, 0 errors

### Tier 2: Static PDFs from Cooperative Sites
⚠️ **Cigna policies** - Requires navigation (manual)  
⚠️ **BCBS FEP policies** - Requires navigation (manual)  
⚠️ **Clinical guidelines** - May require Google search (manual)  
✅ **State Medicaid manuals** - First 5 matching PDFs per state  

**Expected**: 10-20 files, 2-5 minutes

### Tier 3: Careful Rate-Limited Scraping
✅ **ProPublica** - "Uncovered" series, 25 articles max  
✅ **KFF** - "Bill of the Month", 30 stories max  
✅ **State appeal letters** - Washington & North Carolina  

**Expected**: 40-60 files, 5-15 minutes

## Status Codes

Every fetch produces one of these status codes:

- ✅ `OK` - Successfully downloaded and validated
- ⏭️ `SKIP_EXISTS` - File already exists (idempotent behavior)
- ❌ `ERROR_<reason>` - Failed (HTTP error, validation, etc.)
- ⚠️ `MANUAL_REQUIRED` - Needs human intervention
- 🚫 `BLOCKED` - Blocked by robots.txt

## Output Files

### Data Files
```
data/raw/
├── adjudication_logic/
│   ├── carc_rarc/          # CARC and RARC codes
│   ├── cms_ncd_lcd/        # CMS coverage determinations
│   ├── masshealth/         # MA Medicaid manuals
│   ├── va_dmas/            # VA Medicaid manuals
│   └── in_ihcp/            # IN Medicaid manuals
├── insurer_policies/
│   ├── cigna/              # Cigna medical policies
│   ├── bcbs_fep/           # BCBS FEP policies
│   └── oscar/              # Oscar policies
├── clinical_guidelines/
│   ├── asmbs/              # Bariatric surgery guidelines
│   ├── wpath/              # Gender-affirming care SOC
│   ├── asam/               # Substance use criteria
│   └── endocrine_society/  # Growth hormone guidelines
├── propublica_articles/     # ProPublica investigative reporting
├── kff_bill_of_month/       # KFF consumer stories
├── state_appeal_resources/  # State appeal letter examples
│   ├── washington/
│   └── north_carolina/
└── pubmed_test/             # PubMed connectivity test
```

### Log Files
```
logs/
├── collection.log                  # Full operation log
├── collection_summary.md           # Summary report with stats
├── manual_downloads_needed.md      # Items requiring human follow-up
├── errors.log                      # Errors needing investigation
└── phi_quarantine.log              # PHI-flagged files (if any)
```

## Politeness Rules

The script follows strict ethical scraping practices:

1. **Rate Limiting**: 1 request per 2 seconds per domain
2. **Robots.txt**: Checked before every fetch
3. **User Agent**: Identifies as research bot with contact email
4. **Retry Logic**: Exponential backoff on 429/5xx errors
5. **Timeout**: 30 seconds per request
6. **Error Pause**: After 5 consecutive errors, pause domain for 5 minutes

## PHI Safety

All downloaded files are automatically scanned for:
- SSN patterns (`\d{3}-\d{2}-\d{4}`)
- MRN patterns (`MRN:\s*\d+`)

Files with PHI are:
- Quarantined to `data/quarantine/`
- Logged to `logs/phi_quarantine.log`
- Reported prominently in summary

## Idempotency

The script is fully idempotent:
- Checks if target file exists before downloading
- Skips files with size > 0
- Re-running shows mostly `⏭️ SKIP_EXISTS`
- Safe to run multiple times

## Validation

- **PDFs**: Verified to have > 0 pages after download
- **Markdown**: Must produce non-empty text from HTML
- **Failed files**: Deleted immediately, not left corrupt

## Manual Downloads

Some sources require manual intervention:
- **CMS NCD/LCD**: Form-based search interface
- **Cigna/BCBS FEP**: Multi-page navigation
- **Clinical guidelines**: May require Google search or email submission

All manual items are logged to `logs/manual_downloads_needed.md` with:
- Target file path
- Source URL
- Reason for manual requirement
- Timestamp

## Example Output

```
✅ OK                   Tier1  data\raw\adjudication_logic\carc_rarc\rarc_codes.csv           207924    739ms https://x12.org/codes/...
⏭️ SKIP_EXISTS          Tier3  data\raw\state_appeal_resources\washington\example.doc        —         — https://www.insurance.wa.gov/...
⚠️ MANUAL_REQUIRED      Tier2  data\raw\insurer_policies\cigna\bariatric.pdf                  —         — https://www.cigna.com/...
❌ ERROR_HTTP_403       Tier2  data\raw\clinical_guidelines\wpath\soc8.pdf                     —         1801ms https://www.wpath.org/...
```

## Summary Report

After completion, the script prints and saves a summary:

```
================================================================================
COLLECTION SUMMARY
================================================================================
Tier 1 (high-confidence)        OK=2    SKIP=1    ERROR=0    MANUAL=1    BLOCKED=0
Tier 2 (static PDFs)            OK=15   SKIP=3    ERROR=2    MANUAL=4    BLOCKED=0
Tier 3 (rate-limited)           OK=47   SKIP=14   ERROR=3    MANUAL=0    BLOCKED=0
--------------------------------------------------------------------------------
Total files now in data/raw:  89 files, 145.3 MB
Manual downloads required:    5 items → see logs/manual_downloads_needed.md
Errors needing investigation: 5 items → see logs/errors.log
================================================================================
```

## Troubleshooting

### Rate Limiting (429 errors)
Increase `RATE_LIMIT_SECONDS` in the script (default: 2.0s)

### Timeout Errors
Increase `REQUEST_TIMEOUT` (default: 30s)

### Domain Paused
Script automatically pauses domains after 5 consecutive errors for 5 minutes

### Robots.txt Blocks
Respect the block - mark as `MANUAL_REQUIRED` instead

### Unicode Errors
The script includes Windows UTF-8 handling. If issues persist:
```powershell
$env:PYTHONIOENCODING="utf-8"
```

## Dependencies

- `requests` - HTTP client
- `beautifulsoup4` + `lxml` - HTML parsing
- `trafilatura` - HTML-to-markdown extraction (ProPublica, KFF)
- `PyPDF2` - PDF validation
- `tenacity` - Retry logic with exponential backoff

## Acceptance Criteria

✅ **Tier 1** completes with 0 errors  
✅ **Tier 2** produces at least 15 valid PDFs  
✅ **Tier 3** produces at least 20 markdown files (ProPublica + KFF)  
✅ Every fetch produces a status code  
✅ Summary report exists at `logs/collection_summary.md`  
✅ Manual downloads logged to `logs/manual_downloads_needed.md`  
✅ Re-running is fully idempotent  
✅ No PHI quarantined (or user notified if any)

## Notes

- **No Playwright/Selenium**: If a source needs JavaScript rendering, it's marked `MANUAL_REQUIRED`
- **ProPublica**: Uses `trafilatura` for clean article extraction
- **KFF**: Extracts structured data (insurer, amounts) via regex
- **State resources**: Downloads all DOC/DOCX/PDF files from pages

## Contact

For issues or questions:
- Email: sabhisheksagar200@gmail.com
- Check logs: `logs/collection.log`
- Review manual tasks: `logs/manual_downloads_needed.md`
