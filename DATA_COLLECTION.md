# Denial Defense - Data Collection Script

A comprehensive Python script for collecting supplemental data for the Denial Defense healthcare AI research project.

## Overview

This script automates the collection of publicly available healthcare insurance data from multiple sources while respecting robots.txt, rate limits, and data privacy requirements.

## Features

- **Idempotent operations**: Safe to run multiple times - won't duplicate work or overwrite existing files
- **Hierarchical directory setup**: Creates complete project structure automatically
- **Rate limiting**: 1 request per 2 seconds per domain
- **Robots.txt compliance**: Respects all robots.txt directives
- **PHI screening**: Validates collected data for potential protected health information
- **Comprehensive logging**: All operations logged to `logs/collection.log`
- **Modular phases**: Run setup, individual scrapers, or all phases

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. (Optional) For JavaScript-heavy sites, install Playwright browsers:
```bash
playwright install
```

## Usage

### Phase 0: Setup Project Hierarchy Only

Creates all necessary directories without running any scrapers:

```bash
python scripts/collect_supplemental_data.py --setup-only
```

This will:
- Create all required directories (won't touch existing ones)
- Place `.gitkeep` files in empty directories
- Generate `data/raw/README.md` with data source documentation
- Generate `.gitignore` if it doesn't exist
- Print validation tree showing existing vs. newly created directories

### Run All Phases

Setup + all scraping + validation:

```bash
python scripts/collect_supplemental_data.py --all
```

### Run Individual Phases

Skip setup and run only one scraper:

```bash
# Insurer medical policies
python scripts/collect_supplemental_data.py --skip-setup --only insurer_policies

# ProPublica articles
python scripts/collect_supplemental_data.py --skip-setup --only propublica

# KFF Bill of the Month
python scripts/collect_supplemental_data.py --skip-setup --only kff

# State appeal resources
python scripts/collect_supplemental_data.py --skip-setup --only state_resources
```

### Using Shell Scripts

#### PowerShell (Windows):

```powershell
.\scripts\collect.ps1
```

#### Bash (Linux/Mac):

```bash
bash scripts/collect.sh
```

These scripts will:
1. Create virtual environment if it doesn't exist
2. Install dependencies
3. Run the full collection pipeline (`--all` flag)

## Data Sources

### 1. Insurer Medical Policies

Publicly published medical policies from major insurers covering 10 key procedures frequently subject to denials:

- Bariatric surgery
- Gender affirming care
- Fertility/IVF
- Mental health residential treatment
- Substance use treatment
- Growth hormone therapy
- Cromolyn sodium
- Prior authorization for imaging
- ABA therapy for autism
- Biologic medications

**Insurers**: Anthem, UnitedHealthcare, Aetna, Cigna, Oscar Health, BCBS Federal Employee Program

**Format**: PDF

**Output**: `data/raw/insurer_policies/{insurer}/{procedure}.pdf`

### 2. ProPublica "Uncovered" Series

Investigative articles on health insurance denials and practices.

**Source**: https://www.propublica.org/series/uncovered-the-power-of-health-insurance

**License**: Creative Commons BY-NC-ND 3.0

**Format**: Markdown with frontmatter (title, URL, date, denial themes)

**Output**: `data/raw/propublica_articles/{slug}.md`

### 3. KFF Health News "Bill of the Month"

Consumer stories about unexpected medical bills and insurance issues.

**Source**: https://kffhealthnews.org/news/series/bill-of-the-month/

**License**: Creative Commons BY-NC-ND 4.0

**Format**: Markdown with structured frontmatter (insurer, procedure, amounts, outcome)

**Output**: `data/raw/kff_bill_of_month/{slug}.md`

### 4. State Insurance Department Appeal Resources

Consumer appeal guides and sample letters from state insurance departments.

**States**: Washington, North Carolina, New York, Texas, Massachusetts

**License**: Public domain (government works)

**Format**: Mixed (PDF, DOC, HTML)

**Output**: `data/raw/state_appeal_resources/{state}/{filename}`

## Output Files

### Manifests

- `data/raw/insurer_policies/manifest.csv`: Tracking for all insurer policy downloads

### Logs

- `logs/collection.log`: Detailed operation log
- `logs/collection_summary.md`: Summary report with file counts and validation

### Documentation

- `data/raw/README.md`: Data source documentation (auto-generated)
- `.gitignore`: Git ignore rules (auto-generated if missing)

## Validation

The script includes a comprehensive validation phase that:

1. **Counts files** by category and compares against expected minimums
2. **Screens for PHI**: Searches text files for SSN and MRN patterns
3. **Checks PDF integrity**: Verifies PDFs are valid (not error pages)
4. **Generates report**: Creates `logs/collection_summary.md`

### Acceptance Criteria

The project aims to collect:
- ✅ At least 30 insurer policy PDFs
- ✅ At least 15 ProPublica articles
- ✅ At least 20 KFF Bill of the Month stories
- ✅ No PHI detected in collected data

## Data Collection Principles

1. **Public sources only**: We only collect publicly published content
2. **Robots.txt compliance**: All scraping respects robots.txt directives
3. **Rate limiting**: 1 request per 2 seconds per domain minimum
4. **Attribution**: All sources documented with URLs and timestamps
5. **License compliance**: We respect Creative Commons and other license terms
6. **Privacy protection**: PHI screening to exclude protected health information
7. **Idempotent operations**: Safe to re-run without duplication

## Limitations

### Manual Steps Required

Some data sources require manual collection due to technical or legal constraints:

1. **Insurer policies**: Many insurer sites use complex JavaScript, require search, or have download protection. The script provides a manifest structure, but policies may need manual download.

2. **Reddit content**: Reddit's Terms of Service prohibit automated scraping. The `data/raw/denial_letters/reddit/` directory is for manually collected content only.

3. **Auth-walled content**: We do not collect from member portals or content requiring authentication.

### CAPTCHA and Rate Limiting

If a source returns CAPTCHA or aggressive rate limiting:
- The script logs the issue and stops
- Manual intervention required
- We do not attempt circumvention

## Troubleshooting

### Unicode Errors on Windows

The script includes automatic UTF-8 handling for Windows. If you still see encoding errors, try:

```powershell
$env:PYTHONIOENCODING="utf-8"
python scripts/collect_supplemental_data.py --all
```

### Playwright Not Installed

If you see Playwright errors:

```bash
pip install playwright
playwright install chromium
```

### Rate Limiting / 429 Errors

The script automatically retries with exponential backoff. If you continue to hit rate limits:
- Increase `RATE_LIMIT_SECONDS` constant in the script
- Run phases separately with delays between them
- Check if you need to reduce concurrent requests

### Robots.txt Blocks

If robots.txt blocks the user agent, the script will log and skip. Do not modify the user agent to circumvent - respect the site's wishes.

## Development

### Adding New Sources

To add a new data source:

1. Add directory to hierarchy in `ensure_project_hierarchy()`
2. Create new scraper function: `scrape_your_source(collector)`
3. Add CLI flag in `main()` argument parser
4. Add phase call in main execution logic
5. Update validation minimums if applicable

### Customizing Rate Limits

Edit constants at the top of `collect_supplemental_data.py`:

```python
RATE_LIMIT_SECONDS = 2.0  # Seconds between requests per domain
MAX_RETRIES = 3           # Number of retry attempts
RETRY_BACKOFF_BASE = 2    # Exponential backoff base
```

## License

The Denial Defense project is open source under the MIT License. 

Individual data sources have their own licenses:
- ProPublica: CC BY-NC-ND 3.0
- KFF Health News: CC BY-NC-ND 4.0
- Government sources: Public domain
- Insurer policies: Publicly published (fair use for research)

All data is used for non-commercial research purposes only.

## Contact

For questions about data collection or to report issues:
- Email: sabhisheksagar200@gmail.com
- Project: Denial Defense (open source healthcare AI research)

## Acknowledgments

- California DMHC for the IMR dataset
- ProPublica for investigative reporting on insurance denials
- KFF Health News for consumer stories
- State insurance departments for consumer resources
